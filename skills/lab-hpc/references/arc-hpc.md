# arc_hpc (aka chimera / ARC) — GPU cluster

Modern GPU cluster with Slurm (H100 nodes: 184 CPUs, ~1 TB RAM, 4 GPUs each;
high-mem variants ~2 TB). Use it for GPU work and anything needing a modern
OS/glibc. All hosts below are **`~/.ssh/config` aliases** — resolve
usernames/hostnames from that file (see the skill's step 0); never record
them.

## Hosts

- **Login:** `arc` or `chimera-login` (same machine). Light work only:
  editing, git, Slurm commands, file browsing, transfer small files. **No compute.**
- **File transfer:** `chimera-transfer` — use for `rsync`/`scp` of large data.
- **Interactive compute (convenience aliases):** these ssh straight into a
  fresh interactive Slurm job via a `RemoteCommand` in the user's ssh config:
  - `ssh chimera-gpu` → runs `sh_gpu --cpus-per-task 16 --mem-per-cpu 8`
  - `ssh chimera-cpu` → runs `sh_dev --cpus-per-task 16 --mem-per-cpu 4`
- **Compute nodes:** Slurm node names (`GPU****` / `CPU****` style) double as
  ssh aliases in each user's `~/.ssh/config`, ProxyJumping through
  `chimera-login`. A node is reachable **only while the user holds a Slurm
  job on it**. Find your nodes with `squeue --me` on the login node, then ssh
  to that node name.

## Slurm on arc — how to submit (verified 2026-07-04)

- **Account:** lab members submit under account `zhoulab` (QOS `normal`).
  You normally don't need to pass `--account`.
- **`DefaultTime` is 12 h on every partition — always set `--time`.**
- Jobs are single-node on most partitions (`MaxNodes=1` except the priority
  partition). `PreemptMode=REQUEUE` on the preemptible tiers.

| Partition | Wall limit | Purpose / limits |
|---|---|---|
| `cpu` (default) | 5 d | Interactive CPU work. QOS `cpu_interact`: ≤ 64 CPUs and **≤ 2 running jobs per user**; ≤ 4 GB per CPU. |
| `cpu_batch` | 14 d | CPU batch. QOS `cpu_batch`: ≤ 20 running / 200 queued per user. |
| `gpu` | 1 d | Interactive GPU work; ≤ 32 CPUs per node per job; ≤ 10 GB per CPU. |
| `gpu_batch` | 14 d | GPU batch. |
| `*_high_mem` | 14 d | Same tiers on the ~2 TB nodes. |
| `preemptible` | 14 d | Big fan-outs, **GPU available**; may be requeued anytime. QOS `preempt`: ≤ 100 running / 512 queued. |
| `cpu_preemptible` | 14 d | Same, but **CPU-only** (no GPU). QOS `preempt`. |
| `quick_preemptible` | 2 h | Short tests / smoke jobs (**GPU available**). QOS `quick_preempt`: ≤ 4 running / 8 queued. |
| `zhoulab_gpu_priority` | 14 d | **Lab-reserved node** (account `zhoulab` only, 184 CPUs / 4 GPUs). Highest-priority access; also where long-lived reservations live. |

### Choosing a partition (cost + queue reality)

- **No extra cost:** `zhoulab_gpu_priority` and the preemptible tiers
  (`preemptible`, `cpu_preemptible`, `quick_preemptible`). **Billed extra:**
  the other GPU partitions (`gpu`, `gpu_batch`, `gpu_high_mem`, …). Default
  to the no-cost partitions.
- **GPU work → `zhoulab_gpu_priority` first.** It is usually far more
  available than the shared queues, and free to the lab. For GPU fan-outs
  that tolerate requeueing, `preemptible` (GPU-capable) is the free
  alternative.
- **CPU / batch fan-out → `cpu_preemptible`** (CPU-only, free, lots of
  nodes) when the job tolerates requeueing; `quick_preemptible` for smoke
  tests (has GPUs too).
- The interactive wrappers `sh_gpu` / `sh_dev` (= `ssh chimera-gpu` /
  `chimera-cpu`) queue on the shared `gpu` / `cpu` partitions and **often
  wait a long time, especially for large requests** — for anything sizable,
  prefer an sbatch/salloc on `zhoulab_gpu_priority` (e.g.
  `sh_gpu 1 --partition zhoulab_gpu_priority` or the reservation sbatch
  below) or a preemptible partition instead.

- **Interactive jobs** — cluster-provided wrappers (what the ssh aliases run):
  - `sh_gpu [1-4] [srun/salloc options]` — interactive shell on a GPU node
    (default 1 GPU + 8 cores + 80 GB per GPU; default partition `gpu`).
  - `sh_dev [srun/salloc options]` — interactive shell on a CPU node
    (partition `cpu`, default 2 cores / 8 GB; the 2-running-job cap applies).
- **Quick smoke test** (cheap, doesn't touch lab resources):

  ```bash
  ssh arc 'sbatch --partition=quick_preemptible --time=00:05:00 --wrap=hostname'
  ssh arc 'squeue --me'          # then scancel <jobid> if still queued
  ```

- **Long-lived reservation on the lab partition** (adapted from the repo
  owner's script; adjust resources and payload):

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

  Note: `sbatch` inherits the submitting shell's environment — commands like
  `jupyter` must be on PATH in *your* environment (or use an absolute path;
  see `~/.claude/compute/personal.md`).

**Idle-reservation pattern:** if a reserved job already exists and is idle
(e.g. a Jupyter Lab job that isn't actually computing), it is fine to ssh
into that job's node and use it directly instead of queueing a new job.
Check with `squeue --me` first.

## Storage / code

- Code lives in `/large_storage/zhoulab/<user>/pkg`, with the same directory
  names as local repos, synced via git (local → GitHub → `git pull` remote).
