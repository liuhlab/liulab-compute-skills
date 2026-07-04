---
name: lab-containers
description: >-
  Pull, build, update, version-check, or use the lab's Singularity container
  images (SIF) from the ghcr.io liulab-runtime registry on ircbc, whose
  compute nodes have no internet: crane pull on the login node, sbatch build
  from docker-archive, digest-based version checks, and running commands,
  interactive pixi-env shells, or Jupyter inside the containers.
  $LIU_LAB_PACKAGES shared store.
---

# Lab container images: check → pull → build → test → use

Repeatable procedure for `liulab-runtime` environments on ircbc as
Singularity images. Follow the `lab-hpc` skill's rules first (step-0
preflight, `personal.md`, the ircbc VPN caveat, no compute on login nodes,
confirm sbatch/srun with the user before submitting) and its
`references/ircbc-hpc.md` for the underlying facts (network topology,
`$LIU_LAB_PACKAGES` layout, proxy gotchas).

**Scope:** ircbc is the target — its compute nodes have no internet and all
real work runs inside SIFs. arc normally needs no SIFs (environments run
natively via pixi there).

## 1. Version check first — never rebuild blindly

Each SIF has a sidecar file recording the image digest it was built from:
`liulab-runtime_<env>.sif.digest`. Compare local vs remote (login node):

```bash
ssh ircbc 'ls -lh $LIU_LAB_PACKAGES/liulab-runtime_<env>.sif* 2>/dev/null; \
  echo "local:  $(cat $LIU_LAB_PACKAGES/liulab-runtime_<env>.sif.digest 2>/dev/null || echo none)"; \
  echo "remote: $($LIU_LAB_PACKAGES/bin/crane digest ghcr.io/liuhlab/liulab-runtime:<env>)"'
```

- **SIF exists, digests match** → up to date; **do not rebuild**. Use it (§5).
- **SIF exists, digests differ** → tell the user (show the SIF's build date
  and both digests) and **ask** whether to keep the local image or update.
- **No SIF** → proceed to §2 (still confirm the build job before submitting).

Envs: `default`, `ml`, `align-rna`, `align-dna`, … (liulab-runtime README).
Images are shared lab assets — never delete or overwrite someone else's
image without asking. Keep the store group-writable (dirs carry setgid).

## 2. Pull the tarball (login node — network via proxy, no compute)

Pin the digest you checked, so the sidecar exactly matches what gets built:

```bash
ssh ircbc 'cd $LIU_LAB_PACKAGES/oci && \
  $LIU_LAB_PACKAGES/bin/crane pull ghcr.io/liuhlab/liulab-runtime@<digest> liulab-runtime_<env>.docker.tar'
```

The tarball is transient — deleted by the build step. If `bin/crane` is
missing, re-fetch the static binary (the login-node proxy handles it):

```bash
ssh ircbc 'cd $LIU_LAB_PACKAGES/bin && \
  curl -fsSL -o gcr.tgz https://github.com/google/go-containerregistry/releases/latest/download/go-containerregistry_Linux_x86_64.tar.gz && \
  tar xzf gcr.tgz crane && rm gcr.tgz && ./crane version'
```

## 3. Build the SIF (compute job — no network needed)

**Show the user this exact command and get their confirmation BEFORE
submitting** (repo-wide rule):

```bash
ssh ircbc 'sbatch --wait -p compute_cpu -t 02:00:00 -c 8 -J sif_<env> \
  -o $LIU_LAB_PACKAGES/logs/sif_<env>.%j.log --wrap "\
  unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy; \
  export SINGULARITY_TMPDIR=$LIU_LAB_PACKAGES/.tmp SINGULARITY_CACHEDIR=$LIU_LAB_PACKAGES/.tmp; \
  mkdir -p $LIU_LAB_PACKAGES/.tmp; \
  module load singularity && singularity build --force \
    $LIU_LAB_PACKAGES/liulab-runtime_<env>.sif \
    docker-archive://$LIU_LAB_PACKAGES/oci/liulab-runtime_<env>.docker.tar && \
  rm -f $LIU_LAB_PACKAGES/oci/liulab-runtime_<env>.docker.tar"'
```

The trailing `rm` deletes the tarball only if the build succeeded. After the
job succeeds, record the digest sidecar (this is what §1 compares):

```bash
ssh ircbc 'echo <digest> > $LIU_LAB_PACKAGES/liulab-runtime_<env>.sif.digest'
```

## 4. Smoke-test in a compute job

Canonical per-env checks (the same ones the image build itself runs):
`ml`/`ml-gpu` → `python -c "import torch, scvi, scanpy, anndata"`;
`default` → `python -c "import pandas, numpy, seaborn, jupyterlab"`;
`align-rna` → `STAR --version`; `align-dna` → `chromap --version`.

```bash
ssh ircbc 'srun -p compute_cpu -t 10 -J sif_test bash -c "\
  module load singularity && \
  singularity exec $LIU_LAB_PACKAGES/liulab-runtime_<env>.sif bash -c \
    \"source /app/.pixi/activate-<env>.sh && <check>\""'
```

For a fuller Jupyter check, `$LIU_LAB_PACKAGES/bin/test-jupyter-ml.sh` via
`srun` (ml image; adapt for others).

## 5. Using the images (verified patterns — Singularity 3.2.1)

Activation is always `source /app/.pixi/activate-<env>.sh` (fallback:
`export PATH=/app/.pixi/envs/<env>/bin:$PATH`). Do **not** use
`singularity run` — the image's Docker entrypoint does not work under this
old Singularity. `$HOME` is auto-bound; add `--bind /share/lhqlab` (or other
data dirs) as needed.

**Run a command** (batch, in a compute job):

```bash
ssh ircbc 'srun -p compute_cpu -t <time> -c <cpus> bash -c "\
  module load singularity && \
  singularity exec --bind /share/lhqlab $LIU_LAB_PACKAGES/liulab-runtime_<env>.sif \
    bash -c \"source /app/.pixi/activate-<env>.sh && <command...>\""'
```

**Interactive shell in the pixi env, straight from the local PC**
(`--rcfile` gives an activated interactive shell and skips the host bashrc):

```bash
ssh -t ircbc 'srun -p compute_cpu -t 08:00:00 -c <cpus> --pty bash -c "\
  module load singularity && \
  singularity exec --bind /share/lhqlab $LIU_LAB_PACKAGES/liulab-runtime_<env>.sif \
    bash --rcfile /app/.pixi/activate-<env>.sh"'
```

**Jupyter Lab in the container** — submit (with user confirmation), then
tunnel from the local PC through the compute-node alias:

```bash
ssh ircbc 'sbatch -p compute_cpu -t <time> -c <cpus> -J jupyter \
  -o $LIU_LAB_PACKAGES/logs/jupyter.%j.log --wrap "\
  unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy; \
  module load singularity && \
  singularity exec --bind /share/lhqlab $LIU_LAB_PACKAGES/liulab-runtime_<env>.sif \
    bash -c \"source /app/.pixi/activate-<env>.sh && jupyter lab --no-browser --port=<port> --ip=127.0.0.1\""'
# find the node with: ssh ircbc 'squeue -u $USER'   (Slurm 18.08: no --me)
ssh -f -N -L <port>:localhost:<port> <cpuNN>      # local PC; cpuNN alias ProxyJumps via ircbc
```

Token: `grep -m1 "?token=" $LIU_LAB_PACKAGES/logs/jupyter.<jobid>.log`. See
the `lab-jupyter` skill for the full tunnel/reuse/cleanup flow.
