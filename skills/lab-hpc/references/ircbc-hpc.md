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

- **Login:** `ircbc`. Light work only: editing, git, Slurm commands, and
  network downloads (see below). **No compute.**
- **File transfer:** `ircbc-transfer` (note: this alias uses a separate,
  shared lab account — whatever is configured in the user's `~/.ssh/config`).
- **Compute nodes:** `cpu01`…`cpu08`, ProxyJump through `ircbc`. Reachable
  **only while the user holds a Slurm job on them**.

## Network topology (verified 2026-07-04) — plan around this

| Node | Internet | Notes |
| --- | --- | --- |
| compute (`cpu01`…) | **none** | Jobs must never assume network. Stage downloads beforehand. |
| login (`ircbc`) | limited, via **SOCKS proxy** | `socks5h://127.0.0.1:1080` (tunneled from the transfer node); already exported as `http(s)_proxy`/`ALL_PROXY` in the shell profile, so `curl`/`git` just work. Go tools accept it too. |
| transfer (`ircbc-transfer`) | **full, direct** | Small VM: ~1 TB local disk, few cores, and it does **NOT mount `/share`** — anything fetched there must be copied over afterwards. |

Rule of thumb: **download on the login node (through the proxy) directly
onto `/share`; compute on the compute nodes from local files.** Use the
transfer node only when the proxy path fails.

**Local → `/share` uploads** (verified 2026-07-05): `rsync`/`scp` from the
local machine through the `ircbc` login alias straight onto `/share`. Fall
back to `ircbc-transfer` only if that path fails — it does **not** mount
`/share`, so data landing there needs a second hop.

**Proxy-env gotcha:** `srun`/`sbatch` from the login node propagate the
proxy variables into jobs, but compute nodes have no `127.0.0.1:1080`
tunnel — so anything honoring `http(s)_proxy` fails to fetch, and even
`curl http://127.0.0.1:<port>` probes of on-node services get misrouted
into the dead proxy. In job scripts either
`unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy`
(there is no internet to reach anyway) or use `curl --noproxy '*'` for
localhost traffic.

## Lab package store: `$LIU_LAB_PACKAGES`

Shared images/tools live in `/share/lhqlab/liulab_data/packages`, exposed as
the env var `LIU_LAB_PACKAGES` (exported in users' shell profiles):

- `bin/` — static helper binaries (`crane` for registry pulls) and smoke-test
  scripts (`test-jupyter-ml.sh` — Jupyter-in-SIF check, run it via `srun`)
- `oci/` — transient docker-archive tarballs (deleted after the SIF builds)
- `*.sif` — built Singularity images
- `*.sif.digest` — sidecar recording the ghcr.io image digest each SIF was
  built from (the `lab-containers` skill compares it against
  `crane digest` for update checks)
- `logs/` — build-job logs

The whole store is group-writable for `lhqlab` with setgid dirs — keep it
that way so any lab member can add or update images.

## Getting container images onto ircbc (no-internet compute nodes)

`singularity pull docker://…` needs network, so network and compute are
split: `crane pull` a docker-archive tarball on the login node, then
`singularity build` the SIF in a compute job. The full step-by-step recipe
(inventory, pull, build, per-env smoke test) is the **`lab-containers`**
skill — use it.

## Slurm on ircbc — how to submit (verified 2026-07-04)

No accounting/QOS caps are exposed (`sacctmgr` returns nothing); no
`--account` needed. `DefaultTime`/`MaxTime` are unlimited — set `--time`
anyway so runaway jobs die. Slurm 18.08 flag gotchas: `squeue --me` does not
exist (use `squeue -u $USER`); expect other modern flags to be missing too.

| Partition | Nodes | Per node | Notes |
| --- | --- | --- | --- |
| `compute_cpu` (default) | `cpu01`–`cpu08` | 56 CPUs, ~100 GB | **MaxNodes=2 per job.** The workhorse partition. |
| `compute_fat` | 2 fat nodes | 160 CPUs, ~1–2 TB | Big-memory jobs. |
| `compute_gpu_2080` | 2 nodes | 4× RTX 2080 | Both nodes were **drained** when checked — treat this cluster as CPU-only in practice. |

Quick interactive check / smoke test:

```bash
ssh ircbc 'srun -p compute_cpu -t 10 bash -lc "hostname"'
```

**Idle-job reuse (default — prefer over `ssh ircbc "…"`):** find jobs with
`ssh ircbc 'squeue -u $USER'` (no `--me` on Slurm 18.08); if an idle job holds
a `cpu0X` node, `ssh` to it (ProxyJump via `ircbc`) and run there rather than
queueing new. This is the skill's "Default execution target" flow.

## Running work: `module load singularity` + lab containers

Singularity is **not on PATH** — it ships as an OpenHPC module
(`singularity/3.2.1`, available on login and compute nodes; note it is an
old 3.x — very new image features may not work):

```bash
module load singularity
```

Environments are built with pixi and published as containers by the
`liulab-runtime` repo (check its README for current image names and tags).
Verified run/shell/Jupyter patterns inside the images — including the
required pixi-env activation (`source /app/.pixi/activate-<env>.sh`) and
bind mounts — are the **`lab-containers`** skill's "Using the images"
section; use it rather than writing raw `singularity exec` lines. Images
must be built beforehand into `$LIU_LAB_PACKAGES` (compute nodes cannot
pull — see above).

Never run modern toolchains (recent Python builds, compiled binaries from
elsewhere) directly on the host OS — glibc 2.17 will break them.

## Storage / code

- Code lives in `/share/home/<user>/src`, with the same directory names as
  local repos, synced via git (local → GitHub → `git pull` remote).
