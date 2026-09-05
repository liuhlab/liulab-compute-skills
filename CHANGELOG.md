# Changelog

Versions track `version` in `.claude-plugin/plugin.json`. Bump the version
and add an entry here in the same commit. Versioning is CalVer
`YYYY.M.PATCH` (month unpadded; patch counts releases within the month) —
adopted at `2026.7.0`; earlier `0.x` releases predate the switch.

## 2026.9.0 — 2026-09-05

- **Work belongs on a compute node, not a login node.** The old rule was
  about load: no heavy work on a login node, light commands fine. That left
  `ssh arc '<cmd>'` as the normal reflex, and many agents each running
  "small" commands is what overloads a shared machine. The rule is now about
  place. There are two reasons to touch a login node, and no others: you hold
  no job yet and must submit one, or the compute node lacks what you need. On
  ircbc that means internet and `git`. On arc it means nothing at all.
- **Checked on both clusters, not recalled from memory.** The whole Slurm
  client works from a compute node on arc and ircbc alike, so job management
  never needs a login node. Two things the references claimed turned out to
  be wrong. ircbc lets you ssh to a compute node you hold no job on, so
  "reachable" is not "allowed" and working there takes CPU from the job the
  scheduler put on that node. And `git` is not installed on ircbc compute
  nodes at all.
- **Skills split into smaller files.** Five long documents became fourteen
  short ones. `lab-hpc` gained `arc-slurm.md` and `ircbc-slurm.md`;
  `lab-jupyter` and `lab-containers` gained reference folders. Each file now
  covers one thing.
- **No measurements in skill docs.** Free space, percentages, queue waits and
  timings were recorded during the cluster survey. They were true that
  afternoon and misleading after, and an agent reading them cannot tell.
  They are replaced by the guidance they stood for and the command that
  gives a live answer. `AGENTS.md` now states the rule and the line between a
  measurement and a setting an agent must type.
- **One gate command, and CI runs it.** The repo gained a pixi workspace and
  `pixi run check`, which CI now runs on every pull request. It checks
  formatting, types, shell scripts, prose and markdown structure: ruff,
  pyright, shellcheck, vale, markdownlint and a conformance check. The prose
  gates cap agent-facing pages by word count and human-facing pages by
  reading grade.
- **Repo furniture.** An MIT licence. A one-command installer in place of
  hand-made symlinks. A glossary, a set of agent conventions and five
  decision records. The docs site now builds with zensical.

## 2026.7.6 — 2026-07-21

- **Editorial concision pass (no behavior change).** Tightened the
  agent-facing text so the LLM-facing instructions are shorter and more
  consistent. The idle-interactive-job reuse guidance was stated three times
  with overlapping prose (`lab-hpc` SKILL.md hard rule + its own section,
  plus both cluster references); made SKILL.md's "Default execution target"
  the single canonical write-up and reduced the two references to brief,
  same-worded pointers. Trimmed the login-node hard rule. Aligned
  `lab-jupyter`'s cross-reference to the new "Default execution target" name.

## 2026.7.5 — 2026-07-21

- **arc needs no VPN** (`references/arc-hpc.md`): added an explicit "No VPN"
  note so agents don't misgeneralize ircbc's atrust-VPN rule to arc — a
  hanging `ssh arc` is not a VPN problem. (VPN mentions were already scoped
  to ircbc everywhere; this states the arc side positively.)

## 2026.7.4 — 2026-07-21

- **Reuse idle interactive jobs instead of `ssh <login>` for work**
  (`lab-hpc`).
  - `SKILL.md` gains a "Default execution target" section. Before running
    anything heavier than light Slurm control, check `squeue` for an idle
    interactive job that already exists — `--me` on arc, `-u $USER` on
    ircbc. If one is there, `ssh <node-alias>` onto it. Create a job, with
    confirmation, only when none exists.
  - The #1 hard rule now names the `ssh arc "<command>"` anti-pattern. It
    also says why that matters: parallel agents and subagents.
  - Both cluster references lift their idle-reuse notes, and
    `docs/skills/lab-hpc.md` mirrors the enforcement bullets.

## 2026.7.3 — 2026-07-20

- **Clarified the #1 hard rule** in `lab-hpc`, the one about login nodes. It
  now spells out which commands are light and which are heavy. Light means
  `cd`, `ls`, git, Slurm control and small transfers. Heavy means `pixi`,
  builds, big downloads and training, and all of it needs a compute job.
  Staging downloads are the exception. `docs/skills/lab-hpc.md` mirrors the
  wording for readers.
- **arc network fact** (`references/arc-hpc.md`). *Both* login and compute
  nodes have direct internet. ircbc differs: its compute nodes are offline,
  and its login node goes out through a SOCKS proxy. The rule's exception
  now points at both references.
- **personal.md template.** A new prompt records a persistent interactive
  job, with its partition and node alias. Agents reuse that job with
  `ssh <node>` rather than allocate a fresh one.

