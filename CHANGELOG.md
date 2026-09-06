# Changelog

Versions track `version` in `.claude-plugin/plugin.json`. Bump the version
and add an entry here in the same commit. Versioning is CalVer
`YYYY.M.PATCH` (month unpadded; patch counts releases within the month) —
adopted at `2026.7.0`; earlier `0.x` releases predate the switch.

## 2026.9.11 — 2026-09-06

Six things a live run of the Edison command found, and the timing figure it corrected.

### Fixed

- **The cheap test job does not exist.** The page said `DUMMY` was there to exercise the
  plumbing without doing any science. Submitting it answered 404 and made nothing. It is
  off the list of jobs the command will send, beside the retired chemistry job that fails
  the same way, and the page now says what happened and on what day. Asking for either by
  name is refused before anything is sent, and the refusal says the name is real rather
  than calling it unknown.
- **A submission that fails no longer sends you looking for an id.** When the platform
  answered 404 to a new task, the command told you to find your id again with `task list`
  — but no id had been handed out, because nothing was created. It now says so, and points
  at the job name and the ids you passed in.
- **The key-file fix-it text is runnable again.** Pointing the check at a file directly
  under `/` printed a `mkdir` command with nothing after it. It prints the folder now.
- **Deleting a project forgets its name.** The name-to-id file beside your key kept the
  deleted project, so a later command could still turn that name into an id the platform
  had thrown away — the exact mix-up the delete guards against, one command later.

### Changed

- **Two things the platform does that nothing wrote down.** Starting Kosmos also prints a
  `CHAT_STATUS:` line, and making a project creates a chat session on its own, seconds
  later, holding one canned greeting and no work. It costs nothing, but it shows up in
  `kosmos sessions`, and somebody looking for a run they lost could mistake it for one.
  Both are on the Kosmos page.
- **What has never been checked for real is written down as such.** The task id is meant
  to be the first thing a submission prints. That is proven against the test double and
  has never been seen against the platform, because the one free job turned out not to
  exist. The page says so rather than implying otherwise.
- **A timing was three times off.** The rebuild after a plugin update was called "a few
  seconds"; it measured about ten. The first-ever build is still about 22 seconds.

## 2026.9.10 — 2026-09-05

### Changed

- `lab-edison`: the Kosmos page records that billing is per task execution, confirmed
  against an account's own credit ledger, which carries one row per task at an amount
  that differs by job. The task count is the bill, so `kosmos tasks` reads as a cost.
- `lab-edison`: the page now states that the client exposes no credits or balance call.
  A number cannot be read, shown or checked before spending, so the advice to send the
  user to their own credits and activity page is the only route there is, rather than
  caution. Recorded so the next reader does not go looking for an API that is absent.

## 2026.9.9 — 2026-09-05

The code that spends your Edison credits moved out of a shell script and into a
Python package, `src/edison_cli/`. Every check this repo runs now reads it. Kosmos
gets real commands for the first time.

- **The spending code is checked like the rest of the repo.** It used to be Python
  written inside a shell script, where the linter and the type checker could not see
  it. It is a package now, so both read it, and it has its own unit tests.
- **One command, `edison-cli`, in place of two shell scripts.** `task submit`,
  `task status`, `task list`, `task fetch` and `task cancel` do what the old script
  did, with the same flags. `preflight` is the key-file check that used to be a
  script of its own.
- **Kosmos can be driven from here now.** `kosmos start`, `status`, `tasks`,
  `sessions` and `stop`, with `persona list` and `project ensure` to get the two ids
  a run needs. Starting a run prints the exact line that stops it, before anything
  else can happen. Stopping queues the halt first and cancels the leftover tasks
  second, which is the order that works.
- **You can use names instead of long ids.** Anywhere a project or a persona is
  asked for, type its name. The command looks the id up, and stops rather than
  guessing when the name matches nothing or matches more than one thing. Names it
  has looked up are kept in a small file beside your key, holding names and ids
  and nothing else. Anything that spends or deletes skips that file and asks the
  platform again.
- **Projects can be tidied up.** `project delete` prints the project, its name and
  how many runs it holds before anything goes, asks whether the run history goes
  with it, and removes nothing until you say yes.
- **Uploading data is a command too.** `data upload` and `data search`. The one
  place that handles your own files is no longer code typed out by hand. A folder
  goes up as one bundle and a single file as itself, with no flag to remember.
