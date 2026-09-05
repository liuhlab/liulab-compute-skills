# arc (aka chimera / ARC) — hosts, network, toolchain, storage

What the machines are and what they can reach; partitions and submitting are in `arc-slurm.md`,
and the rule about where work runs is `SKILL.md`'s. Hosts appear only as `~/.ssh/config` aliases —
resolve them at run time, never record what they hide. arc is a modern GPU cluster (H100 nodes:
184 CPUs, ~1 TB RAM, 4 GPUs each; high-mem variants ~2 TB), so use it for GPU work and anything
needing a current OS/glibc. **No VPN** (that is ircbc's rule): if `ssh arc` hangs, VPN is not why.

## Hosts

- **Login:** `arc` or `chimera-login`, one machine. A doorway: submit the first job, then leave.
  Once you hold a node the login node has no remaining use — everything below, Slurm included,
  works from the node itself.
- **Bulk transfer:** `chimera-transfer`, for genuinely large moves only. Ordinary files go straight
  to the compute node: `rsync` from a laptop is ~3 s round trip through the ProxyJump (2026-09-04).
- **Compute nodes:** Slurm node names (`GPU****` / `CPU****` style) double as ssh aliases that
  ProxyJump through the login host — roughly 31 of them, in one shared `Host` stanza.

## Landing on a node (verified 2026-09-04)

`ssh <node-alias>` is not a bare ssh: `pam_slurm_adopt` adopts the session into your job's `step_extern`
cgroup, setting `$SLURM_JOB_ID` alone (`SLURM_JOB_NAME` and `SLURM_NODELIST` stay empty). Hence:

- **The session is cgroup-confined.** `nproc` and `nvidia-smi` report your *allocation*, not the
  machine — 48 CPUs / 1 GPU observed where the node has 184 / 4. Size work from Slurm, never from
  `nproc`. Nodes are shared; three other jobs were resident at the same time.
- **A node you hold no job on refuses you** in ~2 s, exit 255, stderr `Access denied by
  pam_slurm_adopt: you have no active jobs on this node` — so sweeping all ~31 aliases for your
  foothold is cheap. But exit 255 also means `Host key verification failed`: a minority of aliases
  are missing from `known_hosts`, and the effective `StrictHostKeyChecking ask` would hang an agent
  on a prompt. Probe with `-o BatchMode=yes` (fails cleanly) or `-o StrictHostKeyChecking=accept-new`.
- **Expect transient noise.** A `Connection timed out during banner exchange`, and a bogus
  `Slurmctld(primary) … is DOWN` from `scontrol ping` while every other client worked, both cleared
  on retry inside one session. Retry once before believing either; never gate on `scontrol ping`.

## Internet and toolchain on the compute node (verified 2026-09-04)

Internet is direct and unproxied — no `*_proxy` variables set at all. GitHub, `pypi.org` and
conda-forge repodata answer 200; `ghcr.io/v2/` answers 401, its unauthenticated challenge, so the
registry is reachable; `git ls-remote` over HTTPS returns real SHAs. Outbound *ssh* to GitHub finds
no key (`Permission denied (publickey)`), so use HTTPS — `gh` 2.4.0 is token-authenticated and set
to HTTPS. Also present: `git` 2.34.1, `python3` 3.10.12, `nvidia-smi`, `rsync`, `tmux`, `screen`,
`singularity`, `apptainer`, `docker`, `curl`, `wget`, `jq`, `node`, and the `sh_gpu` / `sh_dev`
wrappers in `/usr/local/bin`.

- **`module` does not exist on arc** — no Lmod, no environment-modules; `/etc/profile.d` holds plain
  per-app scripts. Any `module load` line is simply wrong here; that is ircbc's habit, not arc's.
- **`pixi`, `uv`, `conda` and `mamba` need a login shell.** They live under the user's home, so
  `ssh <node> 'command -v pixi'` says not found while `ssh <node> 'bash -lc "command -v uv"'` finds
  it. Wrap remote commands in `bash -lc "…"` or use absolute paths — a bare `command -v` probe lies.

## Storage (verified 2026-09-04)

`$HOME` and `/large_storage` are both wekafs network filesystems, mounted identically on login and
compute nodes, so there is nothing to stage between them. `$HOME` is ~932 G with ~751 G free;
`/large_storage` is 2.3 P, 81% used, ~455 T free. `/tmp` is node-local ext4, ~916 G with ~777 G
free, and writable, as is `/dev/shm`; `/scratch` exists but is not writable, and there is no
`/local` or `/localscratch`. Lab code lives in `/large_storage/zhoulab/<user>/pkg`, one directory
per repo with the same names as local ones, synced local → GitHub → `git pull` on the node.
