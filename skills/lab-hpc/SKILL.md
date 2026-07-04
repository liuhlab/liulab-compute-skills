---
name: lab-hpc
description: >-
  Lab HPC clusters (arc/chimera GPU cluster, ircbc CPU cluster) and the lab's
  remote-compute workflow. Use whenever a task involves ssh to a lab server,
  running or testing code on a remote machine, Slurm jobs (sbatch, srun,
  squeue, salloc), GPU/CPU compute nodes, the zhoulab_gpu_priority partition,
  Singularity or ghcr.io containers on HPC, transferring files to a cluster,
  or syncing code local -> GitHub -> remote. Consult BEFORE the first ssh or
  Slurm command of any session touching these clusters. Covers host aliases,
  which cluster to pick, safety rules (never run compute on login nodes;
  ircbc VPN), and per-user config via ~/.ssh/config and
  ~/.claude/compute/personal.md.
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
2. If `~/.claude/compute/personal.md` exists, **read it now** — it overrides
   every default below (usernames, code directories, reservation notes).
3. All lab hosts are reached through conventional **aliases in each user's
   own `~/.ssh/config`**: `arc` / `chimera-login`, `chimera-transfer`,
   `chimera-gpu`, `chimera-cpu`, `ircbc`, `ircbc-transfer`, `cpu01`…`cpu08`,
   plus per-node compute aliases. Read `~/.ssh/config` to resolve hostnames
   and usernames — never hardcode them, never record them anywhere.

## Hard rules (safety)

- **Never run compute on a login node.** For anything heavy, get a Slurm
  compute job first, then ssh/run on the allocated node. Ask before assuming
  a node is available.
- Compute nodes (`GPU****` aliases on chimera, `cpu01`–`cpu08` on ircbc) are
  reachable **only while the user holds a Slurm job on them**.
- If ssh to `ircbc` (or its compute/transfer nodes) hangs or times out:
  **stop and tell the user to check the VPN** (atrust app, managed manually
  by the user). Never try to work around it.

## Development workflow

- Develop code **locally**; run/test heavy work on **remote HPC**.
- Sync path: local edits → `git push` → GitHub → `git pull` on the remote →
  test on a **compute** node (not a login node).
- Repos generally use the **same directory name** locally and remotely.
- `git` and `gh` are already authenticated on local machines and all remotes.

## Choosing a cluster

- **GPU work, or anything needing a modern OS/glibc** → `arc_hpc` (aka
  chimera / ARC). See `references/arc-hpc.md`.
- **CPU-only batch work** → `ircbc_hpc`, ALWAYS inside Singularity with the
  lab's `ghcr.io` containers (the bare OS is CentOS 7, glibc 2.17 — modern
  binaries will not run on it). Images are built by the `liulab-runtime`
  repo. See `references/ircbc-hpc.md`.
- Environments are managed with **pixi** and shipped as `ghcr.io` containers
  (see the `liulab-runtime` repo); on ircbc consume them via Singularity.

## Quick reference

| Cluster | Login alias | Transfer alias | Get a compute node | Code dir |
|---|---|---|---|---|
| arc_hpc (chimera) | `arc` / `chimera-login` | `chimera-transfer` | Prefer `sbatch`/`salloc` on `zhoulab_gpu_priority` (free, usually available) or the preemptible partitions; `ssh chimera-gpu` / `ssh chimera-cpu` (interactive shared queues) often wait long | `/large_storage/zhoulab/<user>/pkg` |
| ircbc_hpc | `ircbc` | `ircbc-transfer` | Slurm job → ssh `cpu01`…`cpu08` | `/share/home/<user>/src` |

`<user>` = the per-cluster username from `~/.ssh/config` /
`~/.claude/compute/personal.md`.

## Deep detail

For node-access patterns, the reserved-partition sbatch example, and
Singularity usage, read:

- `references/arc-hpc.md` — chimera/ARC GPU cluster
- `references/ircbc-hpc.md` — ircbc CPU cluster