- **You now need pixi.** It takes over from `uv` as the tool this skill wants on
  your PATH. No other skill here needs it, and there is still nothing to install by
  hand: the first Edison command builds the environment it runs in. That took about
  22 seconds on the machine it was measured on. A plugin update lands in a fresh
  folder, so the build runs again once per release, faster the second time.
- **A promise the docs used to make is gone.** The page said the client could not
  touch your pixi setup, because it ran from a throwaway environment. That is no
  longer how it works. The new environment lives inside the plugin's own folder,
  which is still not a project of yours.
- **Why the whole change was worth it** is written down in
  `docs/adr/0011-the-spend-path-became-a-package.md`, including the two things the
  design had to give up along the way.

## 2026.9.8 — 2026-09-05

Docs only, in `lab-edison`. The Kosmos page described a call nobody had ever run.
Someone ran it, and it failed. This release corrects the page from that live run.

- **The documented way to start a Kosmos run did not work.** It created a project
  with no persona attached. The chat step then answered a 500, naming no field.
  The page now passes `persona_id`, and it records the 500 as what you get
  without one. It also says where a persona id comes from, because no method in
  the client lists personas.
- **A Kosmos run has no stop button, and the page now says so.** Nothing cancels
  a run as a whole. Cancelling its tasks one by one does not work either: the run
  sends out replacements a minute later. What works is two steps, in order. Queue
  a message telling the run to stop, then cancel whatever is still going. The
  page carries both, in that order.
- **Three more facts the run settled.** A third task name sits behind a run, and
  the tasks it starts go on to start tasks of their own. A reply from Kosmos is
  not in the message's `content` field, which is always empty; it rides in the
  tool call beside it. A stack trace out of `cancel` means the task id is wrong,
  not that the cancel failed.
- **The page no longer says it is untested.** The sentence claiming nothing on it
  had been run is gone. The chat call is marked verified, with the persona fix.
- **`tasks.md` names the field that holds a storage id**: `data_storage_id`. The
  page used to say the field was unknown and print the whole record instead.

## 2026.9.7 — 2026-09-05

Docs only. The four skill pages, the home page and the usage page were rewritten
shorter and in plainer English, and brought back in line with what the skills now
say. No skill, script or template changed, so nothing an agent reads is different.

- **Every page is shorter.** The six pages lost about 430 words, most of them from
  `lab-edison`, without dropping a fact anyone needed. Repeated material is gone:
  the list of what an agent refuses to do lived on both the home page and the
  usage page, and now lives on the home page alone, and the questions the agent
  asks before a job are on the usage page alone.
- **Plainer sentences.** Long dashes are gone from all six pages, bullet lists
  that were really paragraphs are paragraphs again, and page titles read as titles
  rather than as two ideas joined by punctuation. The README and this file were
  not part of the pass.
- **Kosmos leads the `lab-edison` page instead of trailing it.** It is the reason
  to reach for the platform when a goal is bigger than one question, and the page
  had it last, below the one-shot jobs, reading as a hazard to be fenced off. It
  now comes first, and the one-shot jobs follow. The rule is unchanged: the skill
  starts a Kosmos run only when you ask for that run.
- **`lab-edison` says "job" where the skill says job.** The page called them
  agents; the skill and its references call them jobs, and one word for one thing
  is easier to follow. Its key setup, spend rules and task-id recovery are
  unchanged.
- **The cluster table reads as people speak.** It named the clusters by the labels
  the setup check prints, `arc_hpc` and `ircbc_hpc`. Those labels now appear where
  you meet them, next to the check itself, and the table says arc and ircbc. The
  aside about ircbc's GPU nodes went with it; "CPU cluster" is the guidance, and
  `sinfo` is where to look for a node's state.

## 2026.9.6 — 2026-09-05

An architecture review of `lab-edison` found three claims about the Edison
platform that no source backed, and one safety rule that only worked if the
agent remembered it. This release corrects the claims, turns the rule into a
command, and makes every Edison page say where its facts came from.

- **Correction: the platform is run by Edison Scientific, not FutureHouse.**
  Edison Scientific is FutureHouse's commercial spinout, and the platform
  moved to it. Four releases named the wrong company, in five places. If you
  have repeated that to a colleague, this is the fix. The platform's own job
  names still read `job-futurehouse-…` and its persona picker still offers
  `@FutureHouse/…`. Those are live values and they are correct as they stand
  — naming left over from the spinout, and never something to "fix".