## 2026.7.2 — 2026-07-05

- **Repo is now public** (full git history swept for IPs, usernames,
  hostnames, and key material first — clean). README/CLAUDE.md reworded:
  the security policy is what makes publicness safe; install prereqs no
  longer mention org access; dropped the private-marketplace
  `GITHUB_TOKEN` note.
- **Human-facing docs site** (MkDocs Material) under `docs/` +
  `mkdocs.yml`: index (what/install/update), basic-usage page, and one
  page per skill — concise end-user prose, distinct from the agent-facing
  SKILL.md files. Deployed to GitHub Pages from the `gh-pages` branch by
  `.github/workflows/docs.yml` (`mkdocs gh-deploy`, theme pinned `<10`) on
  pushes to main touching the docs.
- `tests/lint.sh`: sweep now excludes the gitignored `site/` build output.

## 2026.7.1 — 2026-07-05

Coherence pass across the three skills, from a multi-agent review of the
whole repo. No cluster facts changed. Only structure, routing and decision
points moved.

- `lab-jupyter` is now one cluster-parameterized lifecycle: reuse → submit →
  token → tunnel → cleanup. It replaces an arc-only procedure that had an
  ircbc paragraph bolted on.
  - A parameter table carries the arc/ircbc substitutions: login alias,
    `squeue --me` vs `squeue -u $USER`, partition, submit source, job-log
    path, tunnel target.
  - Step 1 gains the idle-reservation branch it was missing.
  - Step 3 finds the token by provenance. Grep the job log if the skill
    submitted the job. Use `server list` if it reused one (arc only).
  - Step 4 gains a safe busy-port decision list. Identify the listener
    before any kill.
  - `<jupyter>` is marked arc-only. Partition cost and queue rationale now
    points at `references/arc-hpc.md` instead of restating it.
- The Jupyter-on-ircbc ownership split is codified, in CLAUDE.md too.
  `lab-jupyter` owns the session lifecycle. `lab-containers` owns the
  container invocations, including the ircbc submit command. Its duplicated
  tunnel line is gone. Its Jupyter block now leads with the lifecycle
  pointer, so agents entering there still reuse before they submit.
- `lab-containers` hardening:
  - A directive scope line: ircbc only, do not apply to arc.
  - §1 says where "update" continues, and where to find crane re-fetch.
  - §3 warns that `sbatch --wait` blocks. Do not resubmit on a dropped
    connection. The digest sidecar is now gated on exit 0.
  - §4 explains the two-level quoting of the `<check>` slot and shows a
    fuller example. It also gains a smoke-test-failure branch, because a bad
    SIF otherwise looks up to date forever.
  - The interactive shell takes `-t <time>`, like its siblings.
- `references/ircbc-hpc.md`: the stale "typical batch job" recipe is gone.
  It lacked the required pixi activation and contradicted `lab-containers`
  §5. The section keeps the facts and points at "Using the images".
- `references/arc-hpc.md`: a new "Submitting" H3 lifts the wrapper,
  smoke-test and reservation how-tos out from under "Choosing a partition".
  The `mkdir -p sbatch` guard is noted before the reservation script. The
  idle-reservation paragraph now points at `lab-jupyter`.
- `lab-hpc`:
  - The description now includes "login node", the term users type and evals
    assert, at no budget cost.
  - Cluster choice is reframed as **the user's decision**. Ask, or infer
    from session context. Never auto-route. Per-cluster factors are listed,
    and SIF work goes to `lab-containers`. `lab-jupyter`'s parameter step
    echoes this.
  - The quick-reference table is slimmer. Partition detail moved to a
    bullet, and `ircbc-transfer`'s no-`/share`-mount caveat is now visible.
  - The hard-rules parenthetical covers chimera `CPU****` aliases, and the
    step-0 personal.md wording is more precise.
- ircbc facts re-verified 2026-07-05. `$HOME` auto-binds inside the SIFs,
  as noted in `lab-containers` §5. Local → `/share` uploads go straight
  through the `ircbc` login alias, as recorded in `references/ircbc-hpc.md`.
- Tests:
  - New `jupyter-ircbc` eval case, for the seam this review found broken.
  - The `reject` and `containers` assertions drop terms the prompt itself
    contains, or that a wrong plan would also emit.
  - Lint now sweeps local ssh-config HostNames (dotted values), as it
    already did usernames.
  - `check-hpc-config.sh` warns, and never fails, when arc per-node aliases
    are missing.
- Docs:
  - README skill blurbs updated. lab-jupyter covers both clusters, and
    lab-containers covers version checks and usage.
  - Symlink instructions cover all three skills.
  - Release steps mention CalVer and this changelog.
  - `templates/personal.md` gains the Jupyter port, launch-path and
    resources fields the skills actually read.

## 2026.7.0 — 2026-07-05

