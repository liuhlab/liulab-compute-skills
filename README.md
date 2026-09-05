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
- **`lab-edison`** — the Edison research platform, which Edison Scientific
  runs: cited literature answers, precedent, molecules, and analysis of a
  dataset you upload, run through `edison-client` in a throwaway
  environment. No cluster involved. You invoke it yourself
  (`disable-model-invocation`), it refuses until your key file
  `~/.claude/compute/edison.env` is in place
  (`scripts/check-edison-config.sh`), it shows the job and the query
  before it spends, and it never transmits the key. Kosmos is a chat
  session that fans out into many tasks, and the skill will not start one
  unless you ask for that run.

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
4. Only if you use `lab-edison`: copy
   [templates/edison.env](templates/edison.env) to
   `~/.claude/compute/edison.env`, replace the placeholder with your own
   Edison key, and `chmod 600` it. It goes *beside* `personal.md`, never
   inside it — skills read `personal.md` into context. Never commit it.

## Other agentic tools (Cursor, Codex, Gemini CLI, …)

`git clone` this repo anywhere, then run the installer:

```bash
python skills/install.py --target all --user
```

That links every skill into every product's user-level skills
directory (`~/.claude/skills/`, `~/.agents/skills/`, `~/.codex/skills/`,
`~/.gemini/skills/`). Use `--target codex` for one product, `--list` to see
what would be installed, `--dry-run` to see where, and `--copy` where a
symlink won't do. Because they are links, `git pull` updates every install.
`lab-hpc` is the required base for the cluster skills; `lab-jupyter` and
`lab-containers` build on it. `lab-edison` stands alone and needs none of
them.

One caveat outside Claude Code: `lab-edison` is user-invoked via
`disable-model-invocation: true`, a Claude Code frontmatter key. Other
products ignore it and will trigger the skill like any other. It still
refuses without a key file and still shows the job before submitting.

Install at the user level, not into a project. Claude Code users should use
EITHER the plugin OR symlinks into `~/.claude/skills/` — never both (the
skills would load twice).

## Updating

```bash
claude plugin marketplace update liulab
claude plugin update lab-compute@liulab
```

(or `git pull` for clone-based installs).

## Testing

Three layers under [tests/](tests/) — see [tests/README.md](tests/README.md):

```bash
pixi run check                          # the gate: linters + tests/lint.sh, all at once, every failure reported
bash tests/lint.sh                      # static: manifests, frontmatter, naming, no-secrets sweep
bash tests/preflight.sh --live          # this machine's ssh config + login-node reachability
bash tests/eval.sh [--live] [--only <case>]  # headless claude -p behavior evals (costs tokens; --live submits a real job on arc)
```

`pixi run check` is what CI runs on every pull request. The other two layers
are local-only: one reads your ssh config, the other spends API tokens. The
no-secrets sweep's username and hostname checks only see *your* machine's ssh
config, so they stay a pre-push control — run the gate locally before you push.

## Adding a new skill

1. Create `skills/<new-skill>/SKILL.md` — frontmatter with `name` +
   `description` (open-standard core); keep the body lean and put long
   detail in `references/`. Add `disable-model-invocation: true` only when
   a skill must never load on its own, as `lab-edison` does.
2. Name things `lab-*`, not `liulab-*`. Respect the security policy above:
   no IPs, usernames, keys, or passwords — resolve per-user detail from
   `~/.ssh/config` / `~/.claude/compute/personal.md`.
3. Run `pixi run check`; bump `version` (CalVer `YYYY.M.PATCH`) in
   `.claude-plugin/plugin.json` and add a `CHANGELOG.md` entry in the same
   commit; tag that commit `v<version>`; push with `git push origin main
   --tags`. Installed machines pick it up on
   `claude plugin marketplace update liulab`.
