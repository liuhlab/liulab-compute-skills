# AGENTS.md

Guidance for **any** coding agent working in this repository. `CLAUDE.md` is
a symlink to this file, so Claude Code reads the same text — edit this file,
never the symlink.

The tool-specific literals below are Claude Code's own and must **not** be
renamed for another agent: real filesystem paths (`.claude-plugin/`,
`~/.claude/compute/personal.md`, `templates/CLAUDE-stub.md`) and CLI
commands (`claude plugin …`, `claude -p …`) stay exactly as written.

## What this repo is

**Public** Liu Lab repo of Agent Skills (open standard: `SKILL.md` with
`name` + `description` frontmatter only) packaged as a Claude Code plugin
marketplace. The **repo root is the plugin** (`.claude-plugin/marketplace.json`
declares `source: "./"`): marketplace `liulab`, plugin `lab-compute`, skills
under `skills/<name>/`. One plugin holds all lab skills so they update
atomically. `docs/` + `mkdocs.yml` are a human-facing MkDocs (Material)
site, deployed to GitHub Pages by `.github/workflows/docs.yml` on pushes to
main that touch them — keep those pages concise and end-user-facing (the
SKILL.md files are for agents; the docs are for people), and remember the
security policy below applies to `docs/` too (lint sweeps it).

## Hard security policy (enforced by lint)

The repo must never contain connection details: no IP literals (only
`0.0.0.0`/`127.0.0.1` are exempt), no usernames, no hostnames/FQDNs, no key
filenames/material, no passwords. Hosts are referenced **only by the lab's
ssh alias names**; skills resolve everything per-user at run time from
`~/.ssh/config` and machine-local `~/.claude/compute/personal.md`. SSH
setup itself is out of scope for this repo. `tests/lint.sh` sweeps for
violations (it reads the local machine's ssh-config usernames and dotted
HostNames at test time to check for leaks — never hardcode either into the
test itself; single-label hostnames can't be swept but are still forbidden
by policy).

## Naming policy

Internal names are `lab-*` (`lab-compute`, `lab-hpc`, `lab-jupyter`,
`lab-containers`), never `liulab-*`. The lab identity lives only in the
repo name, the GitHub org, and the marketplace name `liulab`.

## Commands

```bash
pixi run check                          # THE GATE — run on EVERY change; what CI runs on every PR
bash tests/lint.sh                      # static checks alone (same as `pixi run skill-lint`)
bash tests/preflight.sh [--live]        # is this machine's ~/.ssh/config set up (+ ssh reachability)
bash tests/eval.sh [--live] [--only <case>]   # headless agent evals — COSTS TOKENS
```

- `pixi run check` = `check-static` (ruff, ruff format, pyright, via
  `scripts/check.sh`) + `skill-lint` (`tests/lint.sh`). The static steps start
  together and **every** failure is reported in one run, so read to the bottom.
  The step list lives in the `check-static` task in `pyproject.toml` and
  nowhere else — `.github/workflows/ci.yml` invokes the task by name, so the
  local gate and CI cannot drift. Add a step there, not in the workflow.
- `tests/preflight.sh` and `tests/eval.sh` deliberately **never run in CI**
  (one reads a real ssh config, the other spends API tokens). The no-secrets
  sweep is also half-blind in CI — its username/hostname checks read the local
  ssh config — so it stays a **local pre-push control**. See `tests/README.md`.

- Eval cases: `trigger`, `explicit`, `reject`, `containers`,
  `jupyter-ircbc`, `reuse-job`, `live-sbatch`.
  Run one with `--only <case>` (`--only live-sbatch` implies `--live`, which
  submits and cleans up a real tiny Slurm job on arc). Cases run
  concurrently. Each case is a full `claude -p` session — prefer `--only`,
  and **ask the user before running the full suite or `--live`**. Evals hit
  the *installed* plugin: push + `claude plugin update` first, or you're
  testing the previous version.
- Evals assert loose key phrases on `claude -p` transcripts; on failure read
  the transcript path printed before concluding the skill is broken. In
  `eval.sh`, the prompt must come **before** flags — variadic
  `--allowedTools` swallows a trailing prompt.
- `claude plugin eval` (native, scored) is early-access-gated; migrate
  layer-3 cases there when it becomes available (see `tests/README.md`).

## Release flow

1. Edit skills; run `pixi run check`.
2. Bump `version` in `.claude-plugin/plugin.json` and add a `CHANGELOG.md`
   entry (same commit). Versioning is **CalVer `YYYY.M.PATCH`** (e.g.
   `2026.7.0`): year, month without zero-padding (keeps semver parsers
   happy), then a counter that increments per release within the month and
   resets when the month changes.
3. Push. Installed machines pick it up via
   `claude plugin marketplace update liulab` (manual on purpose — no
   `GITHUB_TOKEN` for background auto-update of the private repo).
4. To test locally before/after: `claude plugin update lab-compute@liulab`
   (plain `install` does not upgrade in place).

## Architecture / editing skills

- **Facts vs recipes.** `lab-hpc` holds foundational *facts* (cluster truth,
  safety rules, `references/`). Task-recipe skills (`lab-jupyter`,
  `lab-containers`) hold repeatable *procedures* with their own trigger
  vocabulary; they build on `lab-hpc` and never duplicate cluster facts —
  they point at the references. New content goes: cluster fact →
  `references/`; repeatable multi-step procedure → its own `lab-*` skill;
  one-liner → a bullet in `lab-hpc`.
- **Repo-wide convention:** skills never submit sbatch/srun work on the
  user's behalf without showing the exact script and getting confirmation
  first (stated in `lab-hpc`'s hard rules; keep new recipes consistent).
- **Ownership split for Jupyter-on-ircbc** (keep it — it prevents the two
  recipes drifting): `lab-jupyter` owns the session lifecycle (reuse →
  submit → token → tunnel → cleanup, parameterized per cluster in its
  table); `lab-containers` owns the container invocations, including the
  ircbc Jupyter sbatch command. Neither duplicates the other's half.
- `skills/<name>/SKILL.md` — frontmatter description is the auto-trigger
  signal; keep it keyword-dense. The **combined** description budget across
  all skills is 1536 chars (lint tracks it). Keep bodies lean; long detail
  goes in `references/`, executable checks in `scripts/`.
- `skills/lab-hpc/` is the core skill: step 0 runs
  `scripts/check-hpc-config.sh` and must **refuse** HPC requests on
  unconfigured machines. Per-cluster truth lives in
  `references/arc-hpc.md` / `references/ircbc-hpc.md`.
- Cluster facts in references are **verified on the clusters** and dated —
  don't edit them from memory; re-verify with read-only commands on the
  login nodes. The two clusters differ sharply (arc: modern Slurm, cost/queue
  tiers; ircbc: Slurm 18.08 without `squeue --me`, no internet on compute
  nodes, SOCKS-proxy-on-login gotchas) — read the relevant reference before
  writing cluster commands.
- Behavior changes to a skill are tested with `tests/eval.sh` (agent evals),
  not just lint — lint only proves the files are well-formed.
- `templates/` holds per-user onboarding files users copy to their machines
  (`personal.md`, `CLAUDE-stub.md`); they are documentation, not loaded by
  the plugin.
