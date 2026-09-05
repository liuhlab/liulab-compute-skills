# Jobs, and how to run one

Companion to `SKILL.md`'s "Choosing the job". Read it before the first submission of a session.
Everything here was read off the installed `edison-client` 0.16.1 on 2026-09-05 — re-read it the
same way when this is next touched, and believe the package over any vendor page. The submit /
poll / recover loop is in `tasks.md`.

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

## Never guess a job-name string

`TaskRequest.name` is typed `str | JobNames`, so the client sends whatever string it is handed —
the enum is a convenience list, not a whitelist. Names outside it do run: task history shows
`job-futurehouse-paperqa3-api` and `job-futurehouse-data-analysis-heron`, and neither is a member
(`kosmos.md`). So nothing rejects an invented name, and submitting is the only decisive check —
which is exactly the thing to avoid. A wrong guess teaches you that one string was wrong; a right
guess starts a run the user never asked for and bills it to them. Route from the table above, and
when no row fits, say so and ask.

## The retired chemistry job

The enum still carries `PHOENIX`, and the package's own comment on it is the whole warning:
kept for historical phoenix jobs only, **new submissions will get 404 and should use `MOLECULES`
instead**. So every chemistry request routes to `MOLECULES`. If a molecules run fails, that is an
ordinary failure — the retired name is not a fallback, and reaching for it turns one failure into
a 404.

## Running the client

`scripts/edison-task.sh` runs it. Write the query the user confirmed to a file, then:

```bash
bash scripts/edison-task.sh submit --job LITERATURE --query-file /path/to/query.txt
```

It runs the preflight, sources the key, prints `TASK_ID: <id>` as its first line and returns.
Then poll — `tasks.md` has `status` and the rest, and why this is two steps and not one
blocking call. The `--job` value is a `JobNames` member from the table above; the command
sends nothing else, so a name you invented is refused rather than submitted.

Underneath, the client is PyPI only, so it runs ephemerally under `uv` and installs nothing
the user maintains: `uv run --no-project --python 3.12 --with edison-client python -`. Both
flags are load-bearing:

- **`--no-project`.** This repo has a `pyproject.toml` of its own. Without the flag `uv` tries to
  sync *this* project instead of an ephemeral one, so the failure lands exactly where a
  maintainer is standing.
- **`--python 3.12`.** Not cosmetic. Unpinned runs resolved a different interpreter and
  re-downloaded the whole dependency set a second time.

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

A follow-up rides on the previous run instead of re-establishing its context —
`submit --continue <prior task id>`, which the command turns into
`runtime_config=RuntimeConfig(continued_job_id=...)` on the `TaskRequest`.

The id is the `task_id` of the earlier run and is validated as a UUID, so keep it verbatim. The
field is `continued_job_id`; the vendor's README calls it `continued_task_id`, which `TaskRequest`
rejects outright because it forbids unknown fields. Believe the package.

## Cost

No prices here, on purpose: the platform's own billing page is the only current source, and a
figure written down in a skill goes stale silently. The shape is what you need to route by —
`LITERATURE`, `PRECEDENT` and `MOLECULES` are the ordinary tier; `LITERATURE_HIGH` and `ANALYSIS`
cost more and run longer; a batch multiplies whichever you picked. The client exposes no balance
call, so when the number matters, send the user to their platform balance.
