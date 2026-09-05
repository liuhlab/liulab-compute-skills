# Context

The words this repo uses, and nothing else. How the clusters actually work is in
`skills/lab-hpc/references/`; why the repo is shaped the way it is is in `docs/adr/`.

## Glossary

### Agent-facing document

A document written for a machine that has to act on it: `AGENTS.md`, `CONTEXT.md`, the
pages under `docs/agents/` and `docs/adr/`, and the skill bodies. Capped in words, exempt
from the jargon and reading-grade rules, and kept out of the site navigation. Its opposite
is a human-facing page — `README.md`, `CHANGELOG.md`, and the browsable `docs/` pages —
which is checked for jargon and reading grade and carries no cap. A file is one or the
other; if you cannot tell which, it is human-facing. See `docs/agents/writing.md`.

### Agent Skill

A directory under `skills/` holding a `SKILL.md` whose frontmatter carries `name` and
`description` — the open Agent Skills standard — plus optional `references/` and
`scripts/`. The description is the trigger signal an agent matches a request against; the
body is what it reads once triggered. One skill here carries a key beyond the standard:
`lab-edison` sets `disable-model-invocation: true`, which makes it user-invoked only. That
key is Claude Code's, and other agent tools ignore it and will trigger the skill as they
would any other. See `docs/adr/0007-edison-key-file-and-never-transmit.md`.

### Alias

The name a lab host is called by in this repo: `arc`, `ircbc`, `chimera-transfer`,
`cpu01`. An alias resolves to a real hostname and username only in the user's own
`~/.ssh/config`, on their own machine, at run time. This repo never records what one
resolves to, and the no-secrets sweep fails a commit that does.

### CalVer

The versioning scheme of `.claude-plugin/plugin.json`: `YYYY.M.PATCH` — year, month with
no leading zero, then a counter that increments per release within the month and resets
when the month changes. See `docs/adr/0004-calver-and-manual-updates.md`.

### Compute node

A cluster node that runs real work, inside a Slurm job. It is reachable by ssh only while
the user holds a job on it, and it is the only correct place for anything heavier than
light Slurm control.

### Conformance rule

One named check in the conformance checker, `scripts/conformance.py`, which holds this
repo to the lab template's rules. A rule passes, fails with a list of problems, or reports
that it did not run. Rules are waived by name, never per file.

### Core skill

`lab-hpc`: the skill holding the repo's foundational cluster facts — which cluster is
which, the safety rules, and the per-cluster reference pages. Every other skill builds on
it and none repeats it. Contrast a task-recipe skill; see
`docs/adr/0002-facts-vs-recipes.md`.

### Credit

The Edison platform's unit of spend. A submitted task is charged in credits against the
balance the key belongs to, so a wasted run costs the person whose key it is. The tiers are
what a skill routes by, never the numbers: literature, precedent and molecules are the
ordinary tier; high-reasoning literature and analysis cost more and run longer; a batch
multiplies whichever was picked; a Kosmos run is in a class of its own. No figure appears
anywhere in this repo. The platform's own billing page is the only current source, and a
price written into a skill goes stale in silence — so send the user to their balance
instead of quoting one.

### Description budget

Room for the trigger text an agent reads when it decides which skill to load. Two limits
are easily confused. One skill's frontmatter `description` is capped at 1536 characters —
the platform's limit on a single entry in the skill listing — and the gate fails a
description longer than that. The other is the share of the model's context window the
listing occupies: genuinely shared, but across every skill installed on a machine rather
than the ones in this repo, so no count taken here measures it. The gate prints the total
of this repo's descriptions as information and fails nothing on it. Keeping each one
keyword-dense is still the point; that is a judgement, not a threshold.

### Digest sidecar

A file named `<image>.sif.digest` beside a built SIF, holding the registry digest the image
was built from. A version check compares it against the registry, so it is written only
after the build succeeds — an image that failed its smoke test must not have one.

### Edison

The Edison research platform, run by **Edison Scientific** — FutureHouse's commercial
spinout, which the platform transitioned to — and reached from a lab machine through the
`edison-client` Python package: cited answers over the published literature, precedent
searches, chemistry, and a data-analysis agent that runs code on a dataset the user
uploads. It is a cloud API, and the one thing this repo teaches that has no cluster in it
at all. `lab-edison` is the skill that drives it — user-invoked only, and in the same
plugin as the rest. See `docs/adr/0006-edison-one-skill-in-the-compute-plugin.md`.

This entry is the **single authority** on who runs the platform. Every other page — the
skill body, its trigger description, `README.md`, the published page — names Edison
Scientific in its own register and carries none of the lineage above, because no one
sentence passes every register's checks. The platform's own job names still read
`job-futurehouse-…` and its persona picker still offers `@FutureHouse/…`: naming residue
of the spinout, not evidence of who runs it. They are live API values, so never "correct"
one or argue from one back to a vendor. The gate fails a commit re-attributing the
platform, and exempts those strings.

### Edison key file

`~/.claude/compute/edison.env` on the user's own machine, mode 600: one exported assignment
of the variable the client reads, and nothing else. It sits beside the per-user config and
never inside it, because a skill reads that file into context and a key placed there would
land in every transcript. `templates/edison.env` is the blank copy; a filled-in one never
lands here, and the no-secrets sweep fails a commit that brings one. A skill sources the
file into the process that needs it and never transmits, prints or asks for its contents.
See `docs/adr/0007-edison-key-file-and-never-transmit.md`.

