---
name: lab-jupyter
description: >-
  Start (or reuse) an interactive Jupyter Lab on the lab's arc/chimera HPC
  cluster and tunnel it to the local machine. Use when the user wants
  Jupyter Lab / a notebook on the cluster, an ssh tunnel or port forward to
  a compute node, to reconnect to a running Jupyter job, or to work
  interactively on a GPU node from a local browser. Handles: finding an
  existing idle Jupyter job, submitting a new Slurm job that runs Jupyter,
  locating the node and token, and opening ssh -L localhost tunnels.
---

# Jupyter Lab on the cluster + local tunnel

Get a Jupyter Lab running on an arc/chimera compute node and reachable at
`http://localhost:<port>` on the local machine. Follow the `lab-hpc` skill's
rules (preflight, no compute on login nodes, aliases from `~/.ssh/config`).

**Per-user inputs** (read `~/.claude/compute/personal.md` first):

- `<port>` — Jupyter port (default `9990`).
- `<jupyter>` — how to launch Jupyter in the user's remote environment.
  `sbatch` inherits the *submitting shell's* environment, and the user's env
  manager may not load in non-interactive ssh — so prefer an **absolute
  path** from personal.md (e.g. `~/…/bin/jupyter`). If unknown, try
  `ssh arc 'bash -lc "which jupyter"'`; if still not found, **ask the user**
  which environment provides Jupyter — do not guess-install anything.

## 1. Reuse before you submit

```bash
ssh arc 'squeue --me -h -o "%i %j %T %N %L"'
```

If a RUNNING job looks like a reservation/Jupyter job (name `reserve`,
`jupyter`, `ray`, …), check whether Jupyter is already listening on its node:

```bash
ssh <node> 'ss -tln | grep -E "127\.0\.0\.1:<port>"'
```

If yes → skip to step 3 with that node. Reusing an idle reserved job is the
lab's preferred pattern; never scancel someone's reservation to make room.

## 2. Submit a Jupyter job

Pick a partition per the `lab-hpc` arc reference: `zhoulab_gpu_priority`
(lab-reserved, long-lived, GPU, no extra cost, usually available) is the
default choice; `cpu_preemptible` for a no-GPU session that tolerates
requeueing. Avoid the shared `gpu`/`cpu` partitions — they queue long and
the GPU ones bill extra. Always set `--time`.

```bash
ssh arc 'mkdir -p sbatch && sbatch --job-name=jupyter \
  --partition=zhoulab_gpu_priority --time=2-00:00:00 \
  --cpus-per-task=24 --mem-per-cpu=6G --gpus=1 \
  --output=sbatch/jupyter.%j.log --error=sbatch/jupyter.%j.log \
  --wrap "<jupyter> lab --no-browser --port=<port>"'
```

Wait until it runs, and get the node:

```bash
ssh arc 'squeue -j <jobid> -h -o "%T %N"'   # poll until RUNNING
```

Then confirm Jupyter is up (it can take ~10–30 s):

```bash
ssh <node> 'ss -tln | grep 127\.0\.0\.1:<port>'
```

Jupyter binds to **localhost on the compute node only** — that is correct
and required; never make it listen on `0.0.0.0`.

## 3. Get the URL + token

Either ask the running server (absolute jupyter path again):

```bash
ssh <node> '<jupyter> server list'
```

or grep the job log on the login node: `ssh arc 'grep -m1 "?token=" sbatch/jupyter.<jobid>.log'`.

## 4. Tunnel from the local machine

Compute-node aliases already ProxyJump through the login node, so a plain
`-L` tunnel works. Check the local port is free, then background the tunnel:

```bash
lsof -nP -iTCP:<port> -sTCP:LISTEN || true   # must print nothing
ssh -f -N -L <port>:localhost:<port> <node>
curl -s http://localhost:<port>/api           # → {"version": ...}
```

Give the user: `http://localhost:<port>/lab?token=<token>`.

If the local port is busy (e.g. a stale tunnel), either reuse it if it
already points at the right node, or kill it first:
`pkill -f "ssh -f -N -L <port>"`.

## 5. Cleanup (only when the user is done)

- Kill the local tunnel: `pkill -f "ssh -f -N -L <port>"`.
- Cancel the job: `ssh arc 'scancel <jobid>'` — **ask before cancelling**;
  a reservation job may be intentionally long-lived, and never cancel jobs
  you didn't start.
