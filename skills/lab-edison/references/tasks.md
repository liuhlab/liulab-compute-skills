# Running a task without losing it

Companion to `SKILL.md`'s "Never block, never lose the run". Everything here was read off the
installed `edison-client` 0.16.1 on 2026-09-05 — re-read it the same way when this is next
touched. `jobs.md` holds the routing table, and it is not repeated here.

**`scripts/edison-task.sh` is what you run.** Each section below names its subcommand and then
the call underneath, so a response can be read and a failure understood; none of it is typed
out by hand.

## Submit, then print the id — `submit`

`create_task` returns as soon as the task exists, so the id outlives the shell that made it.
`run_tasks_until_done` runs the whole loop instead, blocking up to `timeout` — **2400 seconds by
default**, the one place that number is written down — and on expiry returns whatever state it
reached rather than raising. The command never calls it, and neither should you.

```bash
bash scripts/edison-task.sh submit --job LITERATURE --query-file <file> [--data <uri>]...
```

The query is a file so that what the user confirmed is what goes out; an absent or empty one is
refused. `TASK_ID: <id>` is the first line of output, before anything can block. A submission
whose id was never printed is a spent credit with no handle, recoverable only by the search
below.

## Poll — `status`

```bash
bash scripts/edison-task.sh status <task-id>   # STATUS: ... / TERMINAL: yes|no
```

Underneath: `client.get_task(task_id, lite=True)` — id, query and status only — with
`ExecutionStatus(t.status).is_terminal_state()` deciding the second line. The statuses are
`queued`, `in progress`, `fail`, `success`, `cancelled` and `truncated`; the last four are
terminal. Poll in short separate calls, sleep between them, and say it is running. Do not hold
one tool call open for the length of the run — and do not park a blocking call in a background
task, because the session that ends kills it mid-run.

## What comes back — `fetch`

```bash
bash scripts/edison-task.sh fetch <task-id> [--out <dir>] [--storage <id>]
```

It prints `HAS_ANSWER:`, the answer, one `FILE:` line per provenance record, and writes the
notebook and any fetched file into `--out`. Which field of a `FILE:` record carries the storage
id is not recorded anywhere, so the record is printed whole: read the id out of it and pass it
back as `--storage`. `datasets.md` has the calls underneath.

`get_task` picks the response class from the job name.

| Job | Class | Read |
| --- | --- | --- |
| literature, precedent, molecules | `PQATaskResponse` | `formatted_answer` — the answer with its citations — and `answer` |
| analysis | `FinchTaskResponse` | `answer`, and `notebook` (a dict of `cells` and `metadata`; write it out as `.ipynb`) |

Reaching for `formatted_answer` on an analysis run raises `AttributeError` on a run that
succeeded. `has_successful_answer` is the honest check on either: a task can reach `success`
carrying no answer. `total_cost` and `total_queries` also exist on `PQATaskResponse` and came
back `None` from a real successful run — do not report a cost from them.

## Recover a run whose id was lost — `list`

```bash
bash scripts/edison-task.sh list [--limit <n>] [--project <id>]
```

Underneath, `client.get_tasks(...)` lists your own trajectories, newest first, as raw dicts
rather than models — the job name under `crow`, the query under `task`, both printed on the
`TASK:` line. This is the way back to an orphaned run, it costs nothing, and it is worth
offering before anyone resubmits and pays twice. Match on the query text and the timestamp,
then `status` or `fetch` that id as usual.

## Making a run visible in the browser

A task submitted through the client carries no project, and the platform's Projects view
lists projects — so an API run has no page there, even though it is in task history and
billed like any other. When the user will want to find a run in the browser later, give it
a home: `client.create_project(name="<name>")` returns an id, `submit --project <id>` attaches
a new run to it, and `add_task_to_project(project_id, task_id)` attaches one that already
exists.

## Cancel — `cancel`

```bash
bash scripts/edison-task.sh cancel <task-id>   # CANCELLED: yes|no
```

`cancel_task(task_id)` returns `False` if the task is already terminal, and `True` once a
re-fetch shows `cancelled`. Reach for it the moment a wrong submission is spotted: analysis is
the long shape, and it is still charging while anyone deliberates.

## The rest of the client, briefly

`search_data_storage(text_query=...)` finds entries already uploaded, so a dataset need not go
up twice. `RuntimeConfig(timeout=<seconds>)` caps how long a run may execute. `tags` and
`project_id` on `TaskRequest` group runs that belong together. There is **no credit-balance
call anywhere in the client** — the platform's own page is the only place that number lives.
