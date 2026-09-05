---
name: lab-edison
description: >-
  Run FutureHouse Edison platform work from a lab machine through the `edison-client` package:
  literature search, data analysis, molecules, precedent, task continuation, dataset upload, and
  what to do about Kosmos. Use when the user asks to search the literature with Edison, submit or
  follow up an Edison task, upload data to the platform, or set up their Edison API key. Covers
  the machine-local key file, the preflight that checks it, and the rule that the key never
  reaches the conversation, a command line, a cluster, or a job script. User-invoked only.
disable-model-invocation: true
---

# Edison platform

FutureHouse's Edison research platform, reached from a lab machine through the `edison-client`
Python package. The key that gets you in is a credential worth more than any run it pays for,
and a transcript is forever — so the rules below come before the work.

## Step 0 — before any Edison command

1. Run `bash scripts/check-edison-config.sh`. It prints one verdict per condition, and never the
   key.
2. **Exit 1 → refuse the task.** Name the condition that failed, offer the fix below, and stop.
   Do not run the client, do not improvise around it, and do not ask for the key.
3. Exit 0 → say which source it found (environment or key file) and carry on. Read
   `~/.claude/compute/personal.md` for Edison notes; it overrides this skill.

## The key file

`~/.claude/compute/edison.env`, mode 600. It sits **beside** `personal.md` and never inside it:
skills read `personal.md` into context, so a key written there is copied into every transcript.

On an unconfigured machine, offer to create it — then hand it back to the user:

```bash
mkdir -p ~/.claude/compute
printf 'export EDISON_PLATFORM_API_KEY=PASTE-YOUR-EDISON-KEY-HERE\n' > ~/.claude/compute/edison.env
chmod 600 ~/.claude/compute/edison.env
```

Then stop. Tell the user to open that file in their own editor and replace the placeholder with
their key from the platform. Their key never comes back through the conversation.

The name is exact: `edison-client` reads `EDISON_PLATFORM_API_KEY` and nothing else, so a key
exported under any other name fails later as an authentication error rather than a missing
setting. An already-exported variable also counts as configured — but a key set in `~/.zshrc` or
`~/.bashrc` is usually invisible here, because tool calls run non-interactive shells that never
read an interactive rc. Say that plainly to a user who can see their key in their own terminal.

To use it, source the file in the same shell as the run:

```bash
. ~/.claude/compute/edison.env
```

## Hard rules

- **Never transmit the key.** No scp or rsync to a cluster, never written into a job script or
  an sbatch file, never on a command line, and never as an `EdisonClient(api_key=...)` argument.
- **Never print it** — not in an echo, a debug line, a log, or a preflight. Lengths only.
- **Never ask the user to type or paste it into the conversation.** If it turns up in a message
  anyway, stop, say so, and tell them to rotate it on the platform.
- Pass it by environment only, from the file into the process that needs it.

## Choosing the job

Route from the shape of the question — literature, high-reasoning literature, precedent,
molecules. `references/jobs.md` holds the routing table, the retired chemistry job that returns
404, the exact ephemeral `uv` invocation, and continuation. Read it before the first submission.

**Show before you spend.** Name the job and print the exact query, then submit. A run the user
never saw is a charge they cannot audit.

**Ask, and wait for an answer**, before a high-reasoning literature run, before an analysis run,
and before any batch of more than three tasks. Those are the expensive shapes. A single
literature, precedent or molecules run needs only the showing above.

**A follow-up continues the prior task.** When the user pushes on an answer you just returned,
pass that task id as `runtime_config.continued_job_id` — a fresh task pays again for context the
old one already holds. Keep the task id of every run so the next question can use it.

## Kosmos

**Kosmos runs in the browser and nowhere else.** No job name for it is published, and
`JobNames` in `edison-client` 0.16.1 carried none on 2026-09-05 while naming every other
advertised agent. Say so **before** touching the client, never route the request to a
different job to have something to run, and **never guess a job-name string** —
`references/kosmos.md` explains why a lucky guess is the expensive outcome here.

Then offer the two things that do help, because the user is about to pay for the run by
hand: draft the research objective with them, and check their dataset is in a state Kosmos
can use. `references/kosmos.md` holds the vendor's guidance on both, the cost warning, and
how to re-check the job list when this goes stale.

A Kosmos run costs far more than an API task — roughly two orders of magnitude — which is
what makes the briefing worth the care. This path calls no API and spends no credits.

## Analysing a dataset

`ANALYSIS` takes the data with the question: upload, submit with the URI the upload returns,
poll, fetch what the run produced. `references/datasets.md` has those calls, the collection rule
for a directory, and how the answer and its notebook come back.

**Where the data sits decides how the run happens, and the default is the user's own machine.**
The key is why: a run started on a cluster needs a live credential sitting on a shared node, and
the only machine that has to hold one is theirs.

- **Data here** — upload from this machine. Nothing to arrange.
- **Data on arc** — stage it down first, then upload from here, however the user already moves
  data; `skills/lab-hpc/references/arc-hpc.md` has the hosts and the transfer alias.
- **Data on ircbc** — the platform is not reachable from that cluster. Compute nodes have no
  route out, and the login node reaches the internet only through a proxy
  (`skills/lab-hpc/references/ircbc-hpc.md`). Say that and stop: do not debug the failure, do not
  hunt for a route. Stage the data down and upload from here instead.

**Running from arc is allowed only when the user has already installed their key there** — the
same key file, at the same path, created in their own arc session with the commands above.
Explain that; never do it for them. No scp, no rsync, and never a key on an ssh command line,
where anyone running `ps` on a shared node reads it. No file there means staging the data down,
not putting a credential on the cluster.

**Confirm before submitting.** Show the exact path going up, file or directory, the job, and the
exact query — then ask, and wait. This is the analysis confirmation *Choosing the job* already
requires, and the upload doubles what a mistake costs: a wrong directory is uploaded before
anyone notices it was wrong.

Report the answer and the artifacts together, and keep the task id — a follow-up continues the
run instead of uploading again.
