# Basic usage

You don't call the cluster skills explicitly — just talk to your agent
about cluster work and the right skill loads itself. In Claude Code you can
also invoke one directly with `/lab-compute:lab-hpc` (or `lab-jupyter`,
`lab-containers`).

[lab-edison](skills/lab-edison.md) is the exception. It never loads on its
own, because every run of it spends your own credits. Ask for it by name:
`/lab-compute:lab-edison` and then your question.

## Things you can ask

**"Test this repo on chimera."**
The agent syncs your code the lab way (local → GitHub → `git pull` on the
cluster), gets a compute node — never the login node — and runs the tests
there. Before any job is submitted, it shows you the exact `sbatch`/`srun`
command and waits for your OK.

**"Get me a GPU node on chimera."**
It drafts a Slurm job on the lab's free `zhoulab_gpu_priority` partition,
asks what resources you want (CPUs, memory, GPUs, time), and shows the
command before submitting.

**"Start Jupyter Lab on the cluster and open it on my laptop."**
The [lab-jupyter](skills/lab-jupyter.md) flow: it first checks whether you
already have a Jupyter job running (and reuses it), otherwise submits one
with your approval, then opens an ssh tunnel and hands you a
`http://localhost:9990/lab?token=…` URL that just works in your browser.
Works on both clusters.

**"Update the ml container image on ircbc."**
The [lab-containers](skills/lab-containers.md) flow: it compares your
image's recorded digest against the registry, tells you whether an update
is actually needed, and only then pulls and rebuilds — pulling on the login
node and building in a compute job, because ircbc's compute nodes have no
internet.

**"Run this alignment on ircbc."**
It runs the command inside the right lab container (the bare OS is too old
for modern tools), in a Slurm job, with the container environment
activated.

**"/lab-compute:lab-edison what is known about …"**
The [lab-edison](skills/lab-edison.md) flow: it checks your key file
first, names the Edison agent it picked, prints your question in full,
and only then sends it. You get an answer with citations. Nothing on this
path involves a cluster.

## What the agent will ask you

- **Which cluster** — the choice depends on your task, project, and where
  the data lives, so the agent asks rather than deciding, unless the answer
  is obvious from context.
- **Job resources** — CPUs, memory, GPUs, wall time. It won't assume.
- **Confirmation before every job submission** — you always see the exact
  command first.
- **Before cancelling or deleting anything shared** — reservation jobs and
  lab container images belong to the whole group; the agent asks first.

## What the agent will refuse

- Running heavy work on a login node.
- Submitting jobs behind your back.
- Working on a machine whose `~/.ssh/config` isn't set up for the cluster
  (it points you to the [setup steps](index.md#install-in-claude-code)
  instead of asking for passwords or IP addresses).
- Retrying its way around a down VPN — it stops and tells you to check it.

## Tips

- Keep `~/.claude/compute/personal.md` filled in (Jupyter port, launch
  path, your usual job resources) and the agent stops re-asking session
  after session.
- Name the cluster in your request ("…on chimera", "…on ircbc") to skip
  the which-cluster question.
- The skills tell the agent to *read* your ssh config, never to change it —
  SSH setup stays in your hands.
