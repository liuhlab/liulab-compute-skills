# Changelog

Versions track `version` in `.claude-plugin/plugin.json`. Bump the version
and add an entry here in the same commit. Versioning is CalVer
`YYYY.M.PATCH` (month unpadded; patch counts releases within the month) —
adopted at `2026.7.0`; earlier `0.x` releases predate the switch.

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
  (`lab-hpc`). Added a "Default execution target" section to `SKILL.md`:
  before running anything heavier than light Slurm control, check `squeue`
  (`--me` on arc, `-u $USER` on ircbc) for an existing idle interactive job
  and `ssh <node-alias>` onto it; create one first (with confirmation) only
  if none exists. Strengthened the #1 hard rule to name the
  `ssh arc "<command>"` anti-pattern and call out parallel agents/subagents
  as the reason it matters. Elevated the idle-reuse notes in both
  `references/arc-hpc.md` and `references/ircbc-hpc.md`, and mirrored the
  enforcement bullets in `docs/skills/lab-hpc.md`.

## 2026.7.3 — 2026-07-20

- **Clarified the #1 hard rule** in `lab-hpc` (login nodes): spelled out
  light-vs-heavy commands (login = `cd`/`ls`/git/Slurm control/small
  transfers; heavy `pixi`/builds/big downloads/training → a compute job),
  with a staging-download exception. Mirrored the wording in the
  human-facing `docs/skills/lab-hpc.md`.
- **arc network fact** (`references/arc-hpc.md`): documented that *both*
  login and compute nodes have direct internet (vs ircbc, whose compute
  nodes are offline / login goes through a SOCKS proxy) — the rule's
  exception now points at both references.
- **personal.md template:** added a prompt to record a persistent
  interactive job (partition + node alias) so agents reuse it (`ssh
  <node>`) instead of allocating a fresh job.

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

Coherence pass across the three skills (multi-agent review of the whole
repo); no cluster facts changed — only structure, routing, and decision
points.

- `lab-jupyter` restructured into one cluster-parameterized lifecycle
  (reuse → submit → token → tunnel → cleanup): a parameter table carries the
  arc/ircbc substitutions (login alias, `squeue --me` vs `squeue -u $USER`,
  partition, submit source, job-log path, tunnel target) instead of an
  arc-only procedure with an ircbc paragraph bolted on. Added the missing
  idle-reservation branch in step 1, provenance-based token lookup in step 3
  (submitted → grep the job log; reused → `server list`, arc only), and a
  safe busy-port decision list in step 4 (identify the listener before any
  kill). `<jupyter>` marked arc-only; partition cost/queue rationale now
  points at `references/arc-hpc.md` instead of restating it.
- Jupyter-on-ircbc ownership split codified (also in CLAUDE.md):
  `lab-jupyter` owns the session lifecycle; `lab-containers` owns the
  container invocations including the ircbc submit command. Removed
  `lab-containers`' duplicated tunnel line; its Jupyter block now leads with
  the lifecycle pointer so agents entering there still reuse-before-submit.
