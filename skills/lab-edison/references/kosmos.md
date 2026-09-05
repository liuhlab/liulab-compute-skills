# Kosmos

> **Provenance** — Source: `edison-client` 0.16.1, the live run of 2026-09-05, and the vendor's Kosmos and client guides · Checked: 2026-09-05 · Default tier: read.
> A claim at another tier is tagged `[verified]`, `[read]` or `[unverified]` where it is made.

Companion to `SKILL.md`. Read it whenever a user says Kosmos. Most of what this page is for
happens before a run starts, because a run is the expensive part.

## What Kosmos is on this platform

Not a job you submit. A **chat session on a project**, which fans the objective out into
many ordinary tasks over several rounds until it decides it is done.

The shape, as the platform presents it: a **persona** is created from a published agent —
the browser's picker offers `@FutureHouse/data-analysis-aries` — and given a name the user
chooses, so "Kosmos" or "Virtual Organism" in a sidebar is *their* label, not a platform
job name. Inside a persona come **projects**, inside a project a **conversation**, and the
conversation spawns the tasks. A project page counts them: Tasks, Generated Files, Uploads.

`[verified]` The fan-out carries three job names, none of them in `JobNames`:
`job-futurehouse-paperqa3-api`, `job-futurehouse-data-analysis-heron` and
`job-futurehouse-data-analysis-heron-data`. The last was the most numerous, and it appears a
minute after a `heron` task — so the fan-out is **two levels deep**, `heron` tasks dispatching
children of their own. Every task carries the project's id. The run picks its own round width;
nothing in the API caps it.

## The job name, and why it is not in `JobNames`

`[verified]` A persona carries `metadata.persona_job_name` — for this one,
**`job-futurehouse-data-analysis-aries`**, matching the agent behind the browser's picker.
It is the authoritative source and free to read *before* anything is spent.
`get_session` on a running session returns the same name.

It is absent from `JobNames` because `JobNames` enumerates the **one-shot task** jobs that
`create_task` takes. Kosmos is on the **chat** surface instead. Two API surfaces, and the
enum describes one of them.

`[read]` The vendor's client page says, just after that enum, that Kosmos is not available via
the API. That is a claim about job names: there is no `JobNames.KOSMOS`, and `create_task`
cannot start a run. The chat methods that do — `send_chat_message`, `queue_chat_message`,
`get_conversation` — are ordinary typed client surface. The vendor's tasks page covers tasks.

**An earlier version of this page said Kosmos runs in the browser and nowhere else. That was
wrong**, and wrong in the direction that matters: it argued from the absence of an enum
member without checking the surface Kosmos actually uses.

## Starting a run

`SKILL.md` carries the rule: never start a run the user has not asked for in those words.
This page is where it bites — everything needed is named here, which makes an accidental
start easier from here than from the browser, not harder.

`[verified]` **with the persona correction**, end to end on 2026-09-05. Three commands; only the
last one spends:

```bash
edison-cli persona list                                   # id, name, persona_job_name
edison-cli project ensure --name <name> --persona <id>    # reuse-or-create; prints the id
edison-cli kosmos start --project <id> --persona <id> --objective-file <file>
```

`kosmos start` prints the project id, the session id and the runnable `kosmos stop …` line
before anything can block. There is no other stop path, so keep it.

**A persona is not optional, and the surface has no persona-less form.** `create_project`
without one returns a project no persona owns; the API accepts that happily and the chat
endpoint then answers **500**. A 500 is in the client's retryable set, so it is re-raised raw
instead of being wrapped, and the response body never reaches you — which is why the error names
no field. Nothing is created and nothing is charged. Confirmed both ways: the persona-less
project 500'd, the persona-owned one started at once.

The persona id has no route through the client. No method lists personas;
`list_persona_owned_projects` and `create_project` both want the id you are hunting for, and
`get_project_by_name` will not find one either. `persona list` goes under the client to
`GET /v0.1/personas` on the authenticated httpx client it already exposes as `.client`.

Ownership comes with construction: `create` and `ensure` both take `--persona`. A run in an
orphan project never appears under the persona in the browser, and a run nobody can find is a
failed run.

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
edison-cli kosmos stop --project <id> --session <id>
```

One command, two steps in a fixed order: queue the halt **first**, then cancel every task still
`queued` or `in progress`. The other way round the orchestrator refills them
while you work, which is why the order is pinned by a test. `cancel_task` returning `False`
means the task went terminal between the listing and the call — its documented behaviour, not an
error, and the command reports it as such. A task id that does not exist is a 404 out of the
`get_task` that `cancel_task` does first; against a real running task the stop is clean and
silent.

## Reading a run that already exists — free

None of this spends anything, and it is usually what the user actually wants:

```bash
edison-cli kosmos sessions [--limit <n>]                 # session ids and timestamps
edison-cli kosmos status --project <id> --session <id>   # job name, and the transcript
edison-cli kosmos tasks --project <id> --session <id>    # every task the run fanned out
edison-cli task fetch <task-id> --out <dir>              # what one of those tasks produced
```

`[verified]` From the session id alone the project id, the whole fan-out and the transcript all
come back — `get_session` returns the project id as `type_id`, and `kosmos sessions` is the way
back to a session id nobody wrote down. Underneath: `get_conversations`, `get_session` (a
**list** of one), `get_tasks(project_id=…)`, `get_conversation`, `list_files(...)["data"]`.
Several hand back a container rather than the thing itself; the commands unwrap them.

`[verified]` **Assistant `content` is empty on every turn.** What the browser shows lives in
`tool_calls[].function.arguments`: a `send_message` call carries the reply as `display_text`,
and each `run_cell` or `wait_for_subagents` step carries a one-line status. Read `content`
alone and a healthy run looks dead. The session also carries a job timeout and a code-cell
timeout — read them before deciding a run has hung.

## Briefing the run

What the user types into a run is the part you can improve. Vendor guidance, from
<https://docs.edisonscientific.com/guides/best-practices-for-optimizing-kosmos-workflows>,
fetched 2026-09-05:

- **One well-defined objective**, with room for the run to generate hypotheses and test
  them as it goes. Not a list of separate questions.
- **Enough context to act on.** Phrase it as you would explain it to an experienced
  colleague who has just joined your team.
- **Not a fact lookup.** The answer should not be obvious after reading a few papers — a
  question like that belongs in `LITERATURE` and costs a fraction as much.

Draft it, show it, and let the user edit it before it goes in.

## Preparing the dataset

Same source, same date:

- Processed data of good quality, not raw files.
- Every column name intuitively labelled. Where a name cannot carry its own meaning, add a
  sheet describing what each one means.
- It does best on complex, high-dimensional data.
- Under 5GB in total, uncompressed.

## Cost

No figures here: the vendor's pricing page did not resolve on 2026-09-05 and the numbers in
circulation are unconfirmed. The shape
is not a multiplier: **a run is billed as the sum of the ordinary tasks it fans out to**, and
that sum grows round after round, with a second level of children the run never had to ask
for. The one run made here was still dispatching when it was deliberately stopped. The
persona's `budget_config` is the only ceiling visible anywhere in the API, and whether it
stops a runaway run is untested. Send the user to their platform balance for the real number.
