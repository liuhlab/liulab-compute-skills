# Changelog

Versions track `version` in `.claude-plugin/plugin.json`. Bump the version
and add an entry here in the same commit.

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
