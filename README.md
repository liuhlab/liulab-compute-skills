# liulab-compute-skills

Private Liu Lab repo of [Agent Skills](https://agentskills.io) for the
lab's HPC/remote-compute setup, packaged as a Claude Code **plugin
marketplace** (marketplace `liulab`, plugin `lab-compute`). Other agentic
tools (Cursor, Codex, Gemini CLI, …) can consume the same skills — SKILL.md
follows the open Agent Skills standard.

Current skills:

- **`lab-hpc`** — the two lab clusters (arc/chimera GPU, ircbc CPU), the
  local → GitHub → remote workflow, Slurm usage (partitions, cost/queue
  guidance), safety rules, and a config preflight
  (`scripts/check-hpc-config.sh`) that makes agents refuse HPC requests on
  machines whose `~/.ssh/config` isn't set up.
- **`lab-jupyter`** — start or reuse a Jupyter Lab job on arc/chimera and
  tunnel it to `http://localhost:<port>` on the local machine.

## Security policy (hard rule)

This repo must **never** contain connection details or secrets of any kind:
no IP addresses or hostnames-with-addresses, no usernames, no SSH keys or key
filenames, no tokens, no passwords, no VPN credentials. Skills refer to hosts
only by the lab's conventional **ssh alias names** and resolve everything
else from each user's own `~/.ssh/config` at run time.

Setting up SSH access (hosts, keys, accounts, VPN) is **out of scope** for
this repo — get it from a lab admin through a secure channel. Keep the repo
private regardless.

## Setup — Claude Code (2 commands)

Prereqs: access to the `liuhlab` GitHub org and a logged-in `gh` (`gh auth
login`).

```bash
claude plugin marketplace add liuhlab/liulab-compute-skills
claude plugin install lab-compute@liulab
```

## Per-user config (once per machine)

1. Make sure your `~/.ssh/config` defines the lab's conventional aliases
   (`arc` / `chimera-login`, `chimera-transfer`, `chimera-gpu`, `chimera-cpu`,
   per-node compute aliases, `ircbc`, `ircbc-transfer`, `cpu01`…`cpu08`) with
   your own usernames and keys. Ask a lab member for a working example —
   this repo intentionally does not ship one.
2. Copy [templates/personal.md](templates/personal.md) to
   `~/.claude/compute/personal.md` and fill in your usernames/directories.
   Never commit it anywhere.
3. Append [templates/CLAUDE-stub.md](templates/CLAUDE-stub.md) to your
   `~/.claude/CLAUDE.md` so the two safety rules apply even in sessions where
   the skill doesn't auto-trigger.

## Other agentic tools (Cursor, Codex, Gemini CLI, …)

`git clone` this repo anywhere, then symlink `skills/lab-hpc` into the tool's
skills directory. Claude Code users should use EITHER the plugin OR a symlink
into `~/.claude/skills/` — never both (the skill would load twice).

## Updating

```bash
claude plugin marketplace update liulab
```

(or `git pull` for clone-based installs). Background auto-update of private
marketplaces would require a `GITHUB_TOKEN` env var; we deliberately don't
set one — update manually.

## Testing

Three layers under [tests/](tests/) — see [tests/README.md](tests/README.md):

```bash
bash tests/lint.sh              # static: manifests, frontmatter, naming, no-secrets sweep
bash tests/preflight.sh --live  # this machine's ssh config + login-node reachability
bash tests/eval.sh --live       # headless claude -p behavior evals (tokens; --live hits the cluster)
```

## Adding a new skill

1. Create `skills/<new-skill>/SKILL.md` — frontmatter with `name` +
   `description` only (open-standard core); keep the body lean and put long
   detail in `references/`.
2. Name things `lab-*`, not `liulab-*`. Respect the security policy above:
   no IPs, usernames, keys, or passwords — resolve per-user detail from
   `~/.ssh/config` / `~/.claude/compute/personal.md`.
3. Bump `version` in `.claude-plugin/plugin.json` and push. Installed
   machines pick it up on `claude plugin marketplace update liulab`.
