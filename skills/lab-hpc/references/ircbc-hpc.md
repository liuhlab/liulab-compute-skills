# ircbc_hpc — CPU cluster (old OS; module + Singularity required)

Slurm cluster running **CentOS 7 (kernel 3.10, glibc 2.17)** with an old
**Slurm 18.08** — expect missing newer sbatch/srun flags. Modern binaries
will NOT run on the bare OS — always run real work inside **Singularity**
with the lab's `ghcr.io` container images. All hosts below are
**`~/.ssh/config` aliases** — resolve usernames/hostnames from that file (see
the skill's step 0); never record them.

## VPN — read this first

The whole cluster sits behind a **VPN** (atrust app) that the user manages
manually. If ssh to `ircbc` (or any of its nodes) hangs or times out:
**stop immediately and tell the user to check / re-login the VPN.** Do not
retry in a loop, do not try alternate routes, do not attempt to fix the VPN.

## Hosts

- **Login:** `ircbc`. Light work only: editing, git, Slurm commands. **No
  compute.**
- **File transfer:** `ircbc-transfer` (note: this alias uses a separate,
  shared lab account — whatever is configured in the user's `~/.ssh/config`).
- **Compute nodes:** `cpu01`…`cpu08`, ProxyJump through `ircbc`. Reachable
  **only while the user holds a Slurm job on them**.

## Slurm on ircbc — how to submit (verified 2026-07-04)

No accounting/QOS caps are exposed (`sacctmgr` returns nothing); no
`--account` needed. `DefaultTime`/`MaxTime` are unlimited — set `--time`
anyway so runaway jobs die.

| Partition | Nodes | Per node | Notes |
|---|---|---|---|
| `compute_cpu` (default) | `cpu01`–`cpu08` | 56 CPUs, ~100 GB | **MaxNodes=2 per job.** The workhorse partition. |
| `compute_fat` | 2 fat nodes | 160 CPUs, ~1–2 TB | Big-memory jobs. |
| `compute_gpu_2080` | 2 nodes | 4× RTX 2080 | Both nodes were **drained** when checked — treat this cluster as CPU-only in practice. |

Quick interactive check / smoke test:

```bash
ssh ircbc 'srun -p compute_cpu -t 10 bash -lc "hostname"'
```

## Running work: `module load singularity` + lab containers

Singularity is **not on PATH** — it ships as an OpenHPC module
(`singularity/3.2.1`, available on login and compute nodes; note it is an
old 3.x — very new image features may not work):

```bash
module load singularity
```

Environments are built with pixi and published as containers by the
`liulab-runtime` repo (check its README for current image names and tags).
Typical batch job:

```bash
#!/bin/bash
#SBATCH --job-name=work
#SBATCH --partition=compute_cpu
#SBATCH --time=1-00:00:00
#SBATCH --cpus-per-task=16
#SBATCH --output=sbatch/%x.%j.log

module load singularity
# pull once beforehand: singularity pull docker://ghcr.io/liuhlab/<image>:<tag>
singularity exec --bind /share/home/<user> <image>_<tag>.sif <command...>
```

Never run modern toolchains (recent Python builds, compiled binaries from
elsewhere) directly on the host OS — glibc 2.17 will break them.

## Storage / code

- Code lives in `/share/home/<user>/src`, with the same directory names as
  local repos, synced via git (local → GitHub → `git pull` remote).
