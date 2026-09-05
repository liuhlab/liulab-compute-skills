---
name: lab-edison
description: >-
  Run FutureHouse Edison platform work from a lab machine through the `edison-client` package:
  literature search, precedent, molecules, data analysis, dataset upload, task history and
  recovering a lost run, and what to do about Kosmos. Use when the user asks to search the
  literature with Edison, submit or follow up an Edison task, check or recover a run they already
  started, upload data to the platform, or set up their Edison API key. Covers the machine-local
  key file, its preflight, and the rule that the key never reaches the conversation, a command
  line, a cluster, or a job script. User-invoked only.
disable-model-invocation: true
---

# Edison platform

FutureHouse's Edison research platform, reached from a lab machine through the `edison-client`
Python package. The key is worth more than any run it pays for and a transcript is forever, so the
rules below come before the work.

## Step 0 — before any Edison command

1. Run `bash scripts/check-edison-config.sh`. One verdict per condition, and never the key.
2. **Exit 1 → refuse the task.** Name the condition that failed, relay the fix it printed, and
   stop. Do not run the client, do not improvise around it, and do not ask for the key.
3. Exit 0 → say which source it found; `~/.claude/compute/personal.md` overrides this skill.

## The key file

`~/.claude/compute/edison.env`, mode 600. It sits **beside** `personal.md` and never inside it:
skills read `personal.md` into context, so a key written there is copied into every transcript.
Source it into the shell that runs the client: `. ~/.claude/compute/edison.env`.

The preflight prints the exact remedy when it fails — the three commands, the one variable name
the client reads, and why a key that works in the user's own terminal can still read as missing.
Relay it and offer to run those commands, then **stop**: the user pastes their own key into the
file in their own editor, and it never comes back through the conversation.

## Hard rules

- **Never transmit the key.** No scp or rsync to a cluster, never written into a job script or
  an sbatch file, never on a command line, and never as an `EdisonClient(api_key=...)` argument.
- **Never print it** — not in an echo, a debug line, a log, or a preflight. Lengths only.
- **Never ask the user to type or paste it into the conversation.** If it turns up in a message
  anyway, stop, say so, and tell them to rotate it on the platform. Pass the key by environment
  only, from the file into the process that needs it.

## Choosing the job

Route from the shape of the question — literature, high-reasoning literature, precedent, molecules,
dataset analysis. `references/jobs.md` holds the routing table, the retired chemistry job that
returns 404, and the ephemeral `uv` invocation. Read it before the first submission.

**Show before you spend.** Name the job and print the exact query, then submit — a run the user never saw is a charge they cannot audit.

**Ask, and wait for an answer**, before a high-reasoning literature run, before an analysis run,
and before any batch of more than three tasks — the expensive shapes. A single literature, precedent
or molecules run needs only the showing above.

## Never block, never lose the run

A run takes minutes, and there are two ways to spend a credit and get nothing back, both
observed: `run_tasks_until_done` blocks one tool call for up to 40 minutes, and moving that
blocking call into a background task loses it outright — the session ends, the process is killed,
and the task finishes on the platform with nobody holding its id.

So **submit, print the task id, and only then poll.** The id is the receipt for the credit and
it outlives every shell. Poll in short calls, say it is running, and never end a turn having
reported a background job id in place of a task id.

**A run is never lost, only misplaced.** `get_tasks` lists your own trajectories and costs nothing,
so offer that before anyone resubmits and pays twice. Keep every task id: a follow-up rides on the
prior run as `runtime_config.continued_job_id`, where a fresh task pays again for context the old
one already holds. `references/tasks.md` has the poll loop, that recovery search, `cancel_task`,
what each response class carries, and how to give a run a project so it shows up in the browser.

## Kosmos

**Kosmos is not a job you submit — it is a chat session on a project that fans one objective
out into many tasks.** That is why `JobNames` has no member for it: the enum lists the one-shot
jobs `create_task` takes, and Kosmos lives on the chat surface beside it, under the job name
`job-futurehouse-data-analysis-aries`. `references/kosmos.md` has the structure, the free
read-only calls, and the vendor's briefing guidance.

**Never start one without the user asking for that run, in those words.** A Kosmos run costs
roughly two orders of magnitude more than an API task, and knowing the call makes an accidental
start easy. "Ask Kosmos about X" asks you to help draft the objective, not to spend. Drafting it,
checking the dataset, and reading a run they already started are free, and usually what they meant.

## Analysing a dataset

`ANALYSIS` takes the data with the question: upload, attach the URI the upload returns, submit,
poll, fetch what the run produced. `references/datasets.md` has those calls, the collection rule
for a directory, and where the run may happen. **The default is the user's own machine**, because
a run started on a cluster needs a live
credential on a shared node, and the only machine that has to hold one is theirs. Data on arc gets
staged down first; ircbc cannot reach the platform at all. Running from arc is allowed only once
the user has installed their own key there — explain that, never do it for them.

**Confirm before submitting.** Show the exact path going up, the job, and the exact query — then ask,
and wait. The upload doubles a mistake: a wrong directory goes up before anyone notices it was wrong.
