# Jobs, and how to run one

> **Provenance** — Source: `edison-client` 0.16.1 and this repo's own `pyproject.toml` · Checked: 2026-09-05 · Default tier: read.
> A claim at another tier is tagged `[verified]`, `[read]` or `[unverified]` where it is made.

Companion to `SKILL.md`, and the first page to read in a session: nothing is submitted until a
question has a job. Re-read the package the same way when this page is next touched, and believe
the package over any vendor page. The submit / poll / recover loop is in `tasks.md`.

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

`ANALYSIS` is driven from `datasets.md`; it is in the table so the routing is complete.
`DUMMY` (`job-futurehouse-dummy-env`) exercises the plumbing and does no science. `CROW`, `FALCON`, `OWL` and `FINCH` are older spellings of four of the rows above —
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

`edison-cli` runs it. `SKILL.md` carries the full invocation; every `edison-cli` line in
`references/` is short for it. Write the query the user confirmed to a file, then:

```bash
edison-cli task submit --job LITERATURE --query-file /path/to/query.txt
```

It runs the preflight, sources the key, prints `TASK_ID: <id>` as its first line and returns.
Then poll — `tasks.md` has `status` and the rest, and why this is two steps and not one
blocking call. The `--job` value is a `JobNames` member from the table above; the command
sends nothing else, so a name you invented is refused rather than submitted.

## The environment underneath

`edison-client` is a dependency of this repo's **default** pixi environment, and `edison-cli` is
a console script installed beside it. So `pixi run --manifest-path` names the plugin's own
manifest and pixi builds that environment on demand. Nothing else pins an interpreter or a
version: `pixi.lock` does both, structurally, for every platform the lab uses.

- **pixi is a prerequisite of this skill**, the way the key file is. `SKILL.md` step 0 says what
  to do when it is missing. Do not substitute `uv`, `pip` or `pixi exec`.
- **The first Edison command on a machine is slow.** The dependency set is dozens of packages and
  pixi resolves and downloads all of them before a line of the program runs. Say so, or it looks
  hung.
- **A plugin update discards the environment.** `claude plugin update` writes a fresh versioned
  directory rather than refreshing the one in place, so the build repeats once per release. It is
  much faster than the first time, because the downloads are cached, but it is not instant —
  worth a sentence to the user rather than a silent pause.
- **The environment lives in the plugin's own directory**, beside the manifest. It is not the
  user's project and not an environment they maintain, and an activated pixi shell of their own
  changes nothing, because `--manifest-path` names the manifest outright.

`EdisonClient()` takes no arguments here, and constructing it is already a network call: it
authenticates and fetches your organisations eagerly, so a bad key fails at construction rather
than at submission. The key reaches it through the environment and by no other route; `SKILL.md`'s
hard rules say what that forbids.

## Continuing a task

A follow-up rides on the previous run instead of re-establishing its context —
`task submit --continue <prior task id>`, which the command turns into
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
