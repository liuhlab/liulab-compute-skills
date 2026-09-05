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

Repeatable procedure for `liulab-runtime` environments on ircbc as Singularity images. Follow
`lab-hpc` first (step-0 preflight, `personal.md`, the VPN caveat, confirm every sbatch and srun
with the user), and its `references/ircbc-hpc.md` for the facts underneath — network topology,
`$LIU_LAB_PACKAGES` layout, proxy gotchas.

**Scope: ircbc only.** Its compute nodes have no internet and all real work there runs inside
SIFs. Do not apply these recipes to arc — arc runs the same `liulab-runtime` environments
natively via pixi (see `lab-hpc`); reach for a SIF there only if the user explicitly asks.

## Where each step runs

Work belongs on a compute node. This skill holds the one honest exception: `crane` talks to
ghcr.io, and ircbc compute nodes have no internet, so the pull and the remote digest check can
only happen on the login node — by necessity, not convenience. The build, the smoke test, and
every actual use of an image are compute-node work.

The whole Slurm client (`squeue`, `sbatch`, `scancel`, `srun`) runs on ircbc compute nodes, so
if you already hold a node, submit from there rather than hopping back. `$LIU_LAB_PACKAGES`
lives on `/share` and is readable from both, so only the network fetch is login-bound.

## Version check first — never rebuild blindly

Each SIF carries a sidecar recording the digest it was built from: `liulab-runtime_<env>.sif.digest`.
List the store instead of assuming what exists, then compare local against remote:

```bash
ssh ircbc 'ls -lh $LIU_LAB_PACKAGES/liulab-runtime_*.sif* 2>/dev/null; \
  echo "local:  $(cat $LIU_LAB_PACKAGES/liulab-runtime_<env>.sif.digest 2>/dev/null || echo none)"; \
  echo "remote: $($LIU_LAB_PACKAGES/bin/crane digest ghcr.io/liuhlab/liulab-runtime:<env>)"'
```

- **Digests match** → up to date. Do not rebuild; go use it.
- **Digests differ** → show the user the SIF's build date and both digests, and **ask** whether
  to keep the local image or update.
- **No SIF for that env** → update, pinning the remote digest just printed.

Env names such as `ml`, `align-rna` and `align-dna` are examples, not a catalogue — the `ls -lh`
above is the authority on what is actually built and how much space each image takes. These are
shared lab images: never delete or overwrite someone else's without asking, keep the store
group-writable (dirs carry setgid), and mind the shared disk before building another SIF.

## Where the rest lives

- `references/update-image.md` — pull the tarball, build the SIF, smoke-test it, write the sidecar.
- `references/using-images.md` — run a command, open an interactive pixi-env shell, start Jupyter.
