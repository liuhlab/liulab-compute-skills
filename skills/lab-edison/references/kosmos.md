# Kosmos

> **Provenance** — Source: `edison-client` 0.16.1, the live run of 2026-09-05, a smoke test on 2026-09-06, and the vendor's Kosmos and client guides · Checked: 2026-09-06 · Default tier: read.
> A claim at another tier is tagged `[verified]`, `[read]` or `[unverified]` where it is made.

Companion to `SKILL.md`. Read it whenever a user says Kosmos.

## What Kosmos is

Not a job you submit. A **chat session on a project**, which fans the objective out into
many ordinary tasks over several rounds until it decides it is done.

The shape: a **persona** is created from a published agent — the browser's picker offers
`@FutureHouse/data-analysis-aries` — and given a name the user chooses, so "Kosmos" or
"Virtual Organism" in a sidebar is *their* label, not a platform job name. Inside a persona
come **projects**, inside a project a **conversation**, and the conversation spawns the tasks.

`[verified]` The fan-out carries three job names, none of them in `JobNames`:
`job-futurehouse-paperqa3-api`, `job-futurehouse-data-analysis-heron` and
`job-futurehouse-data-analysis-heron-data`. The last appears a minute after a `heron` task —
so the fan-out is **two levels deep**, `heron` tasks dispatching children of their own. Every
task carries the project's id. The run picks its own round width; nothing in the API caps it.

## The job name, and why it is not in `JobNames`

`[verified]` A persona carries `metadata.persona_job_name` — for this one,
**`job-futurehouse-data-analysis-aries`**, matching the agent behind the browser's picker.
It is authoritative, and free to read *before* anything is spent.
`get_session` on a running session returns the same name.

It is absent from `JobNames` because `JobNames` enumerates the **one-shot task** jobs that
`create_task` takes. Kosmos is on the **chat** surface instead.

`[read]` The vendor's client page says Kosmos is not available via the API.
That is a claim about job names: there is no `JobNames.KOSMOS`, and `create_task`
cannot start a run. The chat methods that do — `send_chat_message`, `queue_chat_message`,
`get_conversation` — are ordinary typed client surface.

## Starting a run

`SKILL.md` carries the rule: never start a run the user has not asked for in those words.
Everything a start needs is named below, which makes an accidental one easier from here than
from the browser.

`[verified]` **with the persona correction**, end to end on 2026-09-05. Three commands; only the
last one spends:

```bash
edison-cli persona list                                     # id, name, persona_job_name
edison-cli project ensure --name <name> --persona ID|NAME   # reuse-or-create; prints the id
edison-cli kosmos start --project ID|NAME --persona ID|NAME --objective-file <file>
```

Both take a name instead of an id (`tasks.md`). `[verified]` **Before the send**: `PROJECT_ID`,
the `JOB_NAME` read off the persona, `PERSONA_OWNS_PROJECT: yes`, one `DATA:` line per attached
entry. An attachment missing there means stop — nothing has been charged. It
**refuses before sending** if the persona does not own the project. **After it**: `SESSION_ID`,
runnable `STOP:` and `STATUS:` lines, last `CHAT_STATUS:` (`pending` at the start), plus
`CHAT_CLAIM_NAME:`, `CHAT_POD_NAME:` and `CHAT_LOGS_URL:` for whichever the response carried.
None of those can come first: the session id does not exist until the send returns, and the
objective echoed in between is capped at twenty lines. There is no other stop path, so keep the
`STOP:` line.

Attaching data: `kosmos start --data` (`datasets.md`).

**A persona is not optional, and the surface has no persona-less form.** `create_project`
without one returns a project no persona owns; the API accepts that happily and the chat
endpoint then answers **500**. A 500 is in the client's retryable set, so it comes back raw and
bodiless — which is why the error names no field. Nothing is created and nothing is charged.
Confirmed both ways: the persona-less project 500'd, the persona-owned one started at once.

The persona id has no route through the client: no method lists personas, and
`list_persona_owned_projects`, `create_project` and `get_project_by_name` all want the id you
are hunting for. `persona list` goes under the client to `GET /v0.1/personas` on the
authenticated httpx client it exposes as `.client`.

Ownership comes with construction: `create` and `ensure` both take `--persona`, and a run in an
orphan project never appears under the persona in the browser.

## Stopping a run

