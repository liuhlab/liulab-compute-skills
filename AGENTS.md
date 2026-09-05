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
under `skills/<name>/`. One plugin holds every lab skill
(`docs/adr/0001-repo-root-is-the-plugin.md`). `docs/` + `mkdocs.yml` are a
human-facing site built by zensical
(`docs/adr/0005-docs-site-on-zensical.md`), built on every pull request and
deployed to GitHub Pages by `.github/workflows/docs.yml` on pushes to
main — keep those pages concise and end-user-facing (the
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
pixi run docs-build                     # build the site strictly (`docs` environment)
```

- `pixi run check` = `check-static` (the static steps, via
  `scripts/check.sh`) + `skill-lint` (`tests/lint.sh`). The static steps start
  together and **every** failure is reported in one run, so read to the bottom.
  The step list lives in the `check-static` task in `pyproject.toml` and
  nowhere else — not here either, which is why this sentence does not repeat
  it. `.github/workflows/ci.yml` invokes the task by name, so the local gate
  and CI cannot drift. Add a step there, not in the workflow.
- The writing gates: vale reads language, markdownlint reads structure. The
  caps, the per-file-class sections of `.vale.ini` and how to measure against
  them are in `docs/agents/writing.md`. Read it before writing anything — this
  file is subject to one of the caps.
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
   `2026.7.0`) — `docs/adr/0004-calver-and-manual-updates.md`.
3. Tag the bump commit `v<version>` (`git tag v2026.7.7`). The tag is a
   pointer and nothing reads it — no GitHub Release; the `CHANGELOG.md`
   entry is the release notes. A version heading with no tag leaves whoever
   installed that version no commit to check out.
4. Push both: `git push origin main --tags`. Installed machines pick it up
   via `claude plugin marketplace update liulab` — manual on purpose
   (ADR 0004).
5. To test locally before/after: `claude plugin update lab-compute@liulab`
   (plain `install` does not upgrade in place).

## Architecture / editing skills

- **Facts vs recipes** (`docs/adr/0002-facts-vs-recipes.md`). New content
  goes: cluster fact → the right `references/` file below; repeatable
  multi-step procedure → its own `lab-*` skill; one-liner → a bullet in
  `lab-hpc`. A recipe never repeats a cluster fact; it points at the
  reference.
- **Repo-wide convention:** skills never submit sbatch/srun work on the
  user's behalf without showing the exact script and getting confirmation
  first (stated in `lab-hpc`'s hard rules; keep new recipes consistent).
- **Ownership split for Jupyter-on-ircbc:** `lab-jupyter` owns the session
  lifecycle; `lab-containers` owns the container invocations, including the
  ircbc Jupyter sbatch command. Neither duplicates the other's half — keep it
  that way (`docs/adr/0003-jupyter-containers-ownership-split.md`).
- `skills/<name>/SKILL.md` — frontmatter description is the auto-trigger
  signal; keep it keyword-dense. Lint fails a **single** description over
  1536 chars — the platform's per-listing cap, never a repo-wide sum; the
  total is information only. Keep bodies lean; long detail goes in
  `references/`, executable checks in `scripts/`.
- `skills/lab-hpc/` is the core skill: step 0 runs
  `scripts/check-hpc-config.sh` and must **refuse** HPC requests on
  unconfigured machines. Per-cluster truth is split two ways, and a fact
  belongs in exactly one: `arc-hpc.md` / `ircbc-hpc.md` for hosts, network,
  toolchain and storage; `arc-slurm.md` / `ircbc-slurm.md` for partitions,
  choosing one, and submitting. The recipe skills carry their own
  `references/` for detail their SKILL.md is too small to hold.
- Cluster facts in references are **verified on the clusters** and dated —
  don't edit them from memory; re-verify with read-only commands from a
  compute node, which is where the skills say to work and the only place
  several of these facts are observable at all. The two clusters differ
  sharply (arc: modern Slurm, cost/queue tiers; ircbc: Slurm 18.08 without
  `squeue --me`, no internet on compute nodes, SOCKS-proxy-on-login gotchas)
  — read the relevant reference before writing cluster commands.
- **Record configuration, never measurements.** Configuration is what an
  agent must type — partition wall limits, `MaxNodes`, `DefaultTime`, ports,
  module names, topology — and is what the dating rule above governs. A
  measurement is free space, percentages, node states, queue waits, timings,
  how many images exist: true for one afternoon, a confident lie after, and
  the agent cannot tell which. Don't record it; write the guidance it stood
  for plus the command giving a live value ("`/large_storage` fills up, check
  `df -h`", not "81% used"). A version is configuration when behavior depends
  on it (Slurm 18.08 is why ircbc needs `squeue -u $USER`), a measurement
  otherwise.
- Behavior changes to a skill are tested with `tests/eval.sh` (agent evals),
  not just lint — lint only proves the files are well-formed.
- `templates/` holds per-user onboarding files users copy to their machines
  (`personal.md`, `CLAUDE-stub.md`); they are documentation, not loaded by
  the plugin.

## Read next

| When | Read |
| --- | --- |
| Before changing anything | `CONTEXT.md`, then any `docs/adr/` record covering the area |
| Recording vocabulary or a decision | `docs/agents/domain.md` |
| Filing or working an issue | `docs/agents/issue-tracker.md` |
| Labelling someone else's issue | `docs/agents/triage-labels.md` |
| Writing anything | `docs/agents/writing.md` |
