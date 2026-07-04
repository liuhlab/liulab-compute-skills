# liulab-compute-skills

Liu Lab's [Agent Skills](https://agentskills.io) for the lab's
HPC/remote-compute setup, packaged as a Claude Code **plugin marketplace**
(marketplace `liulab`, plugin `lab-compute`). Other agentic tools (Cursor,
Codex, Gemini CLI, …) can consume the same skills — SKILL.md follows the
open Agent Skills standard.

**Docs:** <https://liuhlab.github.io/liulab-compute-skills/> — human-readable
guide (what this is, install, usage, one page per skill).

Current skills:

- **`lab-hpc`** — the two lab clusters (arc/chimera GPU, ircbc CPU), the
  local → GitHub → remote workflow, Slurm usage (partitions, cost/queue
  guidance), safety rules, and a config preflight
  (`scripts/check-hpc-config.sh`) that makes agents refuse HPC requests on
  machines whose `~/.ssh/config` isn't set up.
- **`lab-jupyter`** — start or reuse a Jupyter Lab job on either cluster and
  tunnel it to `http://localhost:<port>` on the local machine: arc/chimera
  natively (`zhoulab_gpu_priority` job + `ssh -L`), ircbc inside the lab's
  Singularity image (via `lab-containers`).
- **`lab-containers`** — version-check, pull/build/update, and use the lab's
  Singularity images (`liulab-runtime` envs) on ircbc, where compute nodes
  have no internet: digest-sidecar update checks, crane pull on the login
  node → sbatch build from docker-archive, and running commands, pixi-env
  shells, or Jupyter inside the containers.

## Security policy (hard rule)

This repo is **public**; what makes that safe is that it must **never**
contain connection details or secrets of any kind: no IP addresses or
hostnames, no usernames, no SSH keys or key filenames, no tokens, no
passwords, no VPN credentials. Skills refer to hosts only by the lab's
conventional **ssh alias names** and resolve everything else from each
user's own `~/.ssh/config` at run time (`tests/lint.sh` enforces this).

Setting up SSH access (hosts, keys, accounts, VPN) is **out of scope** for
this repo — get it from a lab admin through a secure channel.

## Setup — Claude Code (2 commands)

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

`git clone` this repo anywhere, then symlink each skill directory
(`skills/lab-hpc`, `skills/lab-jupyter`, `skills/lab-containers`) — or the
whole `skills/` tree if the tool supports it — into the tool's skills
directory. `lab-hpc` is the required base; the other two build on it.
Claude Code users should use EITHER the plugin OR symlinks into
`~/.claude/skills/` — never both (the skills would load twice).

## Updating

```bash
claude plugin marketplace update liulab
claude plugin update lab-compute@liulab
```

(or `git pull` for clone-based installs).

## Testing

Three layers under [tests/](tests/) — see [tests/README.md](tests/README.md):

```bash
bash tests/lint.sh                      # static: manifests, frontmatter, naming, no-secrets sweep
bash tests/preflight.sh --live          # this machine's ssh config + login-node reachability
bash tests/eval.sh [--live] [--only <case>]  # headless claude -p behavior evals (costs tokens; --live submits a real job on arc)
```

## Adding a new skill

1. Create `skills/<new-skill>/SKILL.md` — frontmatter with `name` +
   `description` only (open-standard core); keep the body lean and put long
   detail in `references/`.
2. Name things `lab-*`, not `liulab-*`. Respect the security policy above:
   no IPs, usernames, keys, or passwords — resolve per-user detail from
   `~/.ssh/config` / `~/.claude/compute/personal.md`.
3. Run `bash tests/lint.sh`; bump `version` (CalVer `YYYY.M.PATCH`) in
   `.claude-plugin/plugin.json` and add a `CHANGELOG.md` entry in the same
   commit; push. Installed machines pick it up on
   `claude plugin marketplace update liulab`.
