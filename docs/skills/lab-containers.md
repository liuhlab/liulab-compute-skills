# lab-containers: Singularity images on ircbc

The lab's software environments are built with pixi and published as container
images (the `liulab-runtime` registry). On ircbc they are the only way to run
modern software: the cluster's OS is far too old for current tools, and its
compute nodes have no internet. So the images are staged as Singularity files
(SIFs) in a shared lab store, and this skill teaches the agent the routine.

!!! note "ircbc only"
    On arc the same environments run natively under pixi. No containers are
    needed there.

## What the agent does with it

Checks before rebuilding. Every image records the registry version it was built
from. Ask for "the ml image, updated" and the agent compares that record against
the registry first, then tells you whether an update is really needed. It never
rebuilds blindly.

Pulls and builds the offline way. The download runs on the login node, the one
place with network. The build then runs as a Slurm job you approve, and the image
lands in the shared store.

Smoke-tests the result. After a build the agent repeats the import and version
checks the image was built with, in a small test job, and tells you if anything
looks off.

Runs your work inside the image. Batch commands, an interactive shell with the
environment already active, or Jupyter Lab in the container. For Jupyter it hands
the session to [lab-jupyter](lab-jupyter.md), which sets up the tunnel.

## Why a login node shows up here

Reading an image from a compute node is fine, because the shared store is mounted
there too. Downloading a new one is not, since ircbc compute nodes have no
internet at all. That is one of the two cases where [lab-hpc](lab-hpc.md) lets the
agent step onto a login node. It downloads, then goes straight back to the job.

## Shared-store etiquette

These images belong to the whole group. The agent asks first before it overwrites
or deletes anything another lab member may be using, and it keeps the store
writable for everyone.

## When it triggers

"Pull/build/update the … image on ircbc", "is the ml container up to date?", "run
this inside the container", "shell into the align-rna environment".
