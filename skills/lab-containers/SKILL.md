---
name: lab-containers
description: >-
  Pull, build, update, or smoke-test the lab's Singularity container images
  (SIF) from the ghcr.io liulab-runtime registry — mainly for the ircbc
  cluster, whose compute nodes have no internet: crane pull on the login
  node, sbatch build from docker-archive, per-env test. Covers the
  $LIU_LAB_PACKAGES shared image store.
---

# Lab container images: pull → build → test

Repeatable procedure for getting `liulab-runtime` environments onto ircbc as
Singularity images. Follow the `lab-hpc` skill's rules first (step-0
preflight, `personal.md`, the ircbc VPN caveat, no compute on login nodes)
and its `references/ircbc-hpc.md` for the underlying facts (network
topology, `$LIU_LAB_PACKAGES` layout, proxy gotchas).

**Scope:** ircbc is the target — its compute nodes have no internet and all
real work runs inside SIFs. arc normally needs no SIFs (environments run
natively via pixi there).

## 1. Inventory first — reuse before rebuilding

```bash
ssh ircbc 'ls -lh $LIU_LAB_PACKAGES/*.sif $LIU_LAB_PACKAGES/oci/'
```

Naming convention: `liulab-runtime_<env>.sif`; pull tarballs land in
`oci/liulab-runtime_<env>.docker.tar` but are transient (deleted after the
build), so `oci/` being empty is normal. Envs: `default`, `ml`, `align-rna`,
`align-dna`, … — see the liulab-runtime README. If the image exists, **ask
the user** whether to reuse it or update/rebuild. Images are shared lab
assets — never delete or overwrite someone else's image without asking.

## 2. Pull the tarball (login node — network via proxy, no compute)

```bash
ssh ircbc 'cd $LIU_LAB_PACKAGES/oci && \
  $LIU_LAB_PACKAGES/bin/crane pull ghcr.io/liuhlab/liulab-runtime:<env> liulab-runtime_<env>.docker.tar'
```

If `bin/crane` is missing, re-fetch the static binary (the login-node proxy
handles the download):

```bash
ssh ircbc 'cd $LIU_LAB_PACKAGES/bin && \
  curl -fsSL -o gcr.tgz https://github.com/google/go-containerregistry/releases/latest/download/go-containerregistry_Linux_x86_64.tar.gz && \
  tar xzf gcr.tgz crane && rm gcr.tgz && ./crane version'
```

The tarball is **transient**: it gets deleted right after a successful SIF
build (step 3). If you ever need to rebuild, just `crane pull` again.

## 3. Build the SIF (compute job — no network needed)

**Show the user this exact command and get their confirmation BEFORE
submitting** (repo-wide rule for sbatch submissions):

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

The trailing `rm` deletes the tarball only if the build succeeded. `--wait`
returns when the job finishes (a few minutes); then check the log and
`ls -lh $LIU_LAB_PACKAGES/liulab-runtime_<env>.sif`.

## 4. Smoke-test in a compute job

Each env has a canonical check (the same ones the image build itself runs):

| env | check |
|---|---|
| `ml` / `ml-gpu` | `python -c "import torch, scvi, scanpy, anndata"` |
| `default` | `python -c "import pandas, numpy, seaborn, jupyterlab"` |
| `align-rna` | `STAR --version` |
| `align-dna` | `chromap --version` |

```bash
ssh ircbc 'srun -p compute_cpu -t 10 -J sif_test bash -c "\
  module load singularity && \
  singularity exec $LIU_LAB_PACKAGES/liulab-runtime_<env>.sif bash -c \
    \"source /app/.pixi/activate-<env>.sh 2>/dev/null || export PATH=/app/.pixi/envs/<env>/bin:\\\$PATH; <check>\""'
```

For a fuller Jupyter-in-SIF check (server starts and answers `/api`), run
`$LIU_LAB_PACKAGES/bin/test-jupyter-ml.sh` via `srun` (ml image; adapt for
others). Remember the proxy gotcha from `references/ircbc-hpc.md`: on-node
`curl` probes need `--noproxy '*'`.