- `lab-containers` hardening: directive scope line ("ircbc only — do not
  apply to arc"); §1 says where "update" continues and where to find crane
  re-fetch; §3 warns that `sbatch --wait` blocks (don't resubmit on a
  dropped connection) and gates the digest sidecar on exit 0; §4 explains
  the two-level quoting of the `<check>` slot with an expanded example and
  gains a smoke-test-failure branch (a bad SIF otherwise looks "up to date"
  forever); interactive shell uses `-t <time>` like its siblings.
- `references/ircbc-hpc.md`: deleted the stale "typical batch job" recipe
  (it lacked the required pixi activation and contradicted `lab-containers`
  §5); the section now keeps the facts and points at "Using the images".
- `references/arc-hpc.md`: new "Submitting" H3 so the wrappers/smoke-test/
  reservation how-tos are no longer nested under "Choosing a partition";
  `mkdir -p sbatch` guard noted before the reservation script;
  idle-reservation paragraph now points at `lab-jupyter`.
- `lab-hpc`: description now includes "login node" (the term users type and
  evals assert) at no budget cost; cluster choice reframed as **the user's
  decision** — ask or infer from session context, never auto-route — with
  per-cluster factors listed and SIF work routed to `lab-containers`
  (echoed in `lab-jupyter`'s parameter step); quick-reference table slimmed
  (partition detail moved to a bullet; `ircbc-transfer`'s
  no-`/share`-mount caveat surfaced); hard-rules parenthetical covers
  chimera `CPU****` aliases; step-0 personal.md wording made precise.
- ircbc facts re-verified 2026-07-05: `$HOME` auto-binds inside the SIFs
  (noted in `lab-containers` §5) and local → `/share` uploads go directly
  through the `ircbc` login alias (recorded in `references/ircbc-hpc.md`).
- Tests: new `jupyter-ircbc` eval case (the seam this review found broken);
  `reject`/`containers` assertions tightened by dropping terms the prompt
  itself contains or a wrong plan would also emit; lint now sweeps local
  ssh-config HostNames (dotted values) like it already did usernames;
  `check-hpc-config.sh` warns (never fails) when arc per-node aliases are
  missing.
- Docs: README skill blurbs updated (lab-jupyter covers both clusters;
  lab-containers covers version checks and usage), symlink instructions
  cover all three skills, release steps mention CalVer + CHANGELOG;
  `templates/personal.md` gains the Jupyter port/launch-path/resources
  fields the skills actually read.

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

- New `lab-containers` skill: the repeatable SIF pull→build→test recipe for
  ircbc (crane pull on the login node, sbatch build from docker-archive with
  the tarball deleted after a successful build, per-env smoke tests
  mirroring the image's own build checks). The ircbc reference now holds
  facts only and points at the skill for the procedure.
- Codified the repo's organizing principle in CLAUDE.md: `lab-hpc` = facts
  (references), other `lab-*` skills = task recipes that never duplicate
  facts.
- New repo-wide hard rule in `lab-hpc`: never submit sbatch/srun work
  without showing the exact script and getting user confirmation first.
- Tests: new `containers` eval case; live-sbatch eval prompt carries
  explicit submission approval to stay compatible with the new rule.

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

- ircbc reference verified on-cluster: CentOS 7 / glibc 2.17 / Slurm 18.08;
  partitions (`compute_cpu` default with MaxNodes=2, `compute_fat`,
  `compute_gpu_2080` drained); Singularity via `module load singularity`
  (verified on login and compute nodes).
- `lab-jupyter` made cluster-aware: arc flow = `zhoulab_gpu_priority` job +
  ssh tunnel; resources (CPU/mem/GPU/time) must come from the user; the
  sbatch script is always confirmed with the user before submission; ircbc
  declared not-yet-supported.

## 0.2.0 — 2026-07-04

- Three-layer test suite under `tests/`: static lint (naming, frontmatter,
  description budget, no-secrets sweep), environment preflight, and headless
  agent evals (`claude -p`) including a live ssh+sbatch end-to-end case.
- `lab-hpc` config preflight: `scripts/check-hpc-config.sh` (ssh -G alias
  checks); skills now refuse HPC requests on unconfigured machines.
- arc reference: verified partitions/QOS and cost/queue guidance
  (`zhoulab_gpu_priority` + preemptible tiers are free — `preemptible`/
  `quick_preemptible` GPU-capable, `cpu_preemptible` CPU-only; shared `gpu`
  queues bill extra and wait long; always set `--time`).
- New `lab-jupyter` skill: Jupyter Lab job on arc + local ssh tunnel.

## 0.1.0 — 2026-07-04

- Initial release: marketplace `liulab`, plugin `lab-compute`, skill
  `lab-hpc` (cluster choice, safety rules, dev workflow, per-cluster
  references), onboarding templates (`personal.md`, `CLAUDE-stub.md`),
  README. Clean-history publish policy: no IPs, usernames, keys, or
  passwords anywhere in the repo.
