# Liu Lab Compute Skills

[Agent Skills](https://agentskills.io) that teach AI coding agents how to use the
Liu Lab's HPC clusters. Built for Claude Code, and they work in any tool that
reads the open skills standard.

Ask an agent to "run this on the cluster" and it needs lab knowledge it cannot
guess: which clusters exist, how a job gets submitted, what is safe to do. This
plugin holds that knowledge, in four skills.

| Skill | What it covers |
| --- | --- |
| [lab-hpc](skills/lab-hpc.md) | The two clusters (arc/chimera GPU, ircbc CPU), Slurm, the safety rules, the per-machine setup check. |
| [lab-jupyter](skills/lab-jupyter.md) | Jupyter Lab on a compute node, tunnelled to your local browser. |
| [lab-containers](skills/lab-containers.md) | The lab's Singularity images on ircbc: keeping them current, running work inside them. |
| [lab-edison](skills/lab-edison.md) | The Edison platform: Kosmos for a whole research goal, cited literature answers and data analysis for a single question. No cluster. |

The first three load by themselves when your request touches remote compute. You
call lab-edison by name, because every run of it costs you money.

## What the agent will not do

It never runs compute on a login node, never submits a job you have not seen, and
never picks a cluster in silence. On a machine that is not set up it refuses and
points you at the setup below, rather than asking for an address or a password.
When ircbc stops answering it tells you to check the VPN instead of retrying in a
loop.

!!! note "No secrets in this repo"
    The skills hold no hostnames, addresses, usernames or keys. Hosts appear only
    as ssh alias names, and the rest is read from *your* `~/.ssh/config` at run
    time. That is what makes this repo safe to publish.

## Install in Claude Code

```bash
claude plugin marketplace add liuhlab/liulab-compute-skills
claude plugin install lab-compute@liulab
```

Then set the machine up once.

1. **SSH aliases.** Your `~/.ssh/config` needs the lab's usual alias names:
   `arc`, `chimera-login`, `chimera-transfer`, `chimera-gpu`, `chimera-cpu`, the
   per-node aliases, `ircbc`, `ircbc-transfer`, and `cpu01` through `cpu08`, each
   with your own username and key. Ask a lab member for a working example. This
   repo ships none.
2. **Personal config.** Copy
   [`templates/personal.md`](https://github.com/liuhlab/liulab-compute-skills/blob/main/templates/personal.md)
   to `~/.claude/compute/personal.md` and fill in your usernames, directories and
   Jupyter defaults. Never commit it.
3. **Safety stub, optional.** Append
   [`templates/CLAUDE-stub.md`](https://github.com/liuhlab/liulab-compute-skills/blob/main/templates/CLAUDE-stub.md)
   to your `~/.claude/CLAUDE.md`, so the core rules apply even in sessions where
   no skill loads.
4. **Edison key and pixi, only for lab-edison.** That skill needs
   [pixi](https://pixi.sh) on your PATH; no other skill here does. Then copy
   [`templates/edison.env`](https://github.com/liuhlab/liulab-compute-skills/blob/main/templates/edison.env)
   to `~/.claude/compute/edison.env`, paste your own key over the placeholder,
   and `chmod 600` it. It sits beside `personal.md`, never inside it. Never
   commit it.

To check the result, ask Claude: *"Am I set up for the lab HPC clusters?"* The
skill runs its preflight and reports per cluster.

## Install in other agents

The skills follow the open Agent Skills standard, so the same files work in
Cursor, Codex, Gemini CLI and the rest. Only the folder each product reads is
different. Clone this repo anywhere, then run the installer:

```bash
python skills/install.py --target all --user
```

That links every skill into every product's user-level skills folder
(`~/.claude/skills/`, `~/.agents/skills/`, `~/.codex/skills/`,
`~/.gemini/skills/`). Use `--target codex` for one product, `--list` to see what
would be installed, `--dry-run` to see where, and `--copy` if your setup cannot
follow a symlink. They are links, so `git pull` updates every install at once.

One thing does not port. The setting that keeps lab-edison from loading on its
own belongs to Claude Code, and other products ignore it. There the skill can
load like any other, so read its [page](skills/lab-edison.md) before you use it
elsewhere.

!!! warning "Install for your user, not for a project"
    Keep `--user`. A project install writes the links into a folder inside the
    repo, and these skills also ship as a plugin, so anyone who opened this repo
    with the plugin installed would load all of them twice. Pick either the
    plugin or the links, never both.

## Updating

```bash
claude plugin marketplace update liulab
claude plugin update lab-compute@liulab
```

For clone-based installs, `git pull`.