- **`lab-edison` now spends through one command, not a remembered rule.**
  `scripts/edison-task.sh` does submit, status, list, cancel and fetch. The
  task id is the first line it prints, before anything can block, so a run
  you paid for is always reachable. Submission takes your query as a file, so
  the text you approved is the text that goes out; a missing or empty file is
  refused before anything is spent. The command runs the preflight itself, so
  a session that skips the setup check refuses instead of spending. Your key
  reaches the client through the environment and by no other route. See
  `docs/adr/0010-edison-skill-runs-through-a-script.md`.
- **Correction: no price for a Kosmos run appears anywhere now.** The old
  claim — roughly two orders of magnitude more than an ordinary task — was
  sourced nowhere and shipped six times. A Kosmos run is billed for each of
  the tasks it fans out to, so it costs the sum of the ones it calls and
  there is no flat per-run price. Check your own balance. The rule has not
  changed: the skill never starts a run unless you ask for that run.
- **Correction: the reason data on ircbc has to come down first.** The skill
  said the platform cannot be reached from that cluster at all, and cited a
  page that says the opposite. The compute nodes there have no route out.
  The two hosts that do have one are a doorway and a data mover, and work
  does not run on either. So the instruction stands — the skill brings the
  files down and uploads from your machine — and the reason is now what its
  source supports.
- **Your key file passes at any owner-only mode.** Four documents said it had
  to be mode 600; the check has always accepted 400 as well. They agree now.
  `chmod 600` is still what the remedy hands you, because that is a command
  and not a claim about what passes. The preflight owns the four facts about
  the key file — the variable, the placeholder, the location and the modes —
  and prints them on request, so the onboarding template, the published page
  and the secrets sweep can be checked against it instead of repeating it.
- **Every `lab-edison` reference page says where its facts came from.** A
  provenance block at the head gives the source, the date it was checked, and
  a tier: **verified** (we ran it), **read** (from the package or a vendor
  page, not run), **unverified** (inferred). A claim at another tier is
  tagged where it is made, which is what now marks the Kosmos chat call
  nobody has ever run. See
  `docs/adr/0009-facts-carry-their-provenance.md`.
- **The skill body is 547 words, down from 950.** It holds what must be true
  before the first call and nothing else: the preflight and its refusal, the
  key rules, show-before-you-spend, never start Kosmos unasked, and one line
  saying which reference page answers what. Every procedure moved behind the
  seam to `references/`, which is where an agent was looking them up anyway.
- Also corrected: the blocking wait's default timeout was written in minutes
  in one file and in seconds in another, and `references/tasks.md` owns the
  number now. And the rule `2026.9.3` announced — never guess a job-name
  string — is written down at last, in `references/jobs.md`. The command
  will only send a name from its own short list, so there is nothing left to
  guess past.

Tests:

