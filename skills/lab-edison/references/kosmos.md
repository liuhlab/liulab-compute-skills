# Kosmos

> **Provenance** — Source: `edison-client` 0.16.1 and the vendor's Kosmos guide · Checked: 2026-09-05 · Default tier: read.
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

`[verified]` Observed 2026-09-05 on a real project: 13 trajectories, all `success`, eight
`job-futurehouse-paperqa3-api` and five `job-futurehouse-data-analysis-heron` — neither in
`JobNames`. Every one carried the project's id.

## The job name, and why it is not in `JobNames`

`[verified]` `get_session` on a Kosmos project session returns `job_name`
**`job-futurehouse-data-analysis-aries`**, matching the agent behind the persona picker. So
a Kosmos job name does exist and is readable from the API for free.

It is absent from `JobNames` because `JobNames` enumerates the **one-shot task** jobs that
`create_task` takes. Kosmos is on the **chat** surface instead —
`send_chat_message(project_id, message, job_name=...)`, with `create_project`,
`get_conversations`, `recover_chat_session` and `queue_chat_message` around it. Two API
surfaces, and the enum only describes one of them.

**An earlier version of this page said Kosmos runs in the browser and nowhere else. That
was wrong**, and it was wrong in the direction that matters: it argued from the absence of
an enum member without checking the surface Kosmos actually uses.

## The rule

`SKILL.md` carries it: never start a run the user has not asked for in those words. This page
is where it bites — the pieces to start a run are all named above, which makes an accidental
start easier from here than from the browser, not harder.

The exact chat invocation is `[unverified]`: nothing here has been run, because running it is
the charge. Treat the call shape as read from the package, not as a tested recipe, and hand the
run back to the user unless they have said to start it.

## Reading a run that already exists — free

None of this spends anything, and it is usually what the user actually wants:

```python
c.get_conversations(limit=25)  # .conversations -> session ids and timestamps
c.get_session("<session_id>")[0]  # a LIST of one; .job_name and .type_id, the project id
c.get_tasks(project_id="<project_id>")  # every task the run fanned out, as raw dicts
c.list_files("<task_id>")["data"]  # what one of those tasks produced
```

`get_tasks` is how you show someone what their Kosmos run did, and how many tasks it bought
them, without opening a browser. Watch the return shapes: two of these four hand back a
container rather than the thing itself, which is the mistake to make here.

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

No figures here. The vendor's pricing page did not resolve on 2026-09-05, and the numbers
in circulation elsewhere are unconfirmed; a wrong price in a skill is worse than none. An
earlier version of this page put a run at two orders of magnitude above a single API task.
Nothing sourced that, and the shape is not a multiplier anyway: a run is billed for each
ordinary task it fans out to, so what it costs is the sum of the tasks it actually calls and
varies with how many that is — the project counted above bought thirteen. There is no flat
per-run price. Send the user to their platform balance for the real number.
