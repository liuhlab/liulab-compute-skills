# Kosmos

> **Provenance** — Source: `edison-client` 0.16.1, the live run of 2026-09-05, and the vendor's Kosmos guide · Checked: 2026-09-05 · Default tier: read.
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
That is the authoritative source and it is free to read *before* anything is spent.
`get_session` on a running session returns the same name.

It is absent from `JobNames` because `JobNames` enumerates the **one-shot task** jobs that
`create_task` takes. Kosmos is on the **chat** surface instead. Two API surfaces, and the
enum describes one of them.

**An earlier version of this page said Kosmos runs in the browser and nowhere else. That was
wrong**, and wrong in the direction that matters: it argued from the absence of an enum
member without checking the surface Kosmos actually uses.

## Starting a run

`SKILL.md` carries the rule: never start a run the user has not asked for in those words.
This page is where it bites — everything needed is named here, which makes an accidental
start easier from here than from the browser, not harder.

`[verified]` **with the persona correction**, end to end on 2026-09-05:

```python
c.client.get("/v0.1/personas", params={"limit": 50})  # id, name, metadata.persona_job_name
pid = c.create_project(name=..., description=..., persona_id=PERSONA)
owned = {str(p["id"]) for p in c.list_persona_owned_projects(PERSONA, limit=50)}
assert str(pid) in owned  # do this BEFORE spending
c.send_chat_message(pid, objective, job_name=JOB)  # the spend; returns the session id
```

**`persona_id` is not optional.** `create_project` without it returns a project no persona
owns; the API accepts that happily and the chat endpoint then answers **500**. A 500 is in the
client's retryable set, so it is re-raised raw instead of being wrapped, and the response body
never reaches you — which is why the error names no field. Nothing is created and nothing is
charged. Confirmed both ways: the persona-less project 500'd, the persona-owned one started at
once.

The persona id has no route through the client. No method lists personas;
`list_persona_owned_projects` and `create_project` both want the id you are hunting for, and
`get_project_by_name` will not find one either. Go under the client to `GET /v0.1/personas`
on the authenticated httpx client it already exposes as `.client`.

The ownership check is not a nicety. A run in an orphan project never appears under the
persona in the browser, and a run nobody can find is a failed run however good the answer.

Send the objective from a file, and print the project and session ids the moment they exist.

## Stopping a run

`[verified]` **There is no run-level cancel.** The only cancel anywhere is
`POST /v0.1/trajectories/{task_id}/cancel` — `cancel_task`, one task at a time. There is no
`cancel_session` and nothing on the conversation surface stops a rollout, and the orchestrator
is not itself a task: `get_task("<session id>")` is a **404**, and no trajectory carries the
`…-aries` job name. A session id is not a trajectory id.

Cancelling tasks alone loses the race — one cancel was answered a minute later by a
replacement task, and four more children after that. What halts the orchestrator is the queue
endpoint, and the order matters:

```python
c.queue_chat_message(session_id=SID, project_id=PID, message="Stop this run now. …")
for t in c.get_tasks(project_id=PID, limit=200):
    if t["status"] in {"in progress", "queued"}:
        c.cancel_task(t["id"])
```

Queue the halt **first**, then clean up what is in flight; the other way round the
orchestrator refills them while you work. `cancel_task` returning `False` means the task went
terminal between the listing and the call — its documented behaviour, not an error. A raw
traceback out of `cancel` means **the task id does not exist**; against a real running task
the shipped command is clean and silent.

## Reading a run that already exists — free

None of this spends anything, and it is usually what the user actually wants:

```python
c.get_conversations(limit=25)  # .conversations -> session ids and timestamps
c.get_session("<session_id>")[0]  # a LIST of one; .job_name and .type_id, the project id
c.get_tasks(project_id="<project_id>")  # every task the run fanned out, as raw dicts
c.get_conversation("<session_id>")  # the transcript
c.list_files("<task_id>")["data"]  # what one of those tasks produced
```

`[verified]` From the session id alone the project id, the whole fan-out and the transcript
all come back. Watch the return shapes: some of these hand back a container rather than the
thing itself, which is the mistake to make here.

`[verified]` **Assistant `content` is empty on every turn.** What the browser shows lives in
`tool_calls[].function.arguments`: a `send_message` call carries the reply as `display_text`,
and each `run_cell` or `wait_for_subagents` step carries a one-line status. Read `content`
alone and a healthy run looks dead. The session also carries a job timeout and a code-cell
timeout — read them before deciding a run has hung.

## Briefing the run

The user usually starts the run themselves. What they type into it is the part you can
improve. Vendor guidance, from
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

No figures here. The vendor's pricing page did not resolve on 2026-09-05, and the numbers in
circulation elsewhere are unconfirmed; a wrong price in a skill is worse than none. The shape
is not a multiplier: **a run is billed as the sum of the ordinary tasks it fans out to**, and
that sum grows round after round, with a second level of children the run never had to ask
for. The one run made here was still dispatching when it was deliberately stopped. The
persona's `budget_config` is the only ceiling visible anywhere in the API, and whether it
stops a runaway run is untested. Send the user to their platform balance for the real number.
