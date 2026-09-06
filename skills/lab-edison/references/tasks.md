# Running a task without losing it

> **Provenance** — Source: `edison-client` 0.16.1 · Checked: 2026-09-05 · Default tier: read.
> A claim at another tier is tagged `[verified]`, `[read]` or `[unverified]` where it is made.

Companion to `SKILL.md`. Read it whenever a run has to be submitted, polled, recovered, cancelled
or read back. Re-read the package the same way when this page is next touched. `jobs.md` holds the
routing table and the environment underneath, and neither is repeated here.

**`edison-cli` is what you run**, in the form `SKILL.md` gives. Each section below names its
subcommand and then the call underneath, so a response can be read and a failure understood; none
of it is typed out by hand.

## Names, ids, and what is remembered

**`--project` and `--persona` take a name or an id**, everywhere either appears. A value that
parses as a UUID is used as one; anything else is looked up. Nobody remembers a UUID, so a name
is the normal way to type these. No match is refused, and so is more than one, with every
candidate printed as `id  name`. The command never picks.

A project name is unique only *inside* a persona, so `--persona` is accepted on **every** command
that takes `--project` and is read only when the project is a name. A project name with no
persona is refused, exit 2, saying so.

Every other identifier is an id and never a name. `--session` and `--continue` are checked here:
one that is not a UUID is refused with exit 2 and nothing is sent. The `TASK_ID` argument and
`project add-task --task` go to the platform as typed, so a wrong one comes back as a 404 read
out as a sentence, and `task list` is how the right one is found.

Resolved names are remembered in `~/.claude/compute/edison-cli-names.json` — names and ids only,
never the key, and a cache that cannot be read is simply not used. **`--no-cache`** looks names
up on the platform again and refreshes what is held. It is on the seven that neither spend nor
destroy: `project create`, `project list`, `project ensure`, `project add-task`,
`kosmos status`, `kosmos tasks` and `task list`. The four that do — `task submit`, `kosmos start`,
`kosmos stop` and `project delete` — always resolve live and take no such flag, because a
remembered name pointing at an id that was deleted and made again is how the wrong project goes.

## Submit, then print the id — `task submit`

`create_task` returns as soon as the task exists, so the id outlives the shell that made it.
`run_tasks_until_done` runs the whole loop instead, blocking up to `timeout` — **2400 seconds by
default**, the one place that number is written down — and on expiry returns whatever state it
reached rather than raising. The command never calls it, and neither should you.

```bash
edison-cli task submit --job LITERATURE --query-file <file> \
  [--project ID|NAME] [--persona ID|NAME] [--data <uri>]... [--continue <task id>]
```

The query is a file so that what the user confirmed is what goes out; an absent or empty one is
refused. `TASK_ID: <id>` is the first line of output, before anything can block. A submission
whose id was never printed is a spent credit with no handle, recoverable only by the search
below.

## Poll — `task status`

```bash
edison-cli task status <task-id>   # STATUS: ... / TERMINAL: yes|no
```

Underneath: `client.get_task(task_id, lite=True)` — id, query and status only — with
`ExecutionStatus(t.status).is_terminal_state()` deciding the second line. The statuses are
`queued`, `in progress`, `fail`, `success`, `cancelled` and `truncated`; the last four are
terminal. Poll in short separate calls, sleep between them, and say it is running. Do not hold
one tool call open for the length of the run — and do not park a blocking call in a background
task, because the session that ends kills it mid-run.

## What comes back — `task fetch`

```bash
edison-cli task fetch <task-id> [--out <dir>] [--storage <id>]
```

`HAS_ANSWER:` comes first. Without `--out` the answer and the record of every file follow on
stdout. With `--out` the answer is written as `<task-id>.answer.md` and the line reads
`ANSWER_FILE:`, the notebook as `<task-id>.ipynb` under `NOTEBOOK:`, and each fetched file is
copied out of the library's temporary directory and named by a `FETCHED:` line. Then one `FILE:`
line per provenance record, with whatever identified the account stripped out. The record is
printed whole; the storage id is its `data_storage_id` field `[verified]` (also
`data_storage.id`). Read the id out of it and pass it back as `--storage`. `datasets.md` has the
calls underneath.

