---
name: lab-jupyter
description: >-
  Start or reuse an interactive Jupyter Lab on a lab HPC cluster and tunnel it to the local machine. Use when the user wants Jupyter Lab or a notebook
  on the cluster, an ssh tunnel or port forward to a compute node, to reconnect to a running Jupyter job, or to work on a GPU node from a local browser.
  Cluster-aware: arc/chimera = zhoulab_gpu_priority Slurm job + ssh -L tunnel; ircbc = Jupyter inside the lab's Singularity image (lab-containers). Confirm the sbatch with the user first.
---

# Jupyter Lab on a compute node, tunnelled to the local browser

Serve Jupyter from a compute node and open it at `http://localhost:<port>` locally. `<port>` defaults to `9990` unless `personal.md` says otherwise, and `lab-hpc`'s rules hold throughout.
Which cluster is the user's call: ask or infer, never pick silently. One lifecycle — reuse, submit, token, tunnel, cleanup — serves both clusters; the commands below are arc's.

| Parameter | arc (chimera) — partitions and cost in `lab-hpc`'s `references/arc-slurm.md` | ircbc — read `lab-hpc`'s `references/ircbc-hpc.md` and `references/ircbc-slurm.md` first |
| --- | --- | --- |
| List jobs, get the node | `squeue --me`; `%N` is the node's ssh alias | `squeue -u $USER` (Slurm 18.08 has no `--me`); nodes are `cpu01`…`cpu08` |
| Submit | partition `zhoulab_gpu_priority`; `<jupyter>` runs natively — take its absolute path from `personal.md`, else `ssh <node> 'bash -lc "which jupyter"'`, since only a login shell sees user-installed tools. Still unknown? Ask; never guess-install | partition `compute_cpu` (no GPU); Jupyter runs inside `liulab-runtime_<env>.sif` — take the sbatch verbatim from `lab-containers` → `references/using-images.md`, § "Jupyter Lab in the container" |
| Job log = token source | `sbatch/jupyter.<jobid>.log` | `$LIU_LAB_PACKAGES/logs/jupyter.<jobid>.log` |

## 1. Reuse before you submit

Reusing an idle job is not just courtesy — it is how you avoid the login node altogether. Find the node you already hold (`lab-hpc`'s SOP). On arc a node you hold no job on refuses ssh quickly — probing never hangs; ircbc has no such gate, so confirm a node is yours before working on it.
The whole Slurm client works from a compute node on both clusters, so list jobs from there — `squeue --me -h -o "%i %j %T %N %L"`, falling back to `ssh arc '<same>'` only when you hold no job anywhere.
For each RUNNING job that looks reusable (`reserve`, `jupyter`, `ray`, …), probe its node: `ssh <node> 'ss -tln | grep -E "127\.0\.0\.1:<port>"'`.

- Listening → go to step 3 with that node. ircbc exception: if `lab-containers` just rebuilt the SIF, the running job still holds the old image, so ask whether to cancel and resubmit instead.
- RUNNING but silent → offer to start Jupyter inside that job, from its node, rather than queueing a duplicate. Never scancel someone else's reservation to make room.

## 2. Submit — only when there is nothing to reuse

Here the login node earns its one use: you hold no allocation, so nothing else can submit the first job. Resources are the user's call — ask for `--cpus-per-task`, `--mem-per-cpu`, `--gpus` and `--time` (`personal.md` may carry defaults).
`zhoulab_gpu_priority` is the lab's own partition — no cost, and usually a far shorter wait than the shared `gpu` queue — but it is `PreemptMode=REQUEUE`: warn that a requeue moves the job and kills the tunnel.
**Show the exact command and get confirmation before submitting**, offering `sbatch --test-only` beside it — a dry run that submits nothing and prints the projected start time, so check the wait rather than guess.
Jupyter binds to **localhost on the compute node only** — never `0.0.0.0`; the tunnel is the only thing that should reach it.

```bash
ssh arc 'mkdir -p sbatch && sbatch --job-name=jupyter --partition=zhoulab_gpu_priority --time=<time> --cpus-per-task=<cpus> \
  --mem-per-cpu=<mem> --gpus=<gpus> --output=sbatch/jupyter.%j.log --error=sbatch/jupyter.%j.log --wrap "<jupyter> lab --no-browser --port=<port>"'
ssh arc 'squeue -j <jobid> -h -o "%T %N"'   # poll to RUNNING, then re-probe until the port answers
```

## 3. Token

Grep the job log (paths above) for `?token=`: `grep -m1 "?token=" sbatch/jupyter.<jobid>.log`, from the node you hold or via `ssh arc '…'`. A reused job, or a log with no token yet, is `references/tunnel.md`'s business.

## 4. Tunnel from the local machine

```bash
lsof -nP -iTCP:<port> -sTCP:LISTEN || true    # must print nothing — if busy, references/tunnel.md
ssh -f -N -L <port>:localhost:<port> <node>   # node aliases ProxyJump through the login node
curl -s http://localhost:<port>/api           # → {"version": ...}
```

Then hand the user `http://localhost:<port>/lab?token=<token>`.

## 5. Cleanup, once the user is done

- Tunnel: `pkill -f "ssh -f -N -L <port>"` — safe here, this flow created it. Kill nothing else.
- Job: `scancel <jobid>` — **ask first.** A reservation may be deliberately long-lived, and a job you did not start is never yours to cancel.