`[verified]` **There is no run-level cancel.** The only cancel anywhere is
`POST /v0.1/trajectories/{task_id}/cancel` — `cancel_task`, one task at a time. There is no
`cancel_session` and nothing on the conversation surface stops a rollout, and the orchestrator
is not itself a task: `get_task("<session id>")` is a **404**, and no trajectory carries the
`…-aries` job name. A session id is not a trajectory id.

Cancelling tasks alone loses the race — one cancel was answered a minute later by a
replacement task, and four more children after that. What halts the orchestrator is the queue
endpoint, and the order matters:

```bash
edison-cli kosmos stop --project ID|NAME --session <id> [--persona ID|NAME]
```

One command, two steps in a fixed order: queue the halt **first**, then cancel every task still
`queued` or `in progress`. The other way round the orchestrator refills them while you work.
`cancel_task` returning `False` means the task went terminal between the listing and the call —
documented behaviour, not an error, and the command reports it as such.

## Reading a run that already exists — free

None of this spends anything, and it is usually what the user wants:

```bash
edison-cli kosmos sessions [-n <n>]      # session, project, time - back from a lost id
edison-cli kosmos status --project ID|NAME --session <id> [--tail <n>]
edison-cli kosmos tasks --project ID|NAME --session <id>
edison-cli task fetch <task-id> --out <dir>                  # one task's own answer, if it has one
```

`status` prints the fan-out and the last `--tail` utterances, six by default. It and `tasks`
take `--persona` for a project name and `--no-cache` to re-list; `start` and `stop` take no
`--no-cache` — they resolve live. Both mark a line they cut with `… [+N chars cut]`; an
unmarked line is complete.

`[verified]` **A fan-out subtask normally carries no answer of its own.** `HAS_ANSWER: no`
under `STATUS: success` was all five fetched: `paperqa3-api` and `heron` children leave their
output in the transcript and in `data_entry:` deliverables. Read `kosmos status` and fetch the
entries it names.

`[verified]` **A new project arrives with a session already in it.** A `project ensure`
produced one about seven seconds later — one canned `Hello! I'm …` greeting and no tasks. It
costs nothing, but `kosmos sessions` then lists one per project, and a reader hunting a lost
run can take a greeting with no tasks under it for the run that died.

`[verified]` From the session id alone the project id, the whole fan-out and the transcript all
come back — `get_session` returns the project id as `type_id`, which is why `kosmos sessions`
prints the project beside every session. A session id on its own is a dead end: `status`,
`tasks` and `stop` all need both. Underneath: `get_conversations`, `get_session` (a **list** of
one), `get_tasks(project_id=…)`, `get_conversation`, `list_files(...)["data"]`. Several hand
back a container rather than the thing itself; the commands unwrap them.

`[verified]` **`(project not recoverable)` in a `kosmos sessions` row** means the project
could not be read at all: it was deleted, no persona owns it, or `get_session` failed. One
string, three causes. It says nothing about the other rows, which are still usable.

`[verified]` **Assistant `content` is empty on every turn.** What the browser shows lives in
`tool_calls[].function.arguments`: a `send_message` call carries the reply as `display_text`,
and each `run_cell` or `wait_for_subagents` step carries a one-line status. Read `content`
alone and a healthy run looks dead. The session also carries a job timeout and a code-cell
timeout — read them before deciding a run has hung.

## Briefing the run

The objective is the part you can improve. Vendor guidance, from
<https://docs.edisonscientific.com/guides/best-practices-for-optimizing-kosmos-workflows>, fetched
2026-09-05:

- **One well-defined objective**, with room for the run to generate hypotheses and test
  them as it goes. Not a list of separate questions.
- **Enough context to act on.** Phrase it as you would explain it to an experienced
  colleague who has just joined your team.
- **Not a fact lookup.** The answer should not be obvious after reading a few papers — a
  question like that belongs in `LITERATURE` and costs a fraction as much.

Draft it, show it, and let the user edit it before it goes in. Its dataset gets the same
treatment from the same guide: `datasets.md`.

## Cost

No figures here: the vendor's pricing page did not resolve. `[verified]`
**Billing is per task execution** — the credit ledger holds one row per task, at an amount
that differs by job, so the task count is the bill and `kosmos tasks` reads as a cost. The
persona's `budget_config` is the only ceiling visible anywhere in the API, and whether it
stops a runaway run is untested.

`[verified]` The client exposes no credits or balance call, so no number can be checked
before spending. Send the user to their credits page.
