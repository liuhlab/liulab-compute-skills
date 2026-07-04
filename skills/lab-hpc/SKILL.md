---
name: lab-hpc
description: >-
  Lab HPC clusters (arc/chimera GPU cluster, ircbc CPU cluster) and the lab's
  remote-compute workflow. Use whenever a task involves ssh to a lab server,
  running or testing code on a remote machine, Slurm jobs (sbatch, srun,
  squeue, salloc), GPU/CPU compute or login nodes, the zhoulab_gpu_priority
  partition, transferring files to a cluster, or syncing code local ->
  GitHub -> remote. Consult BEFORE the first ssh or Slurm command of any
  session. Covers host aliases, which cluster to pick, safety rules (never
  run compute on a login node), and per-user config (~/.ssh/config,
  personal.md).
---

# Lab HPC clusters & remote-compute workflow

This skill documents **shared lab infrastructure**: cluster roles, workflow,
and safety rules. It deliberately contains **no connection details** — no IP
addresses, no usernames, no key files, no credentials. All of that lives on
each user's own machine and is resolved at run time (step 0 below). Never
write such details into this skill, into any repo, or into command output
that gets committed.

## Step 0 — preflight & per-user details (always do this first)

1. **Preflight — verify this machine is configured.** Run the bundled check
   (path relative to this skill's directory):

   ```bash
   bash scripts/check-hpc-config.sh          # add --live to also test ssh
   ```

   It reports, per cluster, `CONFIGURED` or `NOT CONFIGURED (missing: …)`
   based on the user's own `~/.ssh/config`. **If the cluster the task needs
   is NOT CONFIGURED, refuse the HPC request clearly**: say this machine
   isn't set up for that cluster, list the missing ssh aliases, and point
   the user to the repo README's "Per-user config" section. Do NOT
   improvise around it — never ask for or use raw IPs, passwords, or keys;
   SSH setup is out of scope for this skill and must never be automated or
   stored.
2. If `~/.claude/compute/personal.md` exists, **read it now** — it carries
   the user's per-cluster usernames, code dirs, and reservation/sbatch
   notes, and takes precedence over the defaults in this skill and its
   references.
3. All lab hosts are reached through conventional **aliases in each user's
   own `~/.ssh/config`**: `arc` / `chimera-login`, `chimera-transfer`,
   `chimera-gpu`, `chimera-cpu`, `ircbc`, `ircbc-transfer`, `cpu01`…`cpu08`,
   plus per-node compute aliases. Read `~/.ssh/config` to resolve hostnames
   and usernames — never hardcode them, never record them anywhere.

## Hard rules (safety)

- **Never run compute on a login node.** For anything heavy, get a Slurm
  compute job first, then ssh/run on the allocated node. Ask before assuming
  a node is available.
- Compute nodes (`GPU****`/`CPU****` aliases on chimera, `cpu01`–`cpu08` on
  ircbc) are reachable **only while the user holds a Slurm job on them**.
- If ssh to `ircbc` (or its compute/transfer nodes) hangs or times out:
  **stop and tell the user to check the VPN** (atrust app, managed manually
  by the user). Never try to work around it.
- **Never submit sbatch/srun work on the user's behalf without showing the
  exact script/command and getting their confirmation first** (applies to
  every skill in this plugin; tiny read-only probes like `squeue` are fine).

## Development workflow

- Develop code **locally**; run/test heavy work on **remote HPC**.
- Sync path: local edits → `git push` → GitHub → `git pull` on the remote →
  test on a **compute** node (not a login node).
- Repos generally use the **same directory name** locally and remotely.
- `git` and `gh` are already authenticated on local machines and all remotes.

## Choosing a cluster — the user's call

Cluster choice is complex (task, project, where the data lives) — **never
decide it silently**. If the session context doesn't already pin it down
(the user named a cluster, personal.md or the project says so, or the data
already lives on one), **ask the user**. Per-cluster factors:

- **`arc_hpc`** (aka chimera / ARC) — GPUs; modern OS/glibc; envs run
  natively via pixi. See `references/arc-hpc.md`.
- **`ircbc_hpc`** — CPU-only in practice; work ALWAYS runs inside
  Singularity with the lab's `ghcr.io` containers (the bare OS is CentOS 7,
  glibc 2.17 — modern binaries will not run on it); pull/build/use the SIFs
  with the **`lab-containers`** skill. See `references/ircbc-hpc.md`.
- Environments are managed with **pixi** and shipped as `ghcr.io` containers
  by the `liulab-runtime` repo — on arc they normally run natively via pixi
  (no SIFs needed); on ircbc always consume them via Singularity.

## Quick reference

| Cluster | Login alias | Transfer alias | Get a compute node | Code dir |
|---|---|---|---|---|
| arc_hpc (chimera) | `arc` / `chimera-login` | `chimera-transfer` | `sbatch`/`salloc` on `zhoulab_gpu_priority` | `/large_storage/zhoulab/<user>/pkg` |
| ircbc_hpc | `ircbc` | `ircbc-transfer` (no `/share` mount — copy onward after landing; see `references/ircbc-hpc.md`) | Slurm job → ssh `cpu01`…`cpu08` | `/share/home/<user>/src` |

- `<user>` = the per-cluster username from `~/.ssh/config` /
  `~/.claude/compute/personal.md`.
- arc: prefer `zhoulab_gpu_priority` (free, usually available) or the free
  preemptible partitions; interactive `ssh chimera-gpu` / `ssh chimera-cpu`
  (shared queues) often wait long — cost/queue detail in
  `references/arc-hpc.md`.

## Deep detail

For node-access patterns, the reserved-partition sbatch example, and
Singularity usage, read:

- `references/arc-hpc.md` — chimera/ARC GPU cluster
- `references/ircbc-hpc.md` — ircbc CPU cluster
