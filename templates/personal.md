# My lab compute specifics

<!--
Machine-local per-user config. Copy this file to ~/.claude/compute/personal.md
and fill it in. NEVER commit it to any repo. Do NOT put IP addresses, keys, or
passwords here either — connection details belong in ~/.ssh/config only.

Agents read this FIRST, before any ssh, and it overrides the lab-hpc skill's
defaults. The most valuable line is "My standing compute job": it is what lets
an agent go straight to a compute node instead of touching a login node.
-->

## My standing compute job (fill this in first)

The lab keeps a long-lived idle job so agents have a node waiting. Recording it
here saves the agent a probe sweep, and saves the login node entirely.

- Cluster and partition (e.g. arc, `zhoulab_gpu_priority`): ...
- Its node's ssh-config alias — the alias only, never a hostname: ...
- Usual job name, so `squeue` output is recognisable: ...
- Is it mine to use? (reuse freely / ask me first / not mine — never cancel): ...

If there is no standing job, say so here. The agent will then ask before
submitting one rather than assuming a node exists.

## Accounts and paths

- arc/chimera username: `<you>`
- ircbc username: `<you>`
- arc code dir: `/large_storage/zhoulab/<you>/pkg`
- ircbc code dir: `/share/home/<you>/src`

## Jupyter

- Port (lab-jupyter default 9990): ...
- Launch command on arc — use an absolute path, since sbatch does not load
  your env manager and a non-interactive ssh does not read your login shell: ...
- My usual job resources (--cpus-per-task / --mem / --gpus / --time): ...

## Anything else agents should know about MY setup

- Reservation or sbatch notes: ...
- Preferred cluster for a given project, if the choice is usually the same: ...
- Anything that has bitten me before and should not bite an agent: ...
