# lab-hpc — clusters, Slurm, and safety

The foundation skill. It loads before any ssh or Slurm work and hands the
agent the lab's cluster map, the workflow, and the hard safety rules. The
other two skills build on it.

## The two clusters

| | arc_hpc (chimera / ARC) | ircbc_hpc |
| --- | --- | --- |
| Hardware | GPU cluster, H100 nodes | CPU cluster (GPU nodes drained) |
| Software | Recent OS; pixi runs natively | CentOS 7; modern tools need **Singularity containers** |
| Access | ssh alias `arc` or `chimera-login` | ssh alias `ircbc`, behind a **VPN** you start by hand |
| Lab perks | Free `zhoulab_gpu_priority` partition, plus free preemptible tiers | Shared package store with prebuilt container images |

Which cluster fits a task is **your call**. The agent asks, or reads the
answer from context. It never picks one in silence.

## What the skill enforces

- **Preflight first.** The agent checks that your `~/.ssh/config` defines the
  lab aliases. If it does not, the agent refuses the request and points you
  at the setup steps. It never asks you for a raw address or a password.
- **Work belongs on a compute node.** The agent moves onto a compute node
  and stays there. A login node is a doorway, not a workspace. Each cluster
  has one, and everybody shares it. A crowd of agents each firing off
  "small" commands is what brings it down. So `ssh arc '<command>'` is the
  wrong move, even for a one-liner. The Slurm tools you need — `squeue`,
  `sbatch`, `scancel` — all run on the compute node anyway.
- **Two reasons to touch a login node, and no others.** First: you hold no
  job yet, and only a login node can submit the first one. Second: the
  compute node truly lacks something. On ircbc that means internet access
  and `git`. On arc it means nothing at all. The arc compute nodes have
  their own internet and a full toolchain, so once you land on one, stay.
- **Reuse the idle job.** This is the normal path, not a nicety. The lab
  keeps a long-lived idle GPU job parked on arc, so a node is usually
  waiting for you. The agent finds it with `squeue` and works there. If no
  job is running anywhere, it offers to start one first.
- **Show before submit.** You see the exact `sbatch` or `srun` before it
  runs.
- **VPN rule.** If ircbc does not answer, the agent stops and asks you to
  check the VPN. It will not retry in a loop.

## The development workflow it follows

Code is written on your own machine and travels through GitHub: edit,
`git push`, then `git pull` on the cluster, then run on a **compute** node.
The agent knows the usual code directory on each cluster, and reads your own
settings from `~/.claude/compute/personal.md`.

## When it triggers

Any mention of the clusters or of remote compute: ssh to a lab server,
Slurm commands (`sbatch`, `srun`, `squeue`), GPU or compute nodes, moving
files to a cluster, testing code remotely.
