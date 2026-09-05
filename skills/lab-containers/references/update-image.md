# Updating a lab container image

Pull, build and smoke-test a `liulab-runtime` SIF on ircbc. Version-check in `SKILL.md` first; continue only once the user agrees to update.

## 1. Pull the tarball (login node, by necessity)

Pin the digest you just checked so the sidecar matches exactly what gets built. `crane` needs the
registry, and ircbc compute nodes have no internet — so this is the one step that must run there.

```bash
ssh ircbc 'cd $LIU_LAB_PACKAGES/oci && $LIU_LAB_PACKAGES/bin/crane pull ghcr.io/liuhlab/liulab-runtime@<digest> liulab-runtime_<env>.docker.tar'

# only if bin/crane is missing — re-fetch the static binary (the login node's proxy handles it)
ssh ircbc 'cd $LIU_LAB_PACKAGES/bin && curl -fsSL -o gcr.tgz https://github.com/google/go-containerregistry/releases/latest/download/go-containerregistry_Linux_x86_64.tar.gz && tar xzf gcr.tgz crane && rm gcr.tgz && ./crane version'
```

## 2. Build the SIF (compute job)

Everything from here is compute work; if you already hold a node, drop the `ssh ircbc '…'` wrapper and
submit from there. **Show the user this exact command and get confirmation before submitting** (repo-wide
rule) — `sbatch --test-only` is a safe non-submitting dry run to show alongside it.

```bash
ssh ircbc 'sbatch --wait -p compute_cpu -t 02:00:00 -c 8 -J sif_<env> \
  -o $LIU_LAB_PACKAGES/logs/sif_<env>.%j.log --wrap "\
  unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy; \
  export SINGULARITY_TMPDIR=$LIU_LAB_PACKAGES/.tmp SINGULARITY_CACHEDIR=$LIU_LAB_PACKAGES/.tmp; mkdir -p $LIU_LAB_PACKAGES/.tmp; \
  module load singularity && singularity build --force $LIU_LAB_PACKAGES/liulab-runtime_<env>.sif docker-archive://$LIU_LAB_PACKAGES/oci/liulab-runtime_<env>.docker.tar && \
  rm -f $LIU_LAB_PACKAGES/oci/liulab-runtime_<env>.docker.tar"'
```

`--wait` blocks through the queue *and* the build, maybe the full time limit — background it or use a long
timeout. If the connection drops the job survives, so do **not** resubmit: check `squeue -u $USER` and tail
the log. The `unset` earns its keep — six proxy variables leak in from the login shell, pointing at a SOCKS
port only the login node listens on; without it the failure reads as "Connection refused", which looks like
a broken proxy rather than "compute has no internet". The trailing `rm` deletes the transient tarball, and
only on success. Write the sidecar only after the job exits 0 — nonzero means the build failed:
`ssh ircbc 'echo <digest> > $LIU_LAB_PACKAGES/liulab-runtime_<env>.sif.digest'`

## 3. Smoke-test in a compute job

Canonical per-env checks, the ones the image build itself runs — `ml`/`ml-gpu`:
`python -c "import torch, scvi, scanpy, anndata"`; `default`: `python -c "import pandas, numpy, seaborn, jupyterlab"`;
`align-rna`: `STAR --version`; `align-dna`: `chromap --version`. Envs are examples, not a catalogue — for another env,
check its headline tool. Fuller Jupyter check: `$LIU_LAB_PACKAGES/bin/test-jupyter-ml.sh` under `srun` (ml image; adapt for others).

```bash
ssh ircbc 'srun -p compute_cpu -t 10 -J sif_test bash -c "\
  module load singularity && \
  singularity exec $LIU_LAB_PACKAGES/liulab-runtime_<env>.sif bash -c \"source /app/.pixi/activate-<env>.sh && <check>\""'
```

The `<check>` slot (and `<command...>` in `using-images.md`) sits two quoting levels deep — write any inner
double quote as `\\\"`, or keep the payload quote-free. Expanded `ml` inner line:
`\"source /app/.pixi/activate-ml.sh && python -c \\\"import torch, scvi, scanpy, anndata\\\"\"`.

**If the check fails, tell the user before anything else** — the sidecar would make the version check report
this SIF as up to date. Ask whether to delete the SIF and its `.digest` (shared lab images: ask first) or to
investigate; rebuilding from the same pinned digest gives the same image, so the fix is usually upstream.
