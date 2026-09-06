---
name: lab-edison
description: >-
  Run Edison research platform work (the platform is run by Edison Scientific) from a lab machine
  through `edison-cli`, this plugin's command around the `edison-client` package: literature
  search, precedent, molecules, data analysis, dataset upload, task history and recovering a lost
  run, and what to do about Kosmos. Use when the user asks to search the literature with Edison,
  submit or follow up an Edison task, check or recover a run they already started, upload data to
  the platform, or set up their Edison API key. Covers the machine-local key file, its preflight,
  and the rule that the key never reaches the conversation, a command line, a cluster, or a job
  script. User-invoked only.
disable-model-invocation: true
---

# Edison platform

The Edison research platform — run by Edison Scientific — reached from a lab machine through
`edison-cli`, this plugin's command around the `edison-client` package. `references/` holds the
procedures: `jobs.md` routes a question to a job and is read before the first submission,
`tasks.md` submits, polls, cancels, names things rather than remembering ids, and finds a lost
run, `datasets.md` uploads data and fetches what a run made, `kosmos.md` is Kosmos.

## Step 0 — before any Edison command

Every Edison command is `edison-cli <args>`, which this plugin's `bin/` puts on PATH under Claude
Code. Off PATH it is
`pixi run --manifest-path <plugin root>/pyproject.toml edison-cli <args>` instead. `jobs.md`
covers both and the first run's cost.

1. Run `edison-cli preflight` and relay what it prints: one verdict per condition, never the key,
   the `command:` line saying which spelling this machine takes, and on failure the tested
   remedy. It owns the key file; never restate its path, mode, placeholder or fix from here.
2. **`pixi: command not found`, or the environment will not build → refuse, and say what to run.**
   Install pixi from <https://pixi.sh>, then re-run step 0. Never fall back to `uv`, to `pip`, or
   to a hand-written client call.
3. **Exit 1 → refuse the task.** Name the condition that failed, relay the remedy, offer to run
   its commands, and stop — the user pastes their own key into the file themselves. Do not run
   the client or improvise around it.
4. Exit 0 → say which source it found; `~/.claude/compute/personal.md` overrides this skill.

## Hard rules

- **Never transmit the key.** Never copied to a cluster, never written into a job script, never
  on a command line, never an `EdisonClient(api_key=...)` argument, and never into `personal.md` —
  skills read that file into context, so a key there lands in every transcript.
- **Never print it** — not in an echo, a log, or a preflight. Lengths only.
- **Never ask the user to type or paste it into the conversation.** If it turns up in a message
  anyway, stop, say so, and tell them to rotate it on the platform. Pass it by environment only.

## Before you spend

**Show before you spend.** Name the job, write the exact query to a file, show it, then submit
that file — a run the user never saw is a charge they cannot audit.

**Ask, and wait for an answer**, before a high-reasoning literature run, before an analysis run, and
before any batch of more than three tasks — the expensive shapes. An analysis run also shows the
exact path going up: a wrong directory is uploaded before anyone notices. A single literature,
precedent or molecules run needs only the showing above.

**Never start a Kosmos run unless the user asked for that run, in those words.** One objective fans
out into many ordinary tasks and each of them is charged, so a run has no flat price to quote —
send the user to their own platform balance. "Ask Kosmos about X" asks you to help draft the
objective, not to spend; drafting it, checking the dataset and reading a run they already started
cost nothing, and are usually what they meant.

## Never lose the run

**Run everything through `edison-cli`, never a hand-written call.** `task submit` takes the query
as a file and prints the task id first; `kosmos start` prints the project id, the session id and
the runnable stop command. Each subcommand runs the preflight itself, so a skipped step 0 refuses
rather than spends. `--help` prints the rest, group by group; there is no `-h`.

**`--project` and `--persona` take a name or an id**, so nobody has to hold a UUID in their head.
A name matching nothing, or several things, is refused rather than guessed, and a project name
needs `--persona` beside it. `tasks.md` has the rest, `--no-cache` included.

**Print the task id, then poll.** It is the receipt for the credit and outlives every shell.
Never end a turn having reported a background job id in place of a task id.
