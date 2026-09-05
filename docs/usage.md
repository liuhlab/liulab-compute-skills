# Basic usage

Talk to your agent about cluster work and the right skill loads itself. In Claude
Code you can also call one directly: `/lab-compute:lab-hpc`, or `lab-jupyter`, or
`lab-containers`.

[lab-edison](skills/lab-edison.md) is the exception. It never loads on its own,
because every run spends your own credits. Ask for it by name.

## Things you can ask

**"Test this repo on chimera."** The agent moves your code the lab way, local to
GitHub to a `git pull` on the cluster. It takes a compute node, never the login
node, and runs the tests there. You see the exact `sbatch` or `srun` first.

**"Get me a GPU node on chimera."** It drafts a job on the lab's free
`zhoulab_gpu_priority` partition and asks what you want: CPUs, memory, GPUs,
time.

**"Start Jupyter Lab on the cluster and open it on my laptop."**
[lab-jupyter](skills/lab-jupyter.md) checks whether you already have a Jupyter job
running, and reuses it. Otherwise it submits one with your approval, opens an ssh
tunnel, and hands you a `http://localhost:9990/lab?token=…` link that works in
your browser. Either cluster.

**"Update the ml container image on ircbc."**
[lab-containers](skills/lab-containers.md) compares your image's recorded digest
against the registry and tells you whether an update is actually needed. Only then
does it pull and rebuild, pulling on the login node and building in a job, because
ircbc's compute nodes have no internet.

**"Run this alignment on ircbc."** The command runs inside the right lab
container, in a Slurm job, with the environment active. The bare OS there is far
too old for modern tools.

**"/lab-compute:lab-edison what is known about …"**
[lab-edison](skills/lab-edison.md) checks your key file, names the job it picked,
prints your question in full, and only then sends it. You get an answer with
citations, and the task id that paid for it. No cluster on this path.

## What the agent will ask you

Which cluster, unless your request already makes it obvious. What the job needs:
CPUs, memory, GPUs, wall time. And your confirmation of the exact command before
any job is submitted.

It also asks before cancelling or deleting anything shared. Reservation jobs and
container images belong to the whole group.

## Tips

Fill in `~/.claude/compute/personal.md` with your Jupyter port, launch path and
usual job resources, and the agent stops re-asking session after session.

Name the cluster in your request ("…on chimera", "…on ircbc") to skip the
which-cluster question.

The skills tell the agent to read your ssh config, never to change it. SSH setup
stays in your hands.
