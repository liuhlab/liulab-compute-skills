# lab-jupyter — notebooks on the cluster

Gets a Jupyter Lab running on a cluster compute node and makes it reachable
at `http://localhost:<port>` in your local browser, on either cluster.

## How a session goes

1. **Reuse before submit.** The agent lists your running jobs first. If you
   already have a Jupyter or reservation job, it reuses that instead of
   queueing a new one (and asks before piggybacking on an idle
   reservation).
2. **Submit with your approval.** Otherwise it drafts a Slurm job — on arc
   with your own Jupyter install, on ircbc inside the lab's container
   image — asks for the resources you want, and shows you the exact command
   before submitting.
3. **Token.** It fishes the login URL + token out of the job's log.
4. **Tunnel.** It opens a background ssh tunnel from your machine to the
   compute node and checks it works, then hands you the full
   `http://localhost:<port>/lab?token=…` link.
5. **Cleanup on request.** When you're done it kills the tunnel and — only
   after asking — cancels the job. It never cancels jobs it didn't start.

## Cluster differences it handles for you

- **arc/chimera**: runs your own Jupyter (from `personal.md`) in a job on
  the free `zhoulab_gpu_priority` partition — pick this side for GPU work.
- **ircbc**: Jupyter lives inside the lab's Singularity image (see
  [lab-containers](lab-containers.md)); the agent uses the container launch
  command and the cluster's older Slurm dialect automatically.

## What you'll be asked

- Which cluster (unless obvious from context).
- Job resources: CPUs, memory, GPUs, time.
- Confirmation of the job command before it is submitted.

Fill in `~/.claude/compute/personal.md` (port — default 9990 —, the
absolute path of your Jupyter on arc, your usual resources) and most of the
questions disappear.

## When it triggers

"Jupyter on the cluster", "notebook on a GPU node", "tunnel/port-forward to
a compute node", "reconnect to my Jupyter job".
