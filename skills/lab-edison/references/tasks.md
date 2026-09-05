# Running a task without losing it

> **Provenance** — Source: `edison-client` 0.16.1 · Checked: 2026-09-05 · Default tier: read.
> A claim at another tier is tagged `[verified]`, `[read]` or `[unverified]` where it is made.

Companion to `SKILL.md`'s "Never block, never lose the run". Re-read the package the same way
when this page is next touched. `jobs.md` holds the routing table and the ephemeral `uv`
invocation, and neither is repeated here.

## Submit, then print the id

`create_task` returns as soon as the task exists, so the id outlives the shell that made it.
`run_tasks_until_done` runs the whole loop instead, blocking up to `timeout` — 2400 seconds by
default — and on expiry returns whatever state it reached rather than raising. Use it only for
a run you are willing to sit through.

```python
task = TaskRequest(name=JobNames.LITERATURE, query="<the exact query you showed the user>")
task_id = client.create_task(task)
print("TASK_ID:", task_id)  # before anything can block
```

Print the id in the same command that submits it. A submission whose id was never printed is a
spent credit with no handle, recoverable only by the search below.

## Poll

```python
from edison_client.models.rest import ExecutionStatus

t = client.get_task(task_id, lite=True)  # id, query and status only
done = ExecutionStatus(t.status).is_terminal_state()
```

The statuses are `queued`, `in progress`, `fail`, `success`, `cancelled` and `truncated`; the
last four are terminal. Poll in short separate calls, sleep between them, and say it is
running. Do not hold one tool call open for the length of the run — and do not park a blocking
call in a background task, because the session that ends kills it mid-run.

## What comes back

`get_task` picks the response class from the job name.

| Job | Class | Read |
| --- | --- | --- |
| literature, precedent, molecules | `PQATaskResponse` | `formatted_answer` — the answer with its citations — and `answer` |
| analysis | `FinchTaskResponse` | `answer`, and `notebook` (a dict of `cells` and `metadata`; write it out as `.ipynb`) |

Reaching for `formatted_answer` on an analysis run raises `AttributeError` on a run that
succeeded. `has_successful_answer` is the honest check on either: a task can reach `success`
carrying no answer. `total_cost` and `total_queries` also exist on `PQATaskResponse` and came
back `None` from a real successful run `[verified]` — do not report a cost from them.

## Recover a run whose id was lost

```python
for r in client.get_tasks(limit=25):
    print(r["created_at"], r["crow"], r["status"], r["id"], r["task"][:60])
```

`get_tasks` lists your own trajectories, newest first. They are raw dicts rather than models,
and the job name is under `crow`, the query under `task`. This is the way back to an orphaned
run, it costs nothing, and it is worth offering before anyone resubmits and pays twice —
`[verified]`, a real lost run was recovered this way, answer and citations intact. Match on the
query text and the timestamp, then `get_task` that id as usual.

## Making a run visible in the browser

A task submitted through the client carries no project, and the platform's Projects view
lists projects — so an API run has no page there, even though it is in task history and
billed like any other. When the user will want to find a run in the browser later, give it
a home: `client.create_project(name="<name>")` returns an id, `TaskRequest(project_id=...)`
attaches a new run to it, and `add_task_to_project(project_id, task_id)` attaches one that
already exists.

## Cancel

`cancel_task(task_id)` returns `False` if the task is already terminal, and `True` once a
re-fetch shows `cancelled`. Reach for it the moment a wrong submission is spotted: analysis is
the long shape, and it is still charging while anyone deliberates.

## The rest of the client, briefly

`search_data_storage(text_query=...)` finds entries already uploaded, so a dataset need not go
up twice. `RuntimeConfig(timeout=<seconds>)` caps how long a run may execute. `tags` and
`project_id` on `TaskRequest` group runs that belong together. There is **no credit-balance
call anywhere in the client** — the platform's own page is the only place that number lives.
