# arc_hpc (aka chimera / ARC) — GPU cluster

Modern GPU cluster with Slurm. Use it for GPU work and anything needing a
modern OS/glibc. All hosts below are **`~/.ssh/config` aliases** — resolve
usernames/hostnames from that file (see the skill's step 0); never record
them.

## Hosts

- **Login:** `arc` or `chimera-login` (same machine). Light work only:
  editing, git, Slurm commands, file browsing. **No compute.**
- **File transfer:** `chimera-transfer` — use for `rsync`/`scp` of large data.
- **Interactive compute (convenience aliases):** these ssh straight into a
  fresh interactive Slurm job via a `RemoteCommand` in the user's ssh config:
  - `ssh chimera-gpu` → runs `sh_gpu --cpus-per-task 16 --mem-per-cpu 8`
  - `ssh chimera-cpu` → runs `sh_dev --cpus-per-task 16 --mem-per-cpu 4`
- **Compute nodes:** individual nodes have `GPU****`-style aliases (plus some
  `CPU****` nodes) defined in each user's `~/.ssh/config`, ProxyJumping
  through `chimera-login`. A node is reachable **only while the user holds a
  Slurm job on it**. To find where a job runs: `squeue --me` on the login
  node, then ssh to that node's alias.

## Reserved partition: `zhoulab_gpu_priority`

The lab has a reserved, highest-priority partition `zhoulab_gpu_priority`.
Example sbatch for a long-lived reservation job (adapted from the repo
owner's script; adjust resources and the payload command):

```bash
#!/bin/bash
#SBATCH --job-name=reserve
#SBATCH --time=5-00:00:00
#SBATCH --partition=zhoulab_gpu_priority
#SBATCH --cpus-per-task=24
#SBATCH --mem-per-cpu=6G
#SBATCH --gpus=1
#SBATCH --output=sbatch/gpu.%j.output.log
#SBATCH --error=sbatch/gpu.%j.error.log

date
cd "$HOME" && jupyter lab --no-browser --port 9990
date
```

**Idle-reservation pattern:** if a reserved job already exists and is idle
(e.g. a Jupyter Lab job that isn't actually computing), it is fine to ssh
into that job's node and use it directly instead of queueing a new job.
Check with `squeue --me` first.

## Storage / code

- Code lives in `/large_storage/zhoulab/<user>/pkg`, with the same directory
  names as local repos, synced via git (local → GitHub → `git pull` remote).