- **The gate can see four things it could not see before**: a commit putting
  FutureHouse back in charge of the platform (the job names, the persona
  handle and this file's history are exempt), a reference page with no
  provenance block or with a date that will not parse, key-file constants
  that have drifted apart, and a skill body over its cap. Each was checked in
  both directions — a sweep that can no longer fire looks just like a sweep
  that passes.
- **Skill bodies have a word cap of their own, 600** (`Lab.LengthSkill`).
  One dial used to cover skill bodies, reference pages and `AGENTS.md`
  together, so raising it for one handed room to all three. All four bodies
  pass untouched; the Edison body at its old size would not have.
- **The preflight's success path has a fixture at last.** All three of the
  old ones asserted failure, so the check that lets work proceed was the one
  path nothing covered. Three new cases: a replaced key at mode 400, an empty
  file, and a file that assigns nothing.
- The spend path is tested for nothing. The refusals never reach the network,
  and the checks that the task id leads the output and that the key never
  lands in an argument, a program or a log run against a stub.

## 2026.9.5 — 2026-09-05

A case study — one real research question put through `lab-edison` end to end —
found the skill spending a credit and returning nothing, and the fix reshaped
the skill around the task id.

- **`lab-edison` never blocks and never loses a run.** The old skill led with
  `run_tasks_until_done`, which blocks a tool call for up to 40 minutes. Facing
  that, a headless session pushed the submission into a background task and
  ended its turn; the process was killed, the task id had not been printed yet,
  and one credit bought an answer nobody could reach. The rule now is submit,
  print the task id, then poll in short calls — the id is the receipt for the
  credit and it outlives every shell.
- **A run is never lost, only misplaced.** `get_tasks` lists your own
  trajectories for free, so a run whose id went missing is found rather than
  bought again. The lost run from the case study was recovered this way, answer
  and citations intact.
- **New `references/tasks.md`** for the lifecycle every job shares: submit,
  poll, recover, `cancel_task`, what each response class carries, and how to
  attach a run to a project so it appears in the platform's browser view — an
  API run has no page there otherwise. `datasets.md` no longer repeats the
  polling half.
- **Correction: Kosmos is not browser-only, and `2026.9.2`–`2026.9.4` said it
  was.** `get_session` on a real Kosmos project session returns the job name
  `job-futurehouse-data-analysis-aries`. The old reasoning argued from the
  absence of a `JobNames` member without checking the surface Kosmos uses:
  `JobNames` enumerates the one-shot jobs `create_task` takes, and Kosmos is a
  **chat session on a project** — `send_chat_message`, `create_project`,
  `get_conversations` — that fans one objective out into many ordinary tasks
  over several rounds. A real project showed thirteen, eight
  `job-futurehouse-paperqa3-api` and five `job-futurehouse-data-analysis-heron`,
  all carrying that project's id.
- **The Kosmos rule changed shape with the facts.** It was "you cannot"; it is
  now **never start one unless the user asks for that run in those words**,
  which is the rule that was always needed — a run costs roughly two orders of
  magnitude more than an API task, and documenting the call makes an accidental
  start easier, not harder. Drafting the objective, checking the dataset and
  reading a run that already exists stay free, and are usually what was wanted.
  The exact chat invocation is marked unverified, because verifying it is the
  charge.
- The `edison-kosmos` eval asserted the claim that turned out to be wrong; its
  expect regex now names the structure the skill teaches.
- **The key-file setup left `SKILL.md` for the preflight script**, which now
  prints the exact remedy when a check fails. A verdict and its fix can no
  longer drift apart, and the agent relays tested text instead of recalling it.
- Corrected: `list_files` returns a dict keyed `data`, not a list. Recorded:
  `total_cost` and `total_queries` come back `None` on a real successful run,
  so no cost may be reported from them.

Tests:

- **`tests/eval.sh` has no default run.** A bare invocation prints the case
  list and exits without launching anything; the suite needs `--all`, one case
  needs `--only`, and `--live` alone is refused as a modifier rather than a
  request. Evals cost real tokens, and the failure being guarded is an agent
  running all of them on a hunch. `tests/lint.sh` self-tests the guard with
  `claude` stubbed, so a regression cannot spend anything even while failing.
- **New eval case `edison-recover`**: a run whose id was lost must be found in
  task history, not resubmitted. Its negative assertion is the point.
- **`tests/preflight.sh` covers both checks now**, clusters and Edison. Only
  the cluster check decides the exit code — a platform key is opt-in per user,
  and failing on it would teach people to ignore the script.

## 2026.9.4 — 2026-09-05

Guardrails, after a release-discipline failure: `2026.9.3` was tagged, two
test-only pull requests merged on top without a bump, and the plugin cache and
`main` both reported `2026.9.3` with different bytes. Nothing was wrong with
the skills; the number had stopped identifying the tree.

- **A version now names one tree, and every merged change bumps it** — tests
  included, because `source: "./"` ships the whole repo. `tests/lint.sh` fails
  a tagged version whose tree has moved and names the files that moved. See
  `docs/adr/0008-version-identifies-the-content.md`.
- **Eval assertions are tested against fixtures**, with no API call and no
  tokens. `tests/eval.sh --dump` prints the real assertions and the lint drives
  them over synthetic transcripts in `tests/fixtures/eval/`, so the regexes
  under test are the ones that run. Several fixtures are regressions from runs
  that were correct and were reported as failed.
- **The eval case lists are checked**, not merely kept. The usage comment,
  `AGENTS.md` and `tests/README.md` must all name every case;
  `tests/README.md` had been missing one through two releases.
- CI checks out with full history, so the release rule has tags to read. A
  missing tag list fails rather than passes.

## 2026.9.3 — 2026-09-05

- **`lab-edison` no longer argues that Kosmos is browser-only because the job
  enum omits it.** That reasoning was unsound and this is the correction.
  `TaskRequest.name` is typed `str | JobNames`, so the client sends any string
  it is handed — the enum is a convenience list, not a whitelist. Job names
  outside it do run on the platform: `job-futurehouse-paperqa3-api` and
  `job-futurehouse-data-analysis-heron` were both seen in task history and
  neither is in the enum. The conclusion stands, on better ground: no job name
  for Kosmos is published anywhere.
- **A new rule: never guess a job-name string.** It follows from the above and
  it is the practical half. A wrong guess teaches you that one string was
  wrong; a right guess starts a run costing about two orders of magnitude more
  than the task the user asked for. Submitting is the only decisive check, and
  submitting is what there is to avoid. **Corrected in `2026.9.6`:** the rule
  was announced here and never written into the skill. It reached the job
  reference three releases later.
- The enum listing is still documented, now framed as the check that can
  settle the question in one direction only.

## 2026.9.2 — 2026-09-05

- **New skill: `lab-edison`.** It runs work on FutureHouse's Edison
  research platform from your own machine: literature answers with
  citations, precedent, molecules, and analysis of a dataset you upload.
  No cluster is involved, which is a first for this plugin.
- **You have to ask for it by name.** It never loads on its own, because
  every run spends credits from your own account. Type
  `/lab-compute:lab-edison` and then your question. The setting behind
  that is Claude Code's; other agent tools ignore it and will trigger the
  skill like any other.
- **To use it, put your key in a file.** Copy `templates/edison.env` to
  `~/.claude/compute/edison.env`, paste your own key over the
  placeholder, and `chmod 600` it. Until you do, the skill refuses the
  task and says which check failed. It offers to write the file for you,
  and it will never ask you to type your key into the chat.
- **The key goes beside `personal.md`, never inside it.** An agent reads
  `personal.md` into the chat, so a key written there lands in every
  transcript. The skill also never sends the key anywhere — not to a
  cluster, not into a job script, not onto a command line.
- **It shows the job and the query before it spends.** Deep literature
  runs, analysis runs, and batches of more than three tasks stop and ask
  first. A follow-up continues the earlier task instead of paying again.
  No prices are written down anywhere: they change, and a stale one is
  worse than none.
- **Kosmos runs in your browser and nowhere else.** No API can start one.
  The skill says so before it tries, then helps you draft the goal and
  check the data, because you pay for that run by hand.
- **The first run on a machine is slow.** The client installs into
  nothing you maintain, so it downloads dozens of packages the first
  time. It looks hung. It is not. Later runs come from the cache.
- **Edison cannot reach ircbc.** Its compute nodes have no route out, so
  the skill says so and stops. For data on arc it brings the files down
  and uploads from your machine, keeping your key off a shared cluster.
- **For maintainers: the combined description budget no longer fails the
  gate.** The 1536-character figure is the cap on one skill's
  description, not on the sum across a plugin. The per-skill check stays
  and the running total is still printed, now as information. A comment
  where the old check stood records why, so nobody puts it back. The gate
  also gained a rule that fails any commit setting the Edison key to
  anything but the shipped placeholder, and the agent-doc word cap rose
  from 1000 to 1200.
- **The plugin's own description widened.** It read "Liu Lab HPC clusters
  and remote-compute workflow", which no longer covers a skill with no
  cluster in it. It now reads "Liu Lab HPC clusters, remote-compute
  workflow, and the research platforms the lab runs work on".

## 2026.9.1 — 2026-09-05

Both fixes here were found by running the agent evals, which had not run
against `2026.9.0`. Neither shows up in lint.

- **The login-node rule is back in the hard-rules list.** Splitting it into
  its own section left the list that reads as the safety summary without the
  most important rule in it. Asked to state the hard safety rules, an agent
  quoted three bullets and none of them mentioned a login node. The list now
  leads with it and points at the section for the reasoning.
- **Say "reuse" where reuse is meant.** The step that finds your running job
  described taking a foothold but never named the act. It now reads "find and
  reuse the node you already hold".
- The `reuse-job` eval also accepts the newer wording. A correct plan that
  said "holding your job" and "no new allocation" was failing an assertion
  that only knew the older phrasing. The alternatives stay specific enough to
  fail a plan that works on the login node.

## 2026.9.0 — 2026-09-05

- **Work belongs on a compute node, not a login node.** The old rule was
  about load: no heavy work on a login node, light commands fine. That left
  `ssh arc '<cmd>'` as the normal reflex, and many agents each running
  "small" commands is what overloads a shared machine. The rule is now about
  place. There are two reasons to touch a login node, and no others: you hold
  no job yet and must submit one, or the compute node lacks what you need. On
  ircbc that means internet and `git`. On arc it means nothing at all.
- **Checked on both clusters, not recalled from memory.** The whole Slurm
  client works from a compute node on arc and ircbc alike, so job management
  never needs a login node. Two things the references claimed turned out to
  be wrong. ircbc lets you ssh to a compute node you hold no job on, so
  "reachable" is not "allowed" and working there takes CPU from the job the
  scheduler put on that node. And `git` is not installed on ircbc compute
  nodes at all.
- **Skills split into smaller files.** Five long documents became fourteen
  short ones. `lab-hpc` gained `arc-slurm.md` and `ircbc-slurm.md`;
  `lab-jupyter` and `lab-containers` gained reference folders. Each file now
  covers one thing.
- **No measurements in skill docs.** Free space, percentages, queue waits and
  timings were recorded during the cluster survey. They were true that
  afternoon and misleading after, and an agent reading them cannot tell.
  They are replaced by the guidance they stood for and the command that
  gives a live answer. `AGENTS.md` now states the rule and the line between a
  measurement and a setting an agent must type.
- **One gate command, and CI runs it.** The repo gained a pixi workspace and
  `pixi run check`, which CI now runs on every pull request. It checks
  formatting, types, shell scripts, prose and markdown structure: ruff,
  pyright, shellcheck, vale, markdownlint and a conformance check. The prose
  gates cap agent-facing pages by word count and human-facing pages by
  reading grade.
- **Repo furniture.** An MIT licence. A one-command installer in place of
  hand-made symlinks. A glossary, a set of agent conventions and five
  decision records. The docs site now builds with zensical.

## 2026.7.6 — 2026-07-21

- **Editorial concision pass (no behavior change).** Tightened the
  agent-facing text so the LLM-facing instructions are shorter and more
  consistent. The idle-interactive-job reuse guidance was stated three times
  with overlapping prose (`lab-hpc` SKILL.md hard rule + its own section,
  plus both cluster references); made SKILL.md's "Default execution target"
  the single canonical write-up and reduced the two references to brief,
  same-worded pointers. Trimmed the login-node hard rule. Aligned
  `lab-jupyter`'s cross-reference to the new "Default execution target" name.

## 2026.7.5 — 2026-07-21

- **arc needs no VPN** (`references/arc-hpc.md`): added an explicit "No VPN"
  note so agents don't misgeneralize ircbc's atrust-VPN rule to arc — a
  hanging `ssh arc` is not a VPN problem. (VPN mentions were already scoped
  to ircbc everywhere; this states the arc side positively.)

## 2026.7.4 — 2026-07-21

- **Reuse idle interactive jobs instead of `ssh <login>` for work**
  (`lab-hpc`).
  - `SKILL.md` gains a "Default execution target" section. Before running
    anything heavier than light Slurm control, check `squeue` for an idle
    interactive job that already exists — `--me` on arc, `-u $USER` on
    ircbc. If one is there, `ssh <node-alias>` onto it. Create a job, with
    confirmation, only when none exists.
  - The #1 hard rule now names the `ssh arc "<command>"` anti-pattern. It
    also says why that matters: parallel agents and subagents.
  - Both cluster references lift their idle-reuse notes, and
    `docs/skills/lab-hpc.md` mirrors the enforcement bullets.

## 2026.7.3 — 2026-07-20

- **Clarified the #1 hard rule** in `lab-hpc`, the one about login nodes. It
  now spells out which commands are light and which are heavy. Light means
  `cd`, `ls`, git, Slurm control and small transfers. Heavy means `pixi`,
  builds, big downloads and training, and all of it needs a compute job.
  Staging downloads are the exception. `docs/skills/lab-hpc.md` mirrors the
  wording for readers.
- **arc network fact** (`references/arc-hpc.md`). *Both* login and compute
  nodes have direct internet. ircbc differs: its compute nodes are offline,
  and its login node goes out through a SOCKS proxy. The rule's exception
  now points at both references.
- **personal.md template.** A new prompt records a persistent interactive
  job, with its partition and node alias. Agents reuse that job with
  `ssh <node>` rather than allocate a fresh one.

## 2026.7.2 — 2026-07-05

- **Repo is now public** (full git history swept for IPs, usernames,
  hostnames, and key material first — clean). README/CLAUDE.md reworded:
  the security policy is what makes publicness safe; install prereqs no
  longer mention org access; dropped the private-marketplace
  `GITHUB_TOKEN` note.
- **Human-facing docs site** (MkDocs Material) under `docs/` +
  `mkdocs.yml`: index (what/install/update), basic-usage page, and one
  page per skill — concise end-user prose, distinct from the agent-facing
  SKILL.md files. Deployed to GitHub Pages from the `gh-pages` branch by
  `.github/workflows/docs.yml` (`mkdocs gh-deploy`, theme pinned `<10`) on
  pushes to main touching the docs.
- `tests/lint.sh`: sweep now excludes the gitignored `site/` build output.

## 2026.7.1 — 2026-07-05

Coherence pass across the three skills, from a multi-agent review of the
whole repo. No cluster facts changed. Only structure, routing and decision
points moved.

- `lab-jupyter` is now one cluster-parameterized lifecycle: reuse → submit →
  token → tunnel → cleanup. It replaces an arc-only procedure that had an
  ircbc paragraph bolted on.
  - A parameter table carries the arc/ircbc substitutions: login alias,
    `squeue --me` vs `squeue -u $USER`, partition, submit source, job-log
    path, tunnel target.
  - Step 1 gains the idle-reservation branch it was missing.
  - Step 3 finds the token by provenance. Grep the job log if the skill
    submitted the job. Use `server list` if it reused one (arc only).
  - Step 4 gains a safe busy-port decision list. Identify the listener
    before any kill.
  - `<jupyter>` is marked arc-only. Partition cost and queue rationale now
    points at `references/arc-hpc.md` instead of restating it.
- The Jupyter-on-ircbc ownership split is codified, in CLAUDE.md too.
  `lab-jupyter` owns the session lifecycle. `lab-containers` owns the
  container invocations, including the ircbc submit command. Its duplicated
  tunnel line is gone. Its Jupyter block now leads with the lifecycle
  pointer, so agents entering there still reuse before they submit.
- `lab-containers` hardening:
  - A directive scope line: ircbc only, do not apply to arc.
  - §1 says where "update" continues, and where to find crane re-fetch.
  - §3 warns that `sbatch --wait` blocks. Do not resubmit on a dropped
    connection. The digest sidecar is now gated on exit 0.
  - §4 explains the two-level quoting of the `<check>` slot and shows a
    fuller example. It also gains a smoke-test-failure branch, because a bad
    SIF otherwise looks up to date forever.
  - The interactive shell takes `-t <time>`, like its siblings.
- `references/ircbc-hpc.md`: the stale "typical batch job" recipe is gone.
  It lacked the required pixi activation and contradicted `lab-containers`
  §5. The section keeps the facts and points at "Using the images".
- `references/arc-hpc.md`: a new "Submitting" H3 lifts the wrapper,
  smoke-test and reservation how-tos out from under "Choosing a partition".
  The `mkdir -p sbatch` guard is noted before the reservation script. The
  idle-reservation paragraph now points at `lab-jupyter`.
- `lab-hpc`:
  - The description now includes "login node", the term users type and evals
    assert, at no budget cost.
  - Cluster choice is reframed as **the user's decision**. Ask, or infer
    from session context. Never auto-route. Per-cluster factors are listed,
    and SIF work goes to `lab-containers`. `lab-jupyter`'s parameter step
    echoes this.
  - The quick-reference table is slimmer. Partition detail moved to a
    bullet, and `ircbc-transfer`'s no-`/share`-mount caveat is now visible.
  - The hard-rules parenthetical covers chimera `CPU****` aliases, and the
    step-0 personal.md wording is more precise.
- ircbc facts re-verified 2026-07-05. `$HOME` auto-binds inside the SIFs,
  as noted in `lab-containers` §5. Local → `/share` uploads go straight
  through the `ircbc` login alias, as recorded in `references/ircbc-hpc.md`.
- Tests:
  - New `jupyter-ircbc` eval case, for the seam this review found broken.
  - The `reject` and `containers` assertions drop terms the prompt itself
    contains, or that a wrong plan would also emit.
  - Lint now sweeps local ssh-config HostNames (dotted values), as it
    already did usernames.
  - `check-hpc-config.sh` warns, and never fails, when arc per-node aliases
    are missing.
- Docs:
  - README skill blurbs updated. lab-jupyter covers both clusters, and
    lab-containers covers version checks and usage.
  - Symlink instructions cover all three skills.
  - Release steps mention CalVer and this changelog.
  - `templates/personal.md` gains the Jupyter port, launch-path and
    resources fields the skills actually read.

## 2026.7.0 — 2026-07-05

- **Switched to CalVer** (`YYYY.M.PATCH`).
- `lab-containers` expanded:
  - Digest-based version checks: each SIF gets a `.sif.digest` sidecar;
    never rebuild blindly — compare against `crane digest` and ask the user
    when the remote is newer.
  - Pulls are now pinned to the checked digest.
  - New "Using the images" section (verified on-cluster): run commands,
    interactive pixi-env shells from the local PC (`bash --rcfile`
    activation; `singularity run` documented as broken under Singularity
    3.2.1), and Jupyter-in-container with the local tunnel.
- `lab-jupyter`: ircbc is now supported via the Singularity-image flow
  (points at lab-containers for the submit recipe).
- `$LIU_LAB_PACKAGES` store made group-writable with setgid dirs so all
  `lhqlab` members can add/update images; documented in the ircbc reference.
- `tests/eval.sh`: cases now run concurrently (full suite ≈ slowest case);
  added guidance to prefer `--only` and ask before full/`--live` runs; noted
  that evals exercise the installed plugin, not the working tree.

## 0.5.0 — 2026-07-05

- New `lab-containers` skill: the repeatable SIF pull → build → test recipe
  for ircbc. Crane pull runs on the login node. An sbatch job builds from
  the docker-archive, and the tarball is deleted once the build succeeds.
  Per-env smoke tests mirror the image's own build checks. The ircbc
  reference now holds facts only, and points at the skill for the procedure.
- CLAUDE.md states the repo's organizing principle. `lab-hpc` holds the
  facts, in its references. The other `lab-*` skills are task recipes, and
  they never duplicate a fact.
- New repo-wide hard rule in `lab-hpc`. Never submit sbatch or srun work
  without showing the exact script and getting the user to confirm it.
- Tests: a new `containers` eval case. The live-sbatch eval prompt now
  carries explicit submission approval, to stay compatible with the new
  rule.

## 0.4.1 — 2026-07-05

- Added `CLAUDE.md` (repo guidance for Claude Code) and this changelog.

## 0.4.0 — 2026-07-05

- First published release: repo pushed to `github.com/liuhlab/liulab-compute-skills`
  (private), marketplace installs switched from local path to GitHub.
- ircbc reference expanded with verified operational detail:
  - Network topology: no internet on compute nodes; login node reaches out
    via a SOCKS proxy tunneled from the transfer node; transfer node has
    full direct internet, ~1 TB local disk, and no `/share` mount.
  - `$LIU_LAB_PACKAGES` shared package store layout
    (`/share/lhqlab/liulab_data/packages`).
  - Offline container-image workflow: `crane pull` a docker-archive tarball
    on the login node → `singularity build` the SIF in a compute job
    (validated end to end with `liulab-runtime:ml` + a Jupyter Lab smoke
    test on a compute node).
  - Gotchas: proxy env propagates into Slurm jobs (use
    `curl --noproxy` / `unset`); Slurm 18.08 lacks `squeue --me`.

## 0.3.0 — 2026-07-04

- ircbc reference verified on the cluster. It runs CentOS 7, glibc 2.17 and
  Slurm 18.08. Its partitions are `compute_cpu`, the default, with
  MaxNodes=2; `compute_fat`; and `compute_gpu_2080`, which is drained.
  Singularity comes from `module load singularity`, verified on both login
  and compute nodes.
- `lab-jupyter` is now cluster-aware. The arc flow is a
  `zhoulab_gpu_priority` job plus an ssh tunnel. Resources — CPU, memory,
  GPU and time — must come from the user. The sbatch script is always
  confirmed with the user before it is submitted. ircbc is declared
  not-yet-supported.

## 0.2.0 — 2026-07-04

- Three-layer test suite under `tests/`. Layer 1 is static lint: naming,
  frontmatter, the description budget and the no-secrets sweep. Layer 2 is
  the environment preflight. Layer 3 is headless agent evals (`claude -p`),
  including a live ssh and sbatch case that runs end to end.
- `lab-hpc` config preflight: `scripts/check-hpc-config.sh`, which checks
  the aliases with `ssh -G`. Skills now refuse HPC requests on a machine
  that is not configured.
- arc reference: partitions and QOS verified, with cost and queue guidance.
  `zhoulab_gpu_priority` and the preemptible tiers are free. `preemptible`
  and `quick_preemptible` are GPU-capable, and `cpu_preemptible` is CPU
  only. The shared `gpu` queues bill extra and wait long. Always set
  `--time`.
- New `lab-jupyter` skill: a Jupyter Lab job on arc, plus a local ssh
  tunnel.

## 0.1.0 — 2026-07-04

- Initial release. It ships the marketplace `liulab`, the plugin
  `lab-compute` and the skill `lab-hpc`, which covers cluster choice, safety
  rules, the dev workflow and the per-cluster references. It also ships the
  onboarding templates `personal.md` and `CLAUDE-stub.md`, plus a README.
- Clean-history publish policy: no IPs, usernames, keys or passwords
  anywhere in the repo.
