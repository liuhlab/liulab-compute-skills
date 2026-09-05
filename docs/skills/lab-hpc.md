# lab-hpc: clusters, Slurm, and safety

The foundation skill. It loads before any ssh or Slurm work and hands the agent
the lab's cluster map, the workflow, and the hard safety rules. The other cluster
skills build on it.

## The two clusters

| | arc (chimera) | ircbc |
| --- | --- | --- |
| Hardware | GPU cluster, H100 nodes | CPU cluster |
| Software | Recent OS; pixi runs natively | CentOS 7, so modern tools need Singularity containers |
| Access | ssh alias `arc` or `chimera-login` | ssh alias `ircbc`, behind a VPN you start by hand |
| Lab perks | Free `zhoulab_gpu_priority` partition, plus free preemptible tiers | Shared store of prebuilt container images |

Which cluster fits a task is your call. The agent asks, or reads the answer from
your request. It never picks one in silence.

## What the skill enforces

Preflight first. The agent checks that your `~/.ssh/config` defines the lab
aliases. If it does not, it refuses the request and points you at the setup steps.
It never asks you for a raw address or a password.

Work belongs on a compute node. A login node is a doorway, not a workspace: one
shared machine per cluster, and a crowd of agents each firing off "small" commands
is what brings it down. So `ssh arc '<command>'` is the wrong move even for a
one-liner, and it is rarely needed, because `squeue`, `sbatch` and `scancel` all
run from the compute node anyway.

Two reasons to touch a login node, and no others. Either you hold no job yet, and
only a login node can submit the first one. Or the compute node truly lacks
something: on ircbc that means internet access and `git`, and on arc it means
nothing at all. The arc compute nodes have their own internet and a full
toolchain, so once you land on one, stay.

Reuse the idle job. The lab parks a long-lived idle GPU job on arc, so a node is
usually waiting for you. The agent finds it with `squeue` and works there. If no
job is running anywhere, it offers to start one first.

Show before submit. You see the exact `sbatch` or `srun` before it runs.

Stop at a down VPN. If ircbc does not answer, the agent asks you to check the VPN
rather than retrying in a loop.

## The workflow it follows

Code is written on your own machine and travels through GitHub: edit, `git push`,
then `git pull` on the cluster, then run on a compute node. The agent knows the
usual code directory on each cluster, and reads your own settings from
`~/.claude/compute/personal.md`.

## When it triggers

Any mention of the clusters or of remote compute: ssh to a lab server, Slurm
commands (`sbatch`, `srun`, `squeue`), GPU or compute nodes, moving files to a
cluster, testing code remotely.
