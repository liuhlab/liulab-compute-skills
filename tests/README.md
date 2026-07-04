# Testing this skill repo

Skills are prose that steer an agent, so they get tested at three layers with
increasing cost. Run layer 1 on every change; layer 2 when setting up a
machine; layer 3 before tagging a release or after rewriting a skill body.

## Layer 1 — static lint (free, seconds): `tests/lint.sh`

Tests the **artifacts**: manifests are valid JSON, every skill has parseable
`name`/`description` frontmatter, names follow the `lab-*` policy, the
combined description budget stays under Claude Code's limit, and — most
importantly — the **no-secrets sweep**: no IP literals, no key material, and
none of the usernames from *your* local `~/.ssh/config` appear anywhere in
the repo (usernames are read from your machine at test time, so the test
itself stores none). Also self-tests `check-hpc-config.sh` against an empty
ssh config to prove it reports NOT CONFIGURED.

## Layer 2 — environment preflight (free, seconds): `tests/preflight.sh`

Tests the **machine**, not the repo: the same
`skills/lab-hpc/scripts/check-hpc-config.sh` the skill runs as step 0.
Verifies the lab ssh aliases resolve from your `~/.ssh/config`; with
`--live` it also opens a BatchMode connection to each login node (an ircbc
timeout usually means the VPN is down).

## Layer 3 — agent evals (costs tokens; `--live` touches the cluster): `tests/eval.sh`

Tests the **behavior the skill induces** in a real headless Claude Code
session (`claude -p`), with grep-able assertions on the transcript:

1. **trigger** — an HPC prompt that never names the skill must produce a
   Slurm-first plan (plan mode, nothing executes).
2. **explicit** — `/lab-compute:lab-hpc` invocation must state the hard
   safety rules.
3. **reject** — told the preflight reported NOT CONFIGURED, the agent must
   refuse the HPC request and point at per-user setup instead of
   improvising.
4. **live e2e** (only with `--live`) — the agent must actually ssh to arc,
   submit a minimal `hostname` job to a no-cost partition
   (`quick_preemptible`), report the job id, and clean it up. This is the
   real "can Claude ssh in and submit a Slurm job" test — keep it tiny and
   self-cleaning.

Evals are non-deterministic; assertions are deliberately loose (key phrases,
not exact text). A failure means "read the transcript in the temp dir", not
necessarily "the skill is broken".