`get_task` picks the response class from the job name.

| Job | Class | Read |
| --- | --- | --- |
| literature, precedent, molecules | `PQATaskResponse` | `formatted_answer` — the answer with its citations — and `answer` |
| analysis | `FinchTaskResponse` | `answer`, and `notebook` (a dict of `cells` and `metadata`; write it out as `.ipynb`) |

Reaching for `formatted_answer` on an analysis run raises `AttributeError` on a run that
succeeded. `has_successful_answer` is the honest check on either: a task can reach `success`
carrying no answer. `total_cost` and `total_queries` also exist on `PQATaskResponse` and came
back `None` from a real successful run `[verified]` — do not report a cost from them.

## Recover a run whose id was lost — `task list`

```bash
edison-cli task list [-n <n>] [--project ID|NAME] [--persona ID|NAME] [--no-cache]
```

Underneath, `client.get_tasks(...)` lists your own trajectories, newest first, as raw dicts
rather than models — the job name under `crow`, the query under `task`, both printed on the
`TASK:` line. This is the way back to an orphaned run, it costs nothing, and it is worth
offering before anyone resubmits and pays twice — `[verified]`, a real lost run was recovered
this way, answer and citations intact. Match on the query text and the timestamp, then
`status` or `fetch` that id as usual.

## Making a run visible in the browser

A task submitted with no project carries none, and the platform's Projects view lists projects —
so an API run has no page there, even though it is in task history and billed like any other.
When the user will want to find a run in the browser later, give it a home. Every project on this
surface belongs to a persona, so the persona id comes first:

```bash
edison-cli persona list                                     # id, name, persona_job_name
edison-cli project ensure --name <name> --persona ID|NAME   # PROJECT_ID: <id>
edison-cli project add-task --project ID|NAME --task <task-id>
```

`project ensure` reuses a project of that name under that persona and creates one otherwise —
`REUSED: yes|no` says which — so re-running it is safe and does not need a getter that raises
when absent. `project create` is the same without the reuse. Neither has a persona-less form,
and `kosmos.md` says what an orphaned
project costs. `project list --persona ID|NAME` shows what a persona already owns. A *new* run
goes straight into the project with `task submit --project ID|NAME`; `add-task` is for one that
already exists.

## Delete a project — the one irreversible command

```bash
edison-cli project delete --project ID|NAME [--persona ID|NAME] \
  (--delete-tasks | --keep-tasks) --yes
```

It prints `PROJECT_ID:`, `PROJECT_NAME:`, `N_TASKS:` and `TRAJECTORIES: delete|keep` before
anything goes, and prints them on the refusal path too. Three things hold it: `--yes` is
required, and without it the summary ends `DELETED: no` at exit 2; one of `--delete-tasks` /
`--keep-tasks` is required, because the client's own default deletes the paid run history and
this command will not inherit that quietly; and the name resolves live. Without `--persona` the
name can only come off the project's own tasks, so an empty project — exactly the one somebody
is about to delete — reads `(not reachable — pass --persona to name it)`. Show the summary and
get an answer before re-running with `--yes`.

## Cancel — `task cancel`

```bash
edison-cli task cancel <task-id>   # CANCELLED: yes|no
```

`cancel_task(task_id)` returns `False` if the task is already terminal, and `True` once a
re-fetch shows `cancelled`. Reach for it the moment a wrong submission is spotted: analysis is
the long shape, and it is still charging while anyone deliberates.

## The rest of the client, briefly

`edison-cli data search --text <query>` finds entries already uploaded, so a dataset need not go
up twice (`datasets.md`). `edison-cli persona show --name <name>` — or `--id <id>`, exactly one
of the two — prints one persona, job name first. `RuntimeConfig(timeout=<seconds>)` caps how
long a run may execute.
`tags` and `project_id` on `TaskRequest` group runs that belong together. There is **no
credit-balance call anywhere in the client** — the platform's own page is the only place that
number lives.
