# Jobs, and how to run one

> **Provenance** — Source: `edison-client` 0.16.1 · Checked: 2026-09-05 · Default tier: read.
> A claim at another tier is tagged `[verified]`, `[read]` or `[unverified]` where it is made.

Companion to `SKILL.md`'s "Choosing the job". Read it before the first submission of a session.
Re-read the package the same way when this page is next touched, and believe the package over
any vendor page. The submit / poll / recover loop is in `tasks.md`.

## Which job answers which question

Pass the `JobNames` member, never a hand-typed string. The values are given so you can recognise
one in a response's `job_name` — or under `crow`, which is what task history calls it.

| The user is asking | Member | Value |
| --- | --- | --- |
| A question the published literature can answer, with citations | `LITERATURE` | `job-futurehouse-paperqa3` |
| The same, but it needs reasoning across papers that disagree — slower and dearer | `LITERATURE_HIGH` | `job-futurehouse-paperqa3-high` |
| Has anyone done this before? Prior art for a method, a claim, a target | `PRECEDENT` | `job-futurehouse-paperqa3-precedent` |
| Chemistry — molecules, properties, synthesis | `MOLECULES` | `job-futurehouse-data-analysis-molecules` |
| Something about a dataset the user supplies | `ANALYSIS` | `job-futurehouse-data-analysis-crow-high` |

`ANALYSIS` is driven from `SKILL.md`'s dataset section and `datasets.md`; it is in the table so
the routing is complete. `DUMMY` (`job-futurehouse-dummy-env`) exercises the plumbing and does
no science. `CROW`, `FALCON`, `OWL` and `FINCH` are older spellings of four of the rows above —
use the canonical member, so the transcript and the table agree. They share their values with
the canonical members, so Python folds them into aliases and `list(JobNames)` yields **seven**
members, not eleven: a listing that looks to be missing `CROW` is complete.

## The retired chemistry job

The enum still carries `PHOENIX`, and the package's own comment on it is the whole warning:
kept for historical phoenix jobs only, **new submissions will get 404 and should use `MOLECULES`
instead**. So every chemistry request routes to `MOLECULES`. If a molecules run fails, that is an
ordinary failure — the retired name is not a fallback, and reaching for it turns one failure into
a 404.

## Running the client

PyPI only, so it runs ephemerally under `uv` and installs nothing the user maintains:

```bash
. ~/.claude/compute/edison.env
uv run --no-project --python 3.12 --with edison-client python - <<'PY'
from edison_client import EdisonClient
from edison_client.models.app import JobNames, TaskRequest

client = EdisonClient()  # reads the key from the environment
task = TaskRequest(name=JobNames.LITERATURE, query="<the exact query you showed the user>")
print("TASK_ID:", client.create_task(task))  # printed before anything can block
PY
```

Then poll — `tasks.md` has the loop, and why this is two steps and not one blocking call.

Both flags are load-bearing:

- **`--no-project`.** This repo has a `pyproject.toml` of its own. Without the flag `uv` tries to
  sync *this* project instead of an ephemeral one, so the failure lands exactly where a
  maintainer is standing.
- **`--python 3.12`.** Not cosmetic. `[verified]` Unpinned runs resolved a different interpreter
  and re-downloaded the whole dependency set a second time.

An activated pixi shell does not disturb it — `VIRTUAL_ENV` and `CONDA_PREFIX` do not leak into
the run, so nothing needs deactivating first. `pixi exec` is not an alternative: conda-forge does
not carry this package.

**The first run on a machine is slow.** The dependency set is dozens of packages, and `uv`
resolves and downloads all of them before a line of the script executes. Warn the user, or it
looks hung. Later runs come from the cache.

`EdisonClient()` takes no arguments here, and constructing it is already a network call: it
authenticates and fetches your organisations eagerly, so a bad key fails at construction rather
than at submission. The key reaches it through the environment and by no other route — never an
`api_key=` argument, never echoed, never sent to a cluster. See `SKILL.md`'s hard rules.

## Continuing a task

A follow-up rides on the previous run instead of re-establishing its context:

```python
from edison_client.models.app import RuntimeConfig

TaskRequest(
    name=JobNames.LITERATURE,
    query="<the follow-up question>",
    runtime_config=RuntimeConfig(continued_job_id="<prior task id>"),
)
```

The id is the `task_id` of the earlier run and is validated as a UUID, so keep it verbatim. The
field is `continued_job_id`; the vendor's README calls it `continued_task_id`, which `TaskRequest`
rejects outright because it forbids unknown fields. Believe the package.

## Cost

No prices here, on purpose: the platform's own billing page is the only current source, and a
figure written down in a skill goes stale silently. The shape is what you need to route by —
`LITERATURE`, `PRECEDENT` and `MOLECULES` are the ordinary tier; `LITERATURE_HIGH` and `ANALYSIS`
cost more and run longer; a batch multiplies whichever you picked. The client exposes no balance
call, so when the number matters, send the user to their platform balance.
