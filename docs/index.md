# Liu Lab Compute Skills

A set of [Agent Skills](https://agentskills.io) that teach AI coding
agents — Claude Code first, but any skill-aware tool — how to use the Liu
Lab's HPC clusters correctly and safely.

## What is this for?

When you ask an AI agent to "run this on the cluster" or "start Jupyter on
a GPU node", it needs lab-specific knowledge it can't guess: which clusters
exist, how jobs are submitted, what is safe to do. This plugin packages
that knowledge as three skills that load automatically when your request
touches remote compute:

| Skill | What it covers |
|---|---|
| [lab-hpc](skills/lab-hpc.md) | The foundation: the two clusters (arc/chimera GPU, ircbc CPU), Slurm usage, safety rules, per-machine setup checks. |
| [lab-jupyter](skills/lab-jupyter.md) | Jupyter Lab on a cluster compute node, tunneled to your local browser. |
| [lab-containers](skills/lab-containers.md) | The lab's Singularity container images on ircbc: keep them updated and run work inside them. |

The skills come with guardrails baked in. An agent using them will:

- **never run compute on a login node** — it gets a Slurm job first;
- **never submit a job without showing you the exact command** and getting
  your OK;
- **ask which cluster to use** (or infer it from context) instead of
  deciding for you;
- **refuse cleanly** on a machine that isn't set up, instead of improvising
  with raw addresses or passwords;
- **stop and tell you to check the VPN** when ircbc is unreachable.

!!! note "No secrets in this repo"
    The skills contain no hostnames, IP addresses, usernames, or keys.
    Hosts are referred to only by ssh alias names; everything else resolves
    from *your* `~/.ssh/config` at run time. That is why this repo can be
    public.

## Install in Claude Code

```bash
claude plugin marketplace add liuhlab/liulab-compute-skills
claude plugin install lab-compute@liulab
```

Then set up your machine once:

1. **SSH aliases** — make sure your `~/.ssh/config` defines the lab's
   conventional aliases (`arc` / `chimera-login`, `chimera-transfer`,
   `chimera-gpu`, `chimera-cpu`, per-node aliases, `ircbc`,
   `ircbc-transfer`, `cpu01`…`cpu08`) with your own usernames and keys.
   Ask a lab member for a working example — this repo intentionally does
   not ship one.
2. **Personal config** — copy
   [`templates/personal.md`](https://github.com/liuhlab/liulab-compute-skills/blob/main/templates/personal.md)
   to `~/.claude/compute/personal.md` and fill in your usernames,
   directories, and Jupyter defaults. Never commit it anywhere.
3. **Safety stub (optional)** — append
   [`templates/CLAUDE-stub.md`](https://github.com/liuhlab/liulab-compute-skills/blob/main/templates/CLAUDE-stub.md)
   to your `~/.claude/CLAUDE.md` so the core safety rules apply even in
   sessions where no skill triggers.

To check the setup, just ask Claude: *"Am I set up for the lab HPC
clusters?"* — the skill runs its preflight and reports per cluster.

## Install in other agents (Cursor, Codex, Gemini CLI, …)

The skills follow the open Agent Skills standard: `git clone` this repo
anywhere, then symlink each skill directory (`skills/lab-hpc`,
`skills/lab-jupyter`, `skills/lab-containers`) into the tool's skills
directory. `lab-hpc` is the required base; the other two build on it.

Claude Code users should use **either** the plugin **or** symlinks — never
both, or the skills load twice.

## Updating

```bash
claude plugin marketplace update liulab
claude plugin update lab-compute@liulab
```

(For clone-based installs: `git pull`.)