### Eval case

One named scenario in `tests/eval.sh` — `trigger`, `containers`, `reuse-job`, and the
rest. Each is a full headless agent session run against the *installed* plugin, asserting
loose key phrases on the transcript. Evals test behavior; lint only proves the files are
well-formed.

### Gate

`pixi run check`: the one command that must be green before a commit, and what CI runs on
every pull request. The steps start together and every failure is reported in one run, so
read to the bottom. A cap or rule inside the gate is a dial, not a law — raise one
deliberately, in its own commit, with the reason in the message.

### Idle interactive job

A Slurm job the user already holds that is not currently computing — usually a long-lived
Jupyter or reservation job. It is the default place to run work: reuse it before queueing
anything new, and never run work through `ssh` to a login alias.

### Kosmos

The Edison platform's heavyweight agent. Not a job you submit but a **chat session on a
project**, which fans one objective out into many ordinary tasks over several rounds. That
is why `JobNames` has no member for it — the enum lists the one-shot jobs `create_task`
takes, while Kosmos sits on the chat surface under the job name
`job-futurehouse-data-analysis-aries`. Because a run costs roughly two orders of magnitude
more than an API task, a skill never starts one unless the user asks for that run in those
words; drafting the objective, checking the dataset and reading a run that already exists
are free, and are usually what was wanted.

### liulab-runtime

The lab's environment repo: pixi environments (`default`, `ml`, `align-rna`, and others)
published as container images. On arc they run natively under pixi; on ircbc they are
pulled and built into SIFs. This repo teaches how to consume them and does not define them.

### Login node

The shared node an ssh login alias lands on. Light commands only — file browsing, Slurm
control, small transfers, non-bulk `git`. On ircbc it is also the only node with a route
out to the internet, so staging downloads belong there.

### No-secrets sweep

The part of `tests/lint.sh` that greps the whole publishable tree for connection details:
IP literals (`0.0.0.0` and `127.0.0.1` excepted), key material, an Edison key set to
anything but the shipped placeholder, and the usernames and dotted hostnames it reads out
of the local machine's `~/.ssh/config` at run time. Those last two are blind on a CI runner
that has no ssh config, which is why the sweep stays a local pre-push control.

### Partition

A named Slurm queue with its own hardware, limits and cost. `zhoulab_gpu_priority` on arc,
`compute_cpu` on ircbc; arc's preemptible partitions cost nothing and requeue.

### Per-user config

`~/.claude/compute/personal.md` on the user's own machine: their per-cluster usernames,
code directories, ports and reservation notes. A skill reads it at run time and it takes
precedence over any default in this repo. `templates/personal.md` is the blank copy; a
filled-in one never lands here. A credential never goes in it — reading it at run time
means reading it into context, which is why the Edison key file sits beside it.

### Plugin marketplace

This repo. `.claude-plugin/marketplace.json` declares `source: "./"`, so the repo root is
the plugin: marketplace `liulab`, plugin `lab-compute`, every skill inside that one plugin.
See `docs/adr/0001-repo-root-is-the-plugin.md`.

### Preflight

Step 0 of a skill: a script reporting, condition by condition, whether this machine holds
what the task needs. `lab-hpc` runs `scripts/check-hpc-config.sh`, which says per cluster
whether `~/.ssh/config` carries the aliases; `lab-edison` runs
`scripts/check-edison-config.sh`, which says whether the key file exists, is non-empty, is
no longer the placeholder and is owner-only — never the key itself. On a machine that is
not configured the skill refuses the request rather than improvising around it. Each takes
a flag naming an alternative file, so the gate can drive it against fixtures.

### Reservation job

A long-lived Slurm job a user keeps to hold a node on a reserved partition. Never cancel
one you did not start, and never cancel someone else's to make room.

### Shared package store

`$LIU_LAB_PACKAGES` on ircbc: the group-writable directory holding the lab's SIF images,
their digest sidecars, job logs and helper binaries. Everything in it is shared lab
property — never delete or overwrite another person's image without asking.

### SIF

A Singularity image file: one file holding a whole environment. On ircbc every real job
runs inside one, because the host OS is far too old to run modern binaries; on arc the same
environments run natively under pixi.

### Task-recipe skill

`lab-jupyter`, `lab-containers` and `lab-edison`: a skill holding one repeatable procedure
and its own trigger vocabulary. The first two build on the core skill and point at its
references instead of repeating a cluster fact. `lab-edison` has no cluster to defer to, so
it carries its own facts in its own `references/`. See
`docs/adr/0002-facts-vs-recipes.md`.

### Transfer node

The alias for a cluster's data-mover host — `chimera-transfer`, `ircbc-transfer`. Use it
for bulk copies instead of the login node. On ircbc it does not mount the same storage the
login node does, so a file landed there has to be copied onward.

### Waiver

A conformance rule this repo declines, recorded by rule name in `pyproject.toml` with the
reason beside it. Waivers are per rule and never per file, they do not expire, and every
conformance run prints them — so the reason is where a reader meets it.
