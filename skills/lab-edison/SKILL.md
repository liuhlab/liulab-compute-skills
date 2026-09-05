---
name: lab-edison
description: >-
  Run Edison research platform work (the platform is run by Edison Scientific) from a lab machine
  through the `edison-client` package: literature search, precedent, molecules, data analysis,
  dataset upload, task history and recovering a lost run, and what to do about Kosmos. Use when
  the user asks to search the literature with Edison, submit or follow up an Edison task, check
  or recover a run they already started, upload data to the platform, or set up their Edison API
  key. Covers the machine-local key file, its preflight, and the rule that the key never reaches
  the conversation, a command line, a cluster, or a job script. User-invoked only.
disable-model-invocation: true
---

# Edison platform

The Edison research platform — run by Edison Scientific — reached from a lab machine through the
`edison-client` Python package. The key is worth more than any run it pays for and a transcript is
forever, so the rules below come before the work. The procedures are in `references/`: `jobs.md`
routes a question to a job, `tasks.md` submits and polls and cancels and finds a run whose id was
lost, `datasets.md` uploads data and fetches what a run made, `kosmos.md` is Kosmos. Read
`jobs.md` before the first submission of a session.

## Step 0 — before any Edison command

1. Run `bash scripts/check-edison-config.sh` and relay what it prints: one verdict per condition,
   never the key, and on failure the tested remedy. It owns the key file; never restate its path,
   its mode, its placeholder or its fix from here.
2. **Exit 1 → refuse the task.** Name the condition that failed, relay the remedy, offer to run
   its commands, and stop — the user pastes their own key into the file in their own editor. Do
   not run the client and do not improvise around it.
3. Exit 0 → say which source it found; `~/.claude/compute/personal.md` overrides this skill.

## Hard rules

- **Never transmit the key.** No scp or rsync to a cluster, never written into a job script or an
  sbatch file, never on a command line, never an `EdisonClient(api_key=...)` argument, and never
  into `personal.md` — skills read that file into context, so a key there lands in every transcript.
- **Never print it** — not in an echo, a debug line, a log, or a preflight. Lengths only.
- **Never ask the user to type or paste it into the conversation.** If it turns up in a message
  anyway, stop, say so, and tell them to rotate it on the platform. Pass it by environment only,
  from the file into the process that needs it.

## Before you spend

**Show before you spend.** Name the job, write the exact query to a file, show the user that text,
then submit that file — a run the user never saw is a charge they cannot audit.

**Ask, and wait for an answer**, before a high-reasoning literature run, before an analysis run, and
before any batch of more than three tasks — the expensive shapes. An analysis run also shows the
exact path going up, because an upload doubles a mistake: a wrong directory goes up before anyone
notices. A single literature, precedent or molecules run needs only the showing above.

**Never start a Kosmos run unless the user asked for that run, in those words.** One objective fans
out into many ordinary tasks and each of them is charged, so a run has no flat price to quote —
send the user to their own platform balance. "Ask Kosmos about X" asks you to help draft the
objective, not to spend; drafting it, checking the dataset and reading a run they already started
cost nothing, and are usually what they meant.

## Never lose the run

**Run the client through `scripts/edison-task.sh`, never a hand-written call.** `submit` takes the
query as a file and prints the task id as its first line, before anything can block; `status` is
one poll. It runs the preflight itself, so a skipped step 0 refuses rather than spends. `-h`
prints the rest.

**Submit, print the task id, and only then poll.** The id is the receipt for the credit and it
outlives every shell. Never end a turn having reported a background job id in place of a task id.
