# lab-jupyter: notebooks on the cluster

Gets a Jupyter Lab running on a cluster compute node and makes it reachable at
`http://localhost:<port>` in your local browser. It works on either cluster.

## How a session goes

1. **Reuse before submit.** The agent lists your running jobs first. If you
   already have a Jupyter job or an idle reservation, it works on that node
   instead of queueing a new one, and it asks before borrowing a reservation.
2. **Submit with your approval.** Otherwise it drafts a Slurm job, asks which
   resources you want, and shows you the exact command before submitting. On arc
   that runs your own Jupyter install; on ircbc it runs inside the lab's container
   image.
3. **Token.** It fishes the login URL and token out of the job's log.
4. **Tunnel.** It opens a background ssh tunnel to the compute node and checks
   that the tunnel works. Then it hands you the full
   `http://localhost:<port>/lab?token=…` link.
5. **Cleanup when you ask.** It kills the tunnel. It cancels the job only after
   asking, and it never cancels a job it did not start.

## What differs between the clusters

On arc your own Jupyter, named in `personal.md`, runs in a job on the free
`zhoulab_gpu_priority` partition. Pick this side for GPU work.

On ircbc Jupyter lives inside the lab's Singularity image, described in
[lab-containers](lab-containers.md). The agent uses the container launch command,
and the cluster's older Slurm dialect, without being told.

## What you will be asked

Which cluster, unless the context makes it obvious. Job resources: CPUs, memory,
GPUs, time. And confirmation of the job command before it is submitted.

Fill in `~/.claude/compute/personal.md` and most of those questions go away. It
holds your port (9990 by default), the path to your Jupyter on arc, and the
resources you usually ask for.

## When it triggers

"Jupyter on the cluster", "notebook on a GPU node", "tunnel to a compute node",
"reconnect to my Jupyter job".
