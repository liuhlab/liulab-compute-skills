# Testing this skill repo

Skills are prose that steer an agent, so they get tested at three layers with
increasing cost. Run layer 1 on every change; layer 2 when setting up a
machine; layer 3 before tagging a release or after rewriting a skill body.

`pixi run check` is the one command that runs everything cheap and safe:
the static linters plus layer 1, all started at once, every failure reported
in a single run. `.github/workflows/ci.yml` runs the same tasks on every pull
request. **Only layer 1 runs in CI** — layers 2 and 3 are local-only, for the
reasons under each heading below.

## Layer 1 — static lint (free, seconds): `tests/lint.sh`

Tests the **artifacts**: manifests are valid JSON, every skill has parseable
`name`/`description` frontmatter, names follow the `lab-*` policy, each
description stays under the per-skill listing limit (their total is printed,
but nothing fails on it), and — most importantly — the **no-secrets sweep**:
no IP literals, no key material, and none of the usernames or dotted
HostNames from *your* local `~/.ssh/config` appear anywhere in the repo
(both are read from your machine at test time,
so the test itself stores none; single-label hostnames are unsweepable but
still forbidden by policy). Also self-tests `check-hpc-config.sh` against an
empty ssh config to prove it reports NOT CONFIGURED.

**In CI it is half-blind, and that is expected.** The manifest-JSON,
frontmatter, `lab-*` naming, description-length, IP-literal, key-material and
`check-hpc-config.sh` layers all work anywhere, so they are the reason the
suite runs on every pull request (as the `test` job, via the `skill-lint`
task). The **username and hostname sweeps read the runner's own
`~/.ssh/config`**, which has no lab hosts in it: on a runner they check about
one name and zero hostnames. So the leak sweep is a **local pre-push
control** — a green CI run is not evidence that no username or FQDN reached
the tree. Run `bash tests/lint.sh` (or `pixi run check`) on a machine with
the lab ssh config before you push.

## Layer 2 — environment preflight (free, seconds): `tests/preflight.sh`

**Local only — never runs in CI**, because it reads a real `~/.ssh/config`
that a runner does not have. Tests the **machine**, not the repo: the same
`skills/lab-hpc/scripts/check-hpc-config.sh` the skill runs as step 0.
Verifies the lab ssh aliases resolve from your `~/.ssh/config`; with
`--live` it also opens a BatchMode connection to each login node (an ircbc
timeout usually means the VPN is down).

## Layer 3 — agent evals (costs tokens; `--live` touches the cluster): `tests/eval.sh`

**Local only — never runs in CI**, because every case is a real headless
agent session that spends API tokens, and on a public repo anyone who can
open a pull request could spend that budget. Adding it to a workflow later
would be a deliberate decision, not a tidy-up. Tests the **behavior the skill
induces** in a real headless Claude Code session (`claude -p`), with
grep-able assertions on the transcript. Cases
run **concurrently** (full-suite wall time ≈ slowest case, a couple of
minutes). Each case is a full agent session, so: prefer `--only <case>` for
targeted checks, and **ask before running the full suite or `--live`** if
you're an agent doing this on someone's behalf. Evals exercise the
*installed* plugin — push + `claude plugin update` first.

1. **trigger** — an HPC prompt that never names the skill must produce a
   Slurm-first plan (plan mode, nothing executes).
2. **explicit** — `/lab-compute:lab-hpc` invocation must state the hard
   safety rules.
3. **reject** — told the preflight reported NOT CONFIGURED, the agent must
   refuse the HPC request and point at per-user setup instead of
   improvising.
4. **containers** — an image-rebuild prompt must surface the
   `lab-containers` recipe (crane pull on login node, docker-archive build
   in a compute job), not a naive `singularity pull` on a compute node.
5. **jupyter-ircbc** — a Jupyter-on-ircbc prompt must plan the container
   path (`lab-containers` SIF, `squeue -u $USER`, `compute_cpu`), not the
   arc-native flow.
6. **live e2e** (only with `--live`) — the agent must actually ssh to arc,
   submit a minimal `hostname` job to a no-cost partition
   (`quick_preemptible`), report the job id, and clean it up. This is the
   real "can Claude ssh in and submit a Slurm job" test — keep it tiny and
   self-cleaning.

Evals are non-deterministic; assertions are deliberately loose (key phrases,
not exact text). A failure means "read the transcript in the temp dir", not
necessarily "the skill is broken".

> Note: Claude Code ships a native eval framework — `claude plugin eval`
> (cases under `evals/**/case.yaml`, scored graders, no-plugin baseline
> arm). As of 2026-07 it is early-access-gated; once it's generally
> available, migrate these layer-3 cases to it and retire `eval.sh`.
