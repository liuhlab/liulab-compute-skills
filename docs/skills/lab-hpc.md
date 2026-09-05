# lab-hpc — clusters, Slurm, and safety

The foundation skill. It loads before any ssh or Slurm work and gives the
agent the lab's cluster map, workflow, and hard safety rules. The other two
skills build on it.

## The two clusters

| | arc_hpc (aka chimera / ARC) | ircbc_hpc |
| --- | --- | --- |
| Hardware | Modern GPU cluster (H100 nodes) | CPU cluster (GPU nodes drained in practice) |
| Software | Recent OS, environments run natively via pixi | CentOS 7 — modern tools only work **inside Singularity containers** |
| Access | ssh aliases `arc` / `chimera-login`, … | ssh alias `ircbc`, behind a **VPN** you manage manually |
| Lab perks | Free `zhoulab_gpu_priority` partition (lab-reserved node) and free preemptible tiers | Shared lab package store with prebuilt container images |

Which cluster to use for a given task is **your call** — the agent asks or
infers it from context, never decides silently.

## What the skill enforces

- **Preflight first.** On every machine it checks that your `~/.ssh/config`
  actually defines the lab aliases. If not, it refuses the request and
  points you at the setup steps — it will never ask for raw addresses or
  passwords.
- **No heavy work on login nodes.** Login nodes are for light commands only
  (browsing, editing, git, Slurm control, small transfers); anything
  heavy — `pixi`, builds, big downloads, data processing, training — gets a
  Slurm compute job first. In particular the agent won't run work as
  `ssh arc "<command>"`.
- **Reuse your idle interactive job.** Rather than loading the login node,
  the agent looks for an interactive Slurm job you already keep running
  (`squeue`) and `ssh`es onto that node to work; if none exists it offers to
  start one first. This keeps parallel agents/subagents off the login node.
- **Show before submit.** Every `sbatch`/`srun` is shown to you for
  approval before it runs.
- **VPN rule.** If ircbc doesn't respond, the agent stops and tells you to
  check the VPN instead of retrying forever.

## The development workflow it follows

Code is developed locally and synced through GitHub: local edits →
`git push` → `git pull` on the cluster → run on a **compute** node. The
agent knows the standard code directories on each cluster and reads your
personal overrides from `~/.claude/compute/personal.md`.

## When it triggers

Any mention of the clusters or remote compute: ssh to a lab server, Slurm
commands (`sbatch`, `srun`, `squeue`), GPU/compute nodes, transferring
files to a cluster, testing code remotely.
