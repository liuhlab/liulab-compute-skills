# Testing this skill repo

Skills are prose that steers an agent, so they are tested at three layers of
increasing cost. Run layer 1 on every change, layer 2 when setting up a machine,
and layer 3 only when a skill's behaviour has changed. One skill also ships real
code, and that has unit tests of its own, described first.

`pixi run check` runs everything cheap and safe: the static linters, the unit
tests and layer 1, all started at once, every failure reported in one run.
`.github/workflows/ci.yml` runs the same tasks on every pull request. **Only the
unit tests and layer 1 run in CI** — the other two are local-only, for the reasons
below.

## Unit tests — the Edison spend path: `tests/edison_cli/`

Free, seconds. `pixi run test`, and a step of `check-static`. Tests the **code**:
`src/edison_cli`, which is the only Python in this repo that can spend a lab
member's money.

They have their own directory because the rest of `tests/` is bash and costs
something. Every one of them answers from a fake `edison_client` the test writes
into a temporary directory and puts first on `PYTHONPATH`, and the fixture proves
the shadowing worked before any test runs. **Nothing here can reach the
platform**, which is the point: a test of the spending path has to be safe on the
day that path is broken.

What they pin, beyond the obvious: `kosmos stop` queues the halt *before* it
cancels anything, because reversing those two makes the run dispatch replacements
faster than the sweep can cancel them; the preflight module runs with neither the
client nor typer installed; the key reaches the client through the environment,
did arrive, and appears in no argument, no output and no file under `src/`; and
`project delete` removes nothing without `--yes` and a stated disposition for the
run history.

## Layer 1 — static lint: `tests/lint.sh`

Free, seconds. Tests the **files**: manifests are valid JSON, every skill has
parseable `name`/`description` front matter, names follow the `lab-*` policy, each
description fits the per-skill listing limit, and a tagged version still names the
tree it was tagged on. It also self-tests the two preflights, the eval guard, and
the eval assertions (below).

The Edison preflight is a Python module, `src/edison_cli/preflight.py`, and this
suite runs it as a file with a bare interpreter. That is deliberate: the no-secrets
sweep reads the key-file constants from it, so it has to answer on a tree where
nothing is installed, which is why it imports only the standard library.

The heart of it is the **no-secrets sweep**: no IP literals, no key material, no
Edison key other than the shipped placeholder, and none of the usernames or dotted
host names from *your* `~/.ssh/config` anywhere in the repo. Both lists are read
from your machine at test time, so the test itself stores neither.

**In CI that sweep is half-blind, and that is expected.** The username and host
name checks read the runner's own `~/.ssh/config`, which has no lab hosts in it.
So the leak sweep is a **local pre-push control**: a green CI run is not evidence
that no username or host name reached the tree. Run `pixi run check` on a machine
with the lab ssh config before you push.

## Layer 2 — environment preflight: `tests/preflight.sh`

Free, seconds. **Local only** — it reads a real `~/.ssh/config` that a runner does
not have. Tests the **machine**, not the repo, by running the same checks the
skills run as their own step 0. Three of them: the cluster aliases, which decide
the exit code, and then two Edison checks that are reported and never decide,
because the platform is opt-in per user. The first is the key. The second is the
environment `edison-cli` runs in — whether pixi is installed and whether the
environment is built — because the Edison spend path is a Python package now and a
key on its own is no longer enough. It reports; it never builds one. With `--live`
it also opens a connection to each login node; an ircbc timeout usually means the
VPN is down.

## Layer 3 — agent evals: `tests/eval.sh`

Costs tokens. Every case is a real headless `claude -p` session, so **there is no
default run** — a bare `eval.sh` prints the case list and exits without launching
anything. Ask for what you want by name:

```bash
bash tests/eval.sh --only edison-kosmos   # one case
bash tests/eval.sh --all                  # every non-live case
bash tests/eval.sh --all --live           # plus the cluster job and one real credit
```

`--live` on its own is refused: it is a modifier, not a request. Naming a `live-*`
case turns it on by itself. Layer 3 **never runs in CI** — on a public repo,
anyone who could open a pull request could spend that budget. Cases run
concurrently, so a suite takes about as long as its slowest case.

Evals exercise the **installed** plugin, not this working tree: push and
`claude plugin update lab-compute@liulab` first, or you are testing the previous
version. If you are an agent doing this for someone, prefer `--only`, and ask
before `--all` or anything live.

| Case | What it proves |
| --- | --- |
| `trigger` | An HPC prompt that never names the skill still produces a Slurm-first plan |
| `explicit` | Invoking `lab-hpc` by name states the hard safety rules |
| `reject` | Told the preflight failed, the agent refuses instead of improvising |
| `containers` | An image rebuild surfaces crane-on-login and a docker-archive build job |
| `jupyter-ircbc` | Jupyter on ircbc plans the container path, not the arc-native one |
| `reuse-job` | With a job already held, work reuses that node instead of the login node |
| `edison-refuse` | With no key, the agent refuses and never asks for the key in chat |
| `edison-molecules` | Chemistry routes to `MOLECULES`, never to the retired job that 404s |
| `edison-kosmos` | Kosmos is explained as a fan-out chat session, and nothing is substituted for it |
| `edison-recover` | A run whose id was lost is found in task history, not bought again |
| `live-sbatch` | Really ssh to arc, submit a tiny job to a free partition, clean it up |
| `live-edison` | One real literature call comes back with citations, for one credit |

Assertions are loose key-phrase greps, because evals are non-deterministic. Most
cases carry a second, negative assertion — the thing the answer must *not* say.
`tests/lint.sh` tests those regexes for free against the synthetic transcripts in
`fixtures/eval/`, reading them from `eval.sh --dump` so it checks the assertions
that actually run. Seven cases still have no fixtures; lint names them each run.

A failure means "read the transcript in the temp directory", not necessarily "the
skill is broken".

> Note: Claude Code ships a native eval framework, `claude plugin eval`, with
> scored graders and a no-plugin baseline. As of 2026-07 it is early-access-gated.
> Once it is generally available, move these cases to it and retire `eval.sh`.
