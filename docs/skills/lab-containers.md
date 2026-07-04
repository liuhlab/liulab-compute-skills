# lab-containers — Singularity images on ircbc

The lab's software environments are built with pixi and published as
container images (the `liulab-runtime` registry). On ircbc they are the
only way to run modern software: the cluster's OS is too old for current
tools, and its compute nodes have **no internet**, so images are staged as
Singularity files (SIFs) in a shared lab store. This skill teaches the
agent the whole routine.

!!! note "ircbc only"
    On arc the same environments run natively via pixi — no containers
    needed there.

## What the agent can do with it

- **Check before rebuilding.** Every image records which registry version
  it was built from. Asked to "update the ml image", the agent first
  compares that against the registry and tells you whether an update is
  actually needed — it never rebuilds blindly.
- **Pull + build the offline way.** Downloads happen on the login node (the
  only place with network), the build runs as a Slurm job, and the image
  lands in the shared store — with your approval before the build job is
  submitted.
- **Smoke-test.** After a build it runs the same import/version checks the
  image was built with, in a small test job, and tells you if something is
  off.
- **Run your work inside the image.** Batch commands, an interactive shell
  with the environment already activated, or Jupyter Lab in the container
  (handing the session off to [lab-jupyter](lab-jupyter.md) for the
  tunnel).

## Shared-store etiquette

The images are shared lab assets: the agent asks before overwriting or
deleting anything another lab member might be using, and keeps the store
writable for the whole group.

## When it triggers

"Pull/build/update the … image on ircbc", "is the ml container up to
date?", "run this inside the container", "shell into the align-rna
environment".