- **Switched to CalVer** (`YYYY.M.PATCH`).
- `lab-containers` expanded:
  - Digest-based version checks: each SIF gets a `.sif.digest` sidecar;
    never rebuild blindly — compare against `crane digest` and ask the user
    when the remote is newer.
  - Pulls are now pinned to the checked digest.
  - New "Using the images" section (verified on-cluster): run commands,
    interactive pixi-env shells from the local PC (`bash --rcfile`
    activation; `singularity run` documented as broken under Singularity
    3.2.1), and Jupyter-in-container with the local tunnel.
- `lab-jupyter`: ircbc is now supported via the Singularity-image flow
  (points at lab-containers for the submit recipe).
- `$LIU_LAB_PACKAGES` store made group-writable with setgid dirs so all
  `lhqlab` members can add/update images; documented in the ircbc reference.
- `tests/eval.sh`: cases now run concurrently (full suite ≈ slowest case);
  added guidance to prefer `--only` and ask before full/`--live` runs; noted
  that evals exercise the installed plugin, not the working tree.

## 0.5.0 — 2026-07-05

- New `lab-containers` skill: the repeatable SIF pull → build → test recipe
  for ircbc. Crane pull runs on the login node. An sbatch job builds from
  the docker-archive, and the tarball is deleted once the build succeeds.
  Per-env smoke tests mirror the image's own build checks. The ircbc
  reference now holds facts only, and points at the skill for the procedure.
- CLAUDE.md states the repo's organizing principle. `lab-hpc` holds the
  facts, in its references. The other `lab-*` skills are task recipes, and
  they never duplicate a fact.
- New repo-wide hard rule in `lab-hpc`. Never submit sbatch or srun work
  without showing the exact script and getting the user to confirm it.
- Tests: a new `containers` eval case. The live-sbatch eval prompt now
  carries explicit submission approval, to stay compatible with the new
  rule.

## 0.4.1 — 2026-07-05

- Added `CLAUDE.md` (repo guidance for Claude Code) and this changelog.

## 0.4.0 — 2026-07-05

- First published release: repo pushed to `github.com/liuhlab/liulab-compute-skills`
  (private), marketplace installs switched from local path to GitHub.
- ircbc reference expanded with verified operational detail:
  - Network topology: no internet on compute nodes; login node reaches out
    via a SOCKS proxy tunneled from the transfer node; transfer node has
    full direct internet, ~1 TB local disk, and no `/share` mount.
  - `$LIU_LAB_PACKAGES` shared package store layout
    (`/share/lhqlab/liulab_data/packages`).
  - Offline container-image workflow: `crane pull` a docker-archive tarball
    on the login node → `singularity build` the SIF in a compute job
    (validated end to end with `liulab-runtime:ml` + a Jupyter Lab smoke
    test on a compute node).
  - Gotchas: proxy env propagates into Slurm jobs (use
    `curl --noproxy` / `unset`); Slurm 18.08 lacks `squeue --me`.

## 0.3.0 — 2026-07-04

- ircbc reference verified on the cluster. It runs CentOS 7, glibc 2.17 and
  Slurm 18.08. Its partitions are `compute_cpu`, the default, with
  MaxNodes=2; `compute_fat`; and `compute_gpu_2080`, which is drained.
  Singularity comes from `module load singularity`, verified on both login
  and compute nodes.
- `lab-jupyter` is now cluster-aware. The arc flow is a
  `zhoulab_gpu_priority` job plus an ssh tunnel. Resources — CPU, memory,
  GPU and time — must come from the user. The sbatch script is always
  confirmed with the user before it is submitted. ircbc is declared
  not-yet-supported.

## 0.2.0 — 2026-07-04

- Three-layer test suite under `tests/`. Layer 1 is static lint: naming,
  frontmatter, the description budget and the no-secrets sweep. Layer 2 is
  the environment preflight. Layer 3 is headless agent evals (`claude -p`),
  including a live ssh and sbatch case that runs end to end.
- `lab-hpc` config preflight: `scripts/check-hpc-config.sh`, which checks
  the aliases with `ssh -G`. Skills now refuse HPC requests on a machine
  that is not configured.
- arc reference: partitions and QOS verified, with cost and queue guidance.
  `zhoulab_gpu_priority` and the preemptible tiers are free. `preemptible`
  and `quick_preemptible` are GPU-capable, and `cpu_preemptible` is CPU
  only. The shared `gpu` queues bill extra and wait long. Always set
  `--time`.
- New `lab-jupyter` skill: a Jupyter Lab job on arc, plus a local ssh
  tunnel.

## 0.1.0 — 2026-07-04

- Initial release. It ships the marketplace `liulab`, the plugin
  `lab-compute` and the skill `lab-hpc`, which covers cluster choice, safety
  rules, the dev workflow and the per-cluster references. It also ships the
  onboarding templates `personal.md` and `CLAUDE-stub.md`, plus a README.
- Clean-history publish policy: no IPs, usernames, keys or passwords
  anywhere in the repo.
