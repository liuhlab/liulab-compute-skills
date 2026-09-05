---
name: lab-jupyter
description: >-
  Start (or reuse) an interactive Jupyter Lab on a lab HPC cluster and
  tunnel it to the local machine. Use when the user wants Jupyter Lab / a
  notebook on the cluster, an ssh tunnel or port forward to a compute node,
  to reconnect to a running Jupyter job, or to work interactively on a GPU
  node from a local browser. Cluster-aware: arc/chimera = zhoulab_gpu_priority
  Slurm job + ssh -L tunnel; ircbc = Jupyter inside the lab's Singularity
  image (lab-containers). Always confirm the sbatch script with the user
  first.
---

# Jupyter Lab on the cluster + local tunnel

Get a Jupyter Lab running on a cluster compute node and reachable at
`http://localhost:<port>` on the local machine. Follow the `lab-hpc` skill's
rules (preflight, no compute on login nodes, aliases from `~/.ssh/config`).

## Cluster parameters — pick these first

Which cluster is the user's call — ask or infer from session context
(`lab-hpc`'s rule); never pick one silently. One lifecycle (reuse → submit
→ token → tunnel → cleanup) then serves both clusters. Steps 1–5 show arc
commands; on ircbc substitute from this table:

| Parameter | arc_hpc (chimera) | ircbc_hpc |
| --- | --- | --- |
| Login alias | `arc` | `ircbc` |
| List my jobs | `squeue --me` | `squeue -u $USER` (Slurm 18.08 has no `--me`) |
| Partition | `zhoulab_gpu_priority` | `compute_cpu` (no GPU there) |
| Jupyter runs | natively — `<jupyter>` in a Slurm job (step 2) | inside `liulab-runtime_<env>.sif` — take the sbatch verbatim from `lab-containers` § "Jupyter Lab in the container" |
| Job log (token grep) | `sbatch/jupyter.<jobid>.log` | `$LIU_LAB_PACKAGES/logs/jupyter.<jobid>.log` |
| Tunnel target | the job's node alias (from `%N`) | the job's `cpu01`…`cpu08` alias |

On ircbc, read `lab-hpc`'s `references/ircbc-hpc.md` first — the VPN and
proxy-env gotchas there apply to every step.

**Per-user inputs** (read `~/.claude/compute/personal.md` first):

- `<port>` — Jupyter port (default `9990`).
- `<jupyter>` — (arc only) how to launch Jupyter in the user's remote
  environment. `sbatch` inherits the *submitting shell's* environment, and
  the user's env manager may not load in non-interactive ssh — so prefer an
  **absolute path** from personal.md (e.g. `~/…/bin/jupyter`). If unknown,
  try `ssh arc 'bash -lc "which jupyter"'`; if still not found, **ask the
  user** which environment provides Jupyter — do not guess-install anything.
  On ircbc no `<jupyter>` is needed — the launch command ships inside the
  container sbatch.

## 1. Reuse before you submit

```bash
ssh arc 'squeue --me -h -o "%i %j %T %N %L"'
```

`<node>` = the job's node from `%N`; node names double as ssh aliases
(on ircbc these are the `cpu01`…`cpu08` aliases).

If a RUNNING job looks like a reservation/Jupyter job (name `reserve`,
`jupyter`, `ray`, …), check whether Jupyter is already listening on its node:

```bash
ssh <node> 'ss -tln | grep -E "127\.0\.0\.1:<port>"'
```

- Listening → skip to step 3 with that node. Reusing an idle reserved job
  is the lab's preferred pattern. (Exception on ircbc: if the SIF was just
  updated via `lab-containers` §1–§3, a running Jupyter job still uses the
  old image — ask whether to cancel and resubmit instead of reusing.)
- A reservation job is RUNNING but nothing listens on `<port>` (arc) → ask
  the user whether to start Jupyter inside that job by ssh-ing to its node
  (idle-job reuse — `lab-hpc`'s "Default execution target") instead of
  queueing a duplicate; go to step 2 only if they prefer a fresh job.
- Never scancel someone's reservation to make room.

## 2. Submit a Jupyter job

**Resources are the user's call — ask, don't assume.** Get explicit values
for `--cpus-per-task`, memory (`--mem-per-cpu` or `--mem`), `--gpus`, and
`--time` (personal.md may carry the user's usual defaults). Partition:
`zhoulab_gpu_priority` is the standard arc choice; `cpu_preemptible` only
for a no-GPU session that tolerates requeueing — cost/queue trade-offs in
`lab-hpc`'s `references/arc-hpc.md`.

**Always show the user the exact sbatch command/script and get their
confirmation BEFORE submitting.** arc shape:

```bash
ssh arc 'mkdir -p sbatch && sbatch --job-name=jupyter \
  --partition=zhoulab_gpu_priority --time=<time> \
  --cpus-per-task=<cpus> --mem-per-cpu=<mem> --gpus=<gpus> \
  --output=sbatch/jupyter.%j.log --error=sbatch/jupyter.%j.log \
  --wrap "<jupyter> lab --no-browser --port=<port>"'
```

On ircbc, use the sbatch from `lab-containers` § "Jupyter Lab in the
container" verbatim (still confirm first), then continue with the rest of
this step, substituting per the table — the poll and probe below apply on
both clusters.

After the user approves and it is submitted, wait until it runs and get the
node:

```bash
ssh arc 'squeue -j <jobid> -h -o "%T %N"'   # poll until RUNNING
```

Then confirm Jupyter is up (it can take ~10–30 s) with the step-1 listening
probe on `<node>`.

Jupyter binds to **localhost on the compute node only** — that is correct
and required; never make it listen on `0.0.0.0`.

## 3. Get the URL + token

- Job submitted in step 2 → grep its log on the login node (scoped to the
  job, no `<jupyter>` path needed):
  `ssh arc 'grep -m1 "?token=" sbatch/jupyter.<jobid>.log'`
  (ircbc log path per the table).
- Job reused from step 1 → ask the running server instead — a pre-existing
  job may log elsewhere: `ssh <node> '<jupyter> server list'`. arc only; on
  ircbc Jupyter lives inside the SIF, so always grep the job's log.

## 4. Tunnel from the local machine

Compute-node aliases already ProxyJump through the login node, so a plain
`-L` tunnel works. Check the local port is free, then background the tunnel:

```bash
lsof -nP -iTCP:<port> -sTCP:LISTEN || true   # must print nothing
ssh -f -N -L <port>:localhost:<port> <node>
curl -s http://localhost:<port>/api           # → {"version": ...}
```

Give the user: `http://localhost:<port>/lab?token=<token>`.

If the local port is busy, identify the listener before touching anything:

```bash
ps -o pid=,command= -p "$(lsof -tnP -iTCP:<port> -sTCP:LISTEN)"
```

- An ssh tunnel to the SAME node → reuse it; hand over the URL.
- An ssh tunnel to a different/dead node → `kill <pid>` (that PID only),
  then re-tunnel.
- Anything else → do not kill it; pick a different `<port>` and re-tunnel.

## 5. Cleanup (only when the user is done)

- Kill the local tunnel: `pkill -f "ssh -f -N -L <port>"` (safe here — this
  flow created it).
- Cancel the job: `ssh arc 'scancel <jobid>'` — **ask before cancelling**;
  a reservation job may be intentionally long-lived, and never cancel jobs
  you didn't start.
