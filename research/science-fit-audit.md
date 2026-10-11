# Science-fit audit: mattpocock/skills and pstack

Research note for #65, part of the map #62.

**Source:** `mattpocock/skills@49dd158` and `cursor/plugins@978ca6e` (pstack v0.15.17).
I read every in-scope `SKILL.md` in full, and skimmed the playbooks, references and guide.
I also read the three non-upstream skills installed on the maintainer's machine.
**Checked:** 2026-10-10.
**Default tier:** read. Every verdict and every proposed edit is a **judgement**.
Claude Code facts marked *observed* come from this session's own tool and skill list.
Nothing was run in Codex or Kimi Code, so their cells say what an upstream doc claims, or *unverified*.

**Paths.** A mattpocock skill `x` is `skills/engineering/x/` or `skills/productivity/x/` at `49dd158`.
A pstack skill `x` is `pstack/skills/x/` at `978ca6e`. A playbook `p` is `pstack/skills/poteto-mode/playbooks/p.md`.

**Count correction.** At `978ca6e` pstack has 52 skills, 24 of them `principle-*`, not 51 and 26.
I counted the `SKILL.md` files (verified), and the pstack README also says "twenty-four principles".

## Answer

- **mattpocock fits as the base.** Of the 27 in-scope skills, 16 adopt as-is and 9 need named edits.
  `ask-matt` folds into liulab-mode and `wizard` is skipped.
  The workflow core is domain-neutral: grilling, wayfinder, research, to-spec, to-tickets, tdd and code-review.
  The web assumptions sit in examples and a few template lines.
  Examples are vertical slices "through schema, API, UI", user stories, dev-server loops and screenshot evidence.
- **pstack is mostly a source of ideas.** 18 of its 24 principles adopt as-is.
  Nine items need edits: `unslop`, `technical-writing`, `show-me-your-work`, `benchmark-checklist`, `ketchup`, and four principles.
  Eleven become ideas: `poteto-mode`, `automate-me`, `figure-it-out`, `why`'s epistemics and others.
  Fourteen are skipped: Cursor-only machinery, TypeScript-only rules, multi-model panels and PR-stack automation.
- **The edits that matter most for science (judgement).**
  `research` cites papers and tags each claim with the lab's provenance tier.
  `diagnosing-bugs` runs its loop in an existing interactive Slurm job, and confirms any new submission.
  `tdd` and `explain-the-number` learn golden-fixture checks and result-number checks.
  `to-spec` gains an analysis-plan template.
  `never-block-on-the-human` gains the lab's always-confirm list: sbatch, Edison spend, the shared store, wet-lab steps.
  `unslop` stops flagging terms of art (substrate, vector, modality, scaffold, landscape), citations in parentheses, and a methods section's passive voice.
- **One repo decision saves ten lab edits.** mattpocock renamed its glossary from `CONTEXT.md` to `GLOSSARY.md` (its README says so).
  Ten in-scope skills name `GLOSSARY.md`, and this repo uses `CONTEXT.md`.
- **liulab-mode** takes `poteto-mode`'s shape, not its content.
  That shape is a trigger table pointing at skills, an inline principles index, an always-pause list, reply rules, and a playbook router.
  Draft it with `automate-me`'s mining method over Claude Code and Codex transcripts, and scrub it before it lands in this public repo.
- **The three non-upstream skills all retire.** `avoid-ai-writing` is absorbed into the lab's `unslop`.
  The mattpocock skill `retro` and the harness's own memory supersede `self-improvement`.
  `find-skills` triggers on "how do I do X", which matches every science how-to question.
- **Keep these sets whole.** `wayfinder` needs `setup-matt-pocock-skills`, `research`, `prototype`, `grilling` and `domain-modeling`.
  `implement` and `implement-spec` need `tdd` and `code-review`.
  `tdd` and `improve-codebase-architecture` need `codebase-design`.
  `retro` needs `writing-for-agents`.

**Verdicts.** *Adopt as-is*: ship the upstream text unchanged. *Adopt with edits*: ship it with the named edits.
*Idea only*: no skill ships; the named idea moves into the named place. *Skip*: nothing comes in.
My rule for an edit: it must stop the agent doing the wrong thing in lab work.
A TypeScript example that a Python reader translates on sight does not earn an edit, because every edit is drift to carry against upstream.

## mattpocock/skills (`49dd158`)

| Skill | Assumes | Verdict | Edits or reason |
| --- | --- | --- | --- |
| `ask-matt` | A router over mattpocock's user-invoked skills and its idea-to-ship flow. | Idea only | Fold the main-flow map and `PHASE-BOUNDARIES.md` into liulab-mode's router. A router that cannot see `lab-*` skills or science flows would be a second index that drifts. |
| `code-review` | A git diff against a fixed point. Documented standards plus a Fowler smell baseline, which is object-oriented (Feature Envy, Refused Bequest). The spec comes from the tracker. | Adopt with edits | (1) Add a science smell baseline beside Fowler's: hard-coded absolute or cluster paths, unseeded randomness, silent NA or row drops, 0-based and 1-based coordinates mixed, a threshold with no cited source, notebook state that depends on cell order. (2) The spec source may be an analysis plan or a methods section. Keep the two-axis design. |
| `codebase-design` | Language-neutral vocabulary. TypeScript snippets (`StripeGateway`). `DEEPENING.md` uses PGLite, microservices and Stripe as examples. | Adopt as-is | The vocabulary fits Python and R libraries and pipeline steps. The web examples are illustrations, not instructions. |
| `diagnosing-bugs` | A loop that runs in seconds: a failing test, curl against a dev server, Playwright, `git bisect`. The agent runs the loop unattended. | Adopt with edits | (1) Add science loop builders: subsample the input to a fixture that still goes red; diff against a known-good output or a published value; pin seeds, threads and GPU determinism. (2) A loop that needs the cluster runs in an existing interactive job, per `lab-hpc`. A new `sbatch` or `srun` is shown and confirmed first, so "unattended" stops at job submission. |
| `domain-modeling` | `GLOSSARY.md` and `docs/adr/`. Checks terms against the code. | Adopt as-is | Science vocabulary is where it pays most (sample, library, run). This verdict depends on the glossary-name decision under Open points. Otherwise this skill is the first of ten needing the same rename edit. |
| `grill-with-docs` | A wrapper over `grilling` and `domain-modeling`. | Adopt as-is | Domain-neutral. |
| `implement-spec` | Tickets form a task graph. Parallel implementer subagents in worktrees, a merger subagent, one integration branch. | Adopt as-is | For software-shaped work: lab tools and pipelines. Needs background subagents and worktrees. Claude Code has both (observed); Codex and Kimi Code unverified. |
| `implement` | A typechecker, single test files, a full suite. | Adopt with edits | (1) "Run typechecking regularly" becomes "run the repo's check task, for example `pixi run check`". (2) For analysis code with no suite, rerun on the fixture and diff the outputs against the pinned result. |
| `improve-codebase-architecture` | A modular codebase with commit hot spots. An HTML report built from Tailwind and Mermaid CDNs, opened in a local browser. | Adopt as-is | Useful on lab tool repos. A notebook-only repo has little for it to find. |
| `pr` | Summary visuals are component trees and call trees (React-shaped). Evidence ranks screenshots, then test output. Blast-radius examples are layout shift and mobile. | Adopt with edits | (1) Evidence for an analysis change is a before and after figure or a diff of the key numbers, with the commit and job ID that produced it. (2) Blast radius names the results, figures and downstream files that change, and any published number that moves. |
| `prototype` | Two branches: an HTML state-machine demo, or UI variants on one route behind `?variant=`. | Adopt with edits | Add a third branch for an analysis or figure question. Build a throwaway script or notebook on a subsample that renders 2 or 3 variants side by side: normalisations, parameter choices, panel layouts. Keep both existing branches, because wayfinder's prototype tickets call this skill. |
| `research` | A background agent. Primary sources are official docs, source code, specs and first-party APIs. Output is one cited Markdown file. | Adopt with edits | (1) Name the science primary sources: the paper by DOI, PubMed, bioRxiv, database docs (Ensembl, UniProt, GEO), tool source. (2) Tag each claim verified, read or unverified per ADR 0009, and keep direct evidence apart from inference as in pstack `why/references/epistemics.md`. (3) Never route through Edison unless the user asked. Edison spends credits, and `lab-edison` is user-invoked. |
| `retro` | Session logs on this machine. `package.json` or other build-tool check scripts. Dev-server logs. | Adopt as-is | It already reads the repo's own check command. Slurm job logs fit its "information access" category without an edit. |
| `setup-matt-pocock-skills` | Per-repo setup of the tracker, triage labels and domain-doc layout. GitHub by default. | Adopt as-is | A hard dependency of `to-spec`, `to-tickets`, `triage`, `wayfinder`, `code-review` and `implement-spec`. This repo already holds its output in `docs/agents/`. A lab repo template could pre-seed those files, so most repos never run it. |
| `tdd` | Red then green at confirmed seams, with anti-patterns. TypeScript and jest examples in `tests.md` and `mocking.md`. | Adopt with edits | (1) Most analysis outputs have no independent literal. Allow a frozen golden-fixture output with a stated numeric tolerance as the source of truth. (2) Take pstack `tdd`'s rule: when a test needs the cluster or the full dataset, use the closest executable check and say so. |
| `to-spec` | User stories ("As a mobile bank customer"), schema changes, API contracts. | Adopt with edits | Add an analysis-plan template for analysis work: question, data and provenance, methods, outputs (figures and tables), validation and controls, out of scope. Keep the product template for tools. |
| `to-tickets` | Vertical slices "through every layer (schema, API, UI, tests)". CI stays green batch to batch. | Adopt with edits | Reword the slice rule so a tracer bullet can be one sample, or a subsample, carried through every pipeline stage to a figure. Expand-contract stays as written. |
| `triage` | External reporters, a label state machine, `.out-of-scope/`, agent briefs. | Adopt as-is | Fits shared lab tool repos; this repo already has `docs/agents/triage-labels.md`. Analysis repos rarely get raw external issues. |
| `wayfinder` | A tracker with sub-issues and native blocking. Domain-neutral by design. | Adopt as-is | This map runs on it. |
| `wizard` | Human-only steps that end in `.env` values and `gh secret` writes. Third-party dashboards. | Skip | The lab's human-only steps (ssh config, keys, VPN, the Edison key) are outside this repo by policy. A generated script that captures secrets is the wrong default for a public repo. It is model-invoked, so it would also fire on "set up credentials". |
| `grill-me` | A wrapper over `grilling`. | Adopt as-is | Domain-neutral. |
| `grilling` | Rounds of questions in plain chat. Facts come from subagents, decisions from the user. | Adopt as-is | The core primitive, domain-neutral. |
| `handoff` | A file in `$TMPDIR` with a suggested-skills section. | Adopt as-is | Portable across all three agents, which is the lab's multi-agent case. |
| `teach` | A stateful workspace of HTML lessons, quizzes and `MISSION.md`. | Adopt as-is | Fits onboarding a new lab member to Slurm, single-cell analysis or statistics. It keeps the `teach` name over pstack's. |
| `to-questionnaire` | One recipient holds knowledge the user lacks. | Adopt as-is | Collaborators, core facilities, sequencing providers. |
| `wait-what` | Re-pitch the last message in ASD-STE100, using `GLOSSARY.md` terms. | Adopt as-is | Covers pstack `bro`. |
| `writing-for-agents` | Skills and `AGENTS.md` written as context pointers. | Adopt as-is | Complements `docs/agents/writing.md`, which holds the caps and vale rules. |

**Outside the two buckets.** `skills/in-progress/writing-fragments`, `writing-beats` and `writing-shape` are an explore-then-exploit writing flow that grounds each concept before using it.
They are the closest upstream match to paper and grant writing. Watch them; the in-progress README says they "can change or disappear without warning".
`claude-handoff` runs `claude --bg`, so it is Claude Code only. `setup-ts-deep-modules` is TypeScript only.
`skills/misc/` is frozen upstream (`.out-of-scope/frozen-misc-skills.md`).

## pstack (`978ca6e`)

### Skills

| Skill | Assumes | Verdict | Edits or reason |
| --- | --- | --- | --- |
| `architect` | Type sketches with `not implemented` bodies, run through `arena` on two model families. TypeScript tells (`any`, casts). | Skip | mattpocock `codebase-design/DESIGN-IT-TWICE.md` already runs radically different designs in parallel. |
| `arena` | N candidates on Claude and Grok, a judge from the other family, grafts. | Skip | The multi-model panel is Cursor routing; a same-model version duplicates DESIGN-IT-TWICE. |
| `automate-me` | Mines Cursor `agent-transcripts/`. Uses Cursor's `AskQuestion` and `create-skill`. Writes `.cursor/skills/<handle>-mode`. | Idea only | The drafting method for liulab-mode; see below. Run it once by hand. |
| `benchmark-checklist` | `uptime`, `nproc`, profilers. Points at the Opening a PR playbook. | Adopt with edits | (1) Measure inside a Slurm allocation on a compute node, never on the login node, and record node type, GPU and job ID with the number. (2) Point at mattpocock `pr` instead of Opening a PR. The seven questions carry unchanged. |
| `blast-radius` | A diff in a product repo. Library pins. Solid and React timing. | Idea only | Fold "name the one fact the change is safe because of, and prove it by running code" into mattpocock `pr`'s Merge Danger section. |
| `bro` | Restate the last message plainly. | Skip | mattpocock `wait-what` does this with the glossary. |
| `correct` | Repeated agent mistakes, fixed by architecture, then types, lint, tests, docs last. A rule-to-enforcer table. | Idea only | Fold the ladder and the table into mattpocock `retro`'s automated-checks category and into this repo's `AGENTS.md` practice. |
| `create-verification-skill` | An app with a UI, CLI or service to launch and drive. Writes `.cursor/skills/verify-<app>`. | Idea only | The science analogue is a pipeline smoke run on a fixture: launch, doctor, drive, evidence, cleanup. That belongs in a lab pipeline template, not a generator skill. |
| `figure-it-out` | Reads poteto-mode's principles. Uses `architect` and `arena` for one-way doors and a `show-me-your-work` trail. | Idea only | Becomes liulab-mode's fallback when no playbook fits. Its loop, "each unit is an experiment", is already the scientific method. |
| `how` | Explorer and explainer subagents on per-role models from `pstack-models.mdc`. Cursor `readonly` Task calls. | Idea only | Keep its output shape (Overview, Key Concepts, How It Works, Where Things Live, Gotchas) for liulab-mode's investigation playbook. The harness's own explore agents do the walking. |
| `interrogate` | One reviewer per model family. Lead-judgment buckets. | Skip | Multi-model review is Cursor routing; mattpocock `code-review` is the review skill. |
| `ketchup` | A catch-up on everything since the user's last message, with action items. Written in `bro`'s voice. | Adopt with edits | (1) Replace the `bro` pointer with the lab's plain-voice rule (`unslop`). (2) Name Slurm jobs and Edison tasks beside PRs and CI runs as things to check. It pays off after long runs with many subagents. |
| `maintain-verification-skill` | A generated verify skill with a feature map. | Skip | Follows `create-verification-skill`. |
| `make-bot-ui` | Grok Bot webhook routines, Cursor panels, Tailscale. | Skip | A Cursor-only product. |
| `no-comments` | The Comment Sicko subagent, eslint and ts-ignore focus. Deletes most comments. | Skip | Science code needs the comment that cites a threshold's source, and the persona deletes it. Keep one liulab-mode line: a comment states a non-obvious why. |
| `poteto-help` | A help router over pstack, Cursor install and custom modes. | Skip | liulab-mode is the router. |
| `poteto-mode` | Cursor custom-mode frontmatter, per-role models, `poteto-agent`, `cursor-team-kit`, Bugbot, PR stacks. | Idea only | The shape of liulab-mode; see below. |
| `recall` | The Cursor transcript path. `why`'s MCP investigators. | Idea only | Keep its brief contract for liulab-mode's pickup step: a capsule, status-tagged threads, recurring problems, one next move. |
| `reflect` | Three reviewers over a Cursor transcript, `create-skill`, a devex tracker. | Skip | mattpocock `retro` covers it. |
| `setup-pstack` | `~/.cursor/rules/pstack-models.mdc` and Cursor model slugs. | Skip | The lab has no per-role routing; see the harness section. |
| `show-me-your-work` | An append-only TSV decision log, `scripts/log.sh`, an audit against the Cursor transcript, a reviewer from another model family. | Adopt with edits | (1) The transcript path becomes "this harness's session log". (2) The reviewer is a fresh subagent, on another model where the harness offers one. (3) Evidence may be a job ID, an output path, a figure path or a commit. It is a computational lab notebook for long runs. |
| `swarm` | Cursor cloud workers (`environment: "cloud"`). | Skip | Fan-out over samples is a Slurm job array, not a fleet of agents. |
| `tdd` | TDD for bug fixes only; skip when a test is impractical. | Skip | mattpocock `tdd` wins. Its "closest executable check" rule moves into mattpocock `tdd`. |
| `teach` | Explains a subsystem through `how` and `why`. Uses an image-generation tool. | Skip | The name collides with mattpocock `teach`, and it depends on `how` and `why` routing. |
| `technical-writing` | Diátaxis, Google developer style, STE, Global English. Tabs in code snippets. | Adopt with edits | (1) Add a register note. Papers and grants follow IMRaD and the venue's style; Diátaxis is for docs. Wet-lab protocols are how-to guides under STE rules: hazard before the step, quantities with units. (2) Drop "indent code snippets with tabs", which clashes with Python and markdownlint. |
| `typescript-best-practices` | `.ts` and `.tsx` files, triggered by a `paths:` glob. | Skip | TypeScript only. |
| `unslop` | 33 numbered AI-tell rules. User-invoked, yet "must always apply". | Adopt with edits | (1) Rules 7 and 26 apply to metaphor only. Substrate, vector, modality, scaffold and landscape are terms of art in biology. (2) Rule 13 allows parentheses for citations, units, statistics and first-use abbreviations. (3) Under rule 29, a methods section follows the venue's voice. (4) Absorb `avoid-ai-writing`'s venue rule and second-pass audit. (5) Make it model-invoked, so other skills can call it in Claude Code. |
| `why` | MCP discovery across chat, Datadog, Sentry, Databricks, Linear and Notion, plus git blame. | Idea only | Take the five confidence tiers in `references/epistemics.md` (direct, supported, inferred, speculative, unknown) into mattpocock `research` and liulab-mode's claim rule. The MCP roster is product observability. |

### Principles

All 24 are short and mostly language-neutral. Each has `disable-model-invocation: true`; see the cross-reference section on what that means outside Cursor.

| Principle | Assumes | Verdict | Edits or reason |
| --- | --- | --- | --- |
| `laziness-protocol` | General. | Adopt as-is | The smallest change; fits analysis code. |
| `foundational-thinking` | General. CI and lint count as scaffold. | Adopt as-is | "Data structures first" fits an AnnData layout or a sample-sheet schema. |
| `redesign-from-first-principles` | General. | Adopt as-is | No edit needed. |
| `attack-the-premise` | Load-imbalance language: actors, a census. | Adopt as-is | A census written as a rerunnable script is good science practice. |
| `subtract-before-you-add` | General. | Adopt as-is | No edit needed. |
| `minimize-reader-load` | General. | Adopt as-is | No edit needed. |
| `outcome-oriented-execution` | Planned migrations with phase boundaries. | Adopt as-is | Pipeline rewrites. |
| `experience-first` | Product UI: transitions, alignment, spacing. | Adopt with edits | Replace the UI-detail list with the consumer of a result: figure legibility (axis labels, units, colour-blind-safe palettes), and the lab member who runs the pipeline. Its last paragraph already widens "user" this way. |
| `exhaust-the-design-space` | Novel UI or architecture. | Adopt as-is | Compare 2 or 3 analysis approaches before committing to one. |
| `build-the-lever` | Codemods, generators, dump-to-sqlite queries. | Adopt as-is | The strongest science fit: the script is what a reviewer reruns. |
| `model-the-domain` | General. | Adopt as-is | A sample sheet as a typed table, not branches on sample names. |
| `boundary-discipline` | Edges: CLI, config, network. | Adopt as-is | Parse sample sheets and configs where they enter. It says "boundary", which `codebase-design` avoids; see Overlaps. |
| `type-system-discipline` | Static types: branded primitives, sum types, `never`. | Idea only | Lab code is mostly Python, R and bash. Its portable rules, parse at the edge and make illegal states unrepresentable, already live in `boundary-discipline` and `model-the-domain`. |
| `make-operations-idempotent` | Daemons: PID locks, adopting live sessions. | Adopt with edits | Add the Slurm pattern. Preemptible jobs requeue (`lab-hpc`'s arc Slurm reference), so a step writes to a temporary name and renames, and skips outputs that already exist and validate. |
| `migrate-callers-then-delete-legacy-apis` | Internal APIs with no external users. | Adopt as-is | Its own condition covers science: code behind a published result has an external user. |
| `separate-before-serializing-shared-state` | Concurrent writers. | Adopt as-is | Parallel jobs each write their own file and merge at the end. The shared package store is shared state. |
| `prove-it-works` | General. | Adopt as-is | `COMPLETED` in `sacct` is a proxy; read the output values. |
| `fix-root-causes` | General. Restart bugs come from stale state. | Adopt as-is | Stale intermediate files and caches in pipelines. |
| `sequence-verifiable-units` | Sweeps, commits, PRs. | Adopt as-is | One sample through before the batch of hundreds. |
| `test-behavior-not-implementation` | JavaScript matchers (`toBeDefined`, `toHaveBeenCalled`). | Idea only | It duplicates mattpocock `tdd`'s anti-patterns. Fold its test, "would it pass if every call returned None?", into `tdd`. |
| `explain-the-number` | Performance and eval numbers. | Adopt with edits | Add a result-number branch. Before trusting an accuracy, an enrichment or a cell count, rule out leakage between splits, batch confounding, duplicated samples, and a filter that changed the denominator. |
| `guard-the-context-window` | General. | Adopt as-is | Large logs, FASTQ heads, Slurm output. |
| `never-block-on-the-human` | Reversible code work proceeds; irreversible work pauses. | Adopt with edits | Add the lab's always-confirm list: `sbatch`, `srun`, `scancel`, any Edison spend, writes or deletes in the shared package store, wet-lab steps that use samples or reagents. As written it contradicts the repo-wide rule on sbatch. |
| `encode-lessons-in-structure` | General. | Adopt as-is | This repo already works this way; the lint sweeps are the example. |

### poteto-mode playbooks and other pstack files

| Item | Verdict | Where it goes, or why not |
| --- | --- | --- |
| `investigation` | Idea only | liulab-mode Investigation playbook: a read-only, cited answer in `how`'s output shape. |
| `bug-fix` | Skip | mattpocock `diagnosing-bugs` covers it, including the regression test before the fix. |
| `perf-issue` | Idea only | The performance mantras for a slow pipeline: don't do it, do it once, do less, do it later, do it concurrently, do it cheaper. |
| `hillclimb` | Idea only | liulab-mode "Improve a metric": a frozen harness, one change per measurement, keep or revert, a decision log. Fits model training and pipeline tuning. |
| `runtime-forensics`, `trace-forensics` | Skip | CDP traces, heap snapshots, spindumps. Their "load the artifact into sqlite before reading" already lives in `build-the-lever`. |
| `feature` | Idea only | Its throughput checkpoint for parallel work: blocking first steps, independent workstreams, shared state, smallest safe decomposition. |
| `refactoring` | Idea only | liulab-mode "Refactor analysis code": pin the outputs on a fixture first, then prove them identical, or within tolerance, after. |
| `prototype` | Idea only | One rule for liulab-mode: settle an empirical fork by running it, not by asking. mattpocock `prototype` is the skill. |
| `visual-parity` | Skip | Pixel-exact UI equivalence. |
| `authoring-a-skill` | Skip | Built on Cursor `create-skill`. mattpocock `writing-for-agents` and this repo's gate cover it. |
| `eval` | Idea only | Blinding rules for `tests/eval.sh`: no "eval" words, an organic prompt, a judge who sees labels only. The map's fog already names eval coverage. |
| `babysit`, `shipping`, `autopilot-full`, `autopilot-stack`, `orchestrate` | Skip | Merge queues, PR stacks, Cursor cloud agents, Bugbot, the Origin forge, bun scripts. |
| `autonomous-run` | Idea only | liulab-mode "Long run": a checkable exit predicate, and the end of a Slurm job as the wake event. |
| `session-pickup`, `pause-safely` | Idea only | Pausing is a `wip:` commit plus a mattpocock `handoff` note. Picking up reads the trail and redoes nothing. |
| `multi-phase-plan` | Skip | mattpocock `to-spec`, `to-tickets` and `wayfinder` own planning. It also needs `node` for `check-plan.mjs`. |
| `worktree-cleanup` | Skip | iOS simulators and Cursor state. |
| `opening-a-pr` | Skip | mattpocock `pr` wins. One idea: a Scope line saying what the PR leaves out. |
| `agents/poteto-agent.md`, `agents/comment-sicko.md` | Skip | The portable form: tell a plain subagent to read the mode skill first. |
| `automations/benny/` | Skip | Slack triage through Cursor automations. |
| `poteto-mode/references/bugbot-triage.md` | Skip | Cursor Bugbot. |
| `poteto-mode/scripts/` (`orch`, `watch-pr`, `check-plan.mjs`, `bootstrap.ts`) | Skip | TypeScript under bun or node. The lab's runtime dependencies go through pixi. |

## Harness-specific mechanics

None of the rows below was tested in Codex or Kimi Code.
"Upstream says" means a mattpocock or pstack doc claims it; I did not run it.

| Mechanic | Used by | Claude Code | Codex, Kimi Code | Portable equivalent |
| --- | --- | --- | --- | --- |
| Per-role model routing (`pstack-models.mdc`, `grok-*` and `claude-*` slugs) | `setup-pstack`; `how`, `why`, `arena`, `swarm`, `architect`, `interrogate`, `reflect`; code playbooks | Subagents take a model, but only from Anthropic's family (observed). | Unverified. | Drop routing. A second opinion is a fresh subagent with the same prompt. A different vendor means running the review in the other agent by hand. |
| `subagent_type: "poteto-agent"` or `"Comment Sicko"`; Task `readonly`, `environment: "cloud"`, `cloud_base_branch` | `poteto-mode`, `how`, `why`, `swarm`, `no-comments` | Has `subagent_type` on its subagent tool (observed), but not Cursor's `readonly` or cloud parameters. | Unverified. | mattpocock's convention (`.agents/invocation.md`): say "spawn a subagent", say "call the Skill tool with X", and tell the subagent which skill to read first. |
| Cursor custom modes (`mode: true`, `icon`, `color`, `reminder`; option+enter) | `poteto-mode` | None known (unverified). | Unverified. | A user-invoked skill typed at task start, plus a one-line always-on pointer in `templates/CLAUDE-stub.md` and the matching `AGENTS.md`. |
| `/loop` | `autonomous-run`, `babysit`, `visual-parity`, `bug-fix` | Ships a `/loop` skill (observed). | Unverified. | For cluster work the wake event is the job ending: a blocking `sbatch --wait`, or a watcher polling `sacct`, run in the background. |
| `AskQuestion` structured picker | `poteto-mode`, `automate-me`, `setup-pstack` | Has `AskUserQuestion`, per mattpocock's out-of-scope note. | Unverified. | Plain chat questions. mattpocock rejects pickers in `.out-of-scope/native-question-tool.md`. |
| Cursor's built-in `create-skill` | `authoring-a-skill`, `automate-me`, `reflect` | Anthropic's `skill-creator` is installed (observed). | Unverified. | mattpocock `writing-for-agents` plus this repo's gate. |
| `deslop`, `control-ui`, `control-cli` from `cursor-team-kit` | `poteto-mode`, `babysit`, `shipping` | Not shipped (the pstack README says so). | Not shipped. | Not needed. Review is mattpocock `code-review`; the lab's preflights check the machine. |
| Transcript path `agent-transcripts/` under `~/.cursor/projects/` | `automate-me`, `reflect`, `recall`, `eval`, `show-me-your-work` | `~/.claude/projects/<slug>/` (observed). | Codex sessions path unverified. | "This harness's session logs", as mattpocock `retro` words it. |
| Bugbot, agentic security review, the Origin forge, Cursor cloud agents, Grok Bot routines | `babysit`, `shipping`, `autopilot-*`, `make-bot-ui` | None. | None known. | Skip. |
| Multi-model panels: cross-judge, reviewer per family, blinded eval judge | `arena`, `interrogate`, `architect`, `eval` | One vendor only. | Unverified. | Fresh same-model contexts, or a cross-tool run by hand. |
| `paths:` glob trigger; image-generation tool | `typescript-best-practices`; pstack `teach` | Not used by the lab. | Unverified. | Skip. |
| `disable-model-invocation: true` | Every mattpocock user-invoked skill; `lab-edison` | Honoured. | This repo's README says other tools ignore it. mattpocock pairs it with `agents/openai.yaml` setting `policy.allow_implicit_invocation: false` for Codex (`.agents/invocation.md`). Kimi Code unverified. | Ship both files. Side finding: `lab-edison` has no `agents/openai.yaml`, so Codex may trigger it on its own. The README already warns about this. |
| "Call the Skill tool with X" | Every operative mattpocock edge | Has a Skill tool (observed). | Upstream says most harnesses expose one. Unverified. | Keep the wording verbatim. It is mattpocock's harness-neutral phrasing. |
| `claude --bg`; `/clear` and `/compact` by name | in-progress `claude-handoff`; `ask-matt` | Claude Code commands. | Unverified. | The phase-boundary advice carries; the command names do not. |
| Background subagents and worktrees | `research`, `implement-spec`, `code-review` | Available (observed). | Unverified. | Degrade to sequential foreground work. |

## Cross-reference graph

An *operative* edge is a step that runs another skill now ("call the Skill tool with X") or tells the user to run one.
Router prose (`ask-matt`, `poteto-help`, READMEs) only names skills and is left out.

**mattpocock**, from the skill bodies:

- `wayfinder` → `grilling`, `domain-modeling`, `research`, `prototype`. Tells the user to run `setup-matt-pocock-skills`, and reads the "Wayfinding operations" section of the tracker doc that setup writes.
- `grill-with-docs` → `grilling`, `domain-modeling`. `grill-me` → `grilling`.
- `triage` → `grilling`, `domain-modeling`; setup for labels; reads `.out-of-scope/`.
- `improve-codebase-architecture` → `codebase-design`, `grilling`, `domain-modeling`.
- `implement` → `tdd`, `code-review`. `implement-spec` → `tdd`, `code-review`, plus setup.
- `tdd` → `codebase-design`, and hands refactoring to the `code-review` stage.
- `retro` → `writing-for-agents` on every run (`.out-of-scope/lazy-load-writing-for-agents.md`).
- `to-spec`, `to-tickets`, `code-review` → setup, for the tracker.
- `handoff` → names whatever skills the next session needs.
- **Glossary readers.** Ten skills read the repo glossary by the name `GLOSSARY.md`: `ask-matt`, `codebase-design` (DESIGN-IT-TWICE), `diagnosing-bugs`, `domain-modeling`, `improve-codebase-architecture`, `pr`, `setup-matt-pocock-skills`, `tdd`, `triage`, `wait-what` (verified by grep).

**Closure.** Adopting `wayfinder` pulls in setup, `research`, `prototype`, `grilling` and `domain-modeling`.
The implement pair pulls in `tdd`, `code-review` and `codebase-design`.
Skipping `wizard` and folding `ask-matt` breaks no operative edge, only router labels.

**pstack**, from the skill bodies:

- `poteto-mode` → `how`, `why`, `architect`, `arena`, `swarm`, `interrogate`, `unslop`, `technical-writing`, `no-comments`, `benchmark-checklist`, `show-me-your-work`, `figure-it-out`, `tdd`, all 24 principles, its 23 playbooks, `poteto-agent`. Outside pstack it calls `deslop`, `control-ui`, `control-cli`, `create-skill` and Cursor's `/loop`.
- `figure-it-out` → poteto-mode's principles section, `architect`, `arena`, `show-me-your-work`.
- `architect` → `how`, `why`, `arena`, `interrogate`. `arena` → four principles.
- pstack `teach` → `how`, `why`, `unslop`. `recall` → `why`, the session-pickup playbook, `unslop`. `ketchup` → `bro`.
- `blast-radius` → `how`, `why`, `arena`, `unslop`. `no-comments` → Comment Sicko, `how`, `why`, `architect`.
- `automate-me` → `create-skill`, `unslop`, and `poteto-mode` as its model. `reflect` → `create-skill`.
- `technical-writing` → `unslop`. `show-me-your-work` → `unslop`, `encode-lessons-in-structure`.
- `benchmark-checklist` → the Opening a PR, Perf issue and Hillclimb playbooks. `setup-pstack` → `create-verification-skill`, which pairs with `maintain-verification-skill`.
- Among the principles: `attack-the-premise` → `build-the-lever`, `fix-root-causes`, `laziness-protocol`, `redesign-from-first-principles`. `build-the-lever` → `laziness-protocol`, `encode-lessons-in-structure`, `prove-it-works`. `explain-the-number` → `benchmark-checklist`, `prove-it-works`. `minimize-reader-load` → `guard-the-context-window`. `prove-it-works` → `show-me-your-work`. `sequence-verifiable-units` → `prove-it-works`, `build-the-lever`. `type-system-discipline` → `typescript-best-practices`, `boundary-discipline`.

**Closure of the recommended pstack set.** `unslop` and `technical-writing` close on each other.
`show-me-your-work` needs `unslop` and `encode-lessons-in-structure`.
`benchmark-checklist` and `explain-the-number` point at each other; repoint the PR edge to mattpocock `pr`.
`ketchup`'s edge to `bro` is repointed to `unslop`.
The 22 kept principles close, because only `typescript-best-practices` points at `type-system-discipline` and nothing points at `test-behavior-not-implementation`.

**Two mechanism caveats (judgement).**

1. **Principles are user-invoked.** In Claude Code no skill can call a user-invoked skill (mattpocock `.agents/invocation.md`).
   `poteto-mode` gets around this by telling the agent to read each leaf file by path.
   The lab can ship the principles as reference pages inside liulab-mode, read by path, which works in any agent.
   Or it can make them 24 model-invoked skills, which adds 24 descriptions to every listing. I would take reference pages.
2. **Names are edges.** Every operative edge names its target ("grilling"), and wayfinder's labels are `wayfinder:*`.
   `AGENTS.md`'s naming policy says internal names are `lab` or `lab-*`.
   Renaming adopted skills to `lab-*` rewrites nearly every file, which is a lab edit everywhere.
   Keeping upstream names needs a stated exception to the policy. I would keep the names.

## Overlaps and which side wins

| Overlap | Winner (judgement) | What the other side contributes |
| --- | --- | --- |
| `tdd` (both) | mattpocock. It has seams and anti-patterns, and `implement` calls it. | pstack's "closest executable check when a test is impractical". |
| `teach` (both, same name) | mattpocock. Multi-session learning fits onboarding new lab members. | Nothing required. pstack's build-the-diagram-up rule could go into liulab-mode's reply rules. |
| `unslop` vs `avoid-ai-writing` | `unslop`. It is the maintainer's pick, shorter, and its stable rule numbers let other skills cite it. | The venue and voice rule ("do not impose a casual style on grant proposals"), the second-pass audit, and tiered word flags that cut false positives. |
| pstack principles vs `codebase-design` | Both stay. `codebase-design` owns module-shape words (module, interface, seam, depth); the principles own when-to-apply rules. Both draw on Ousterhout and agree. | One word clashes. `codebase-design` avoids "boundary", but `boundary-discipline` uses "system boundary" for where outside data enters. Settle it in liulab-mode's principles index: a system boundary is where outside data enters; for module shape, say seam. |
| `DESIGN-IT-TWICE` vs `architect`, `arena`, `exhaust-the-design-space` | mattpocock. | `exhaust-the-design-space` stays as the rule that triggers it. |
| `code-review` vs `interrogate`, `no-comments`, `blast-radius` | mattpocock. | `blast-radius`'s proven safety fact moves into `pr`'s Merge Danger. |
| `diagnosing-bugs` vs the `bug-fix` playbook and `fix-root-causes` | The skill and the principle together; they do not conflict. | Nothing. |
| `retro` vs `reflect`, `correct`, `self-improvement` | mattpocock `retro`. | `correct`'s enforcement ladder and rule table. |
| `handoff` vs `pause-safely`, `session-pickup`, `recall` | mattpocock `handoff`. | A `wip:` commit on pause, and `recall`'s brief contract on pickup. |
| `wait-what` vs `bro` | mattpocock. | Nothing. |
| `pr` vs `opening-a-pr` | mattpocock. | A Scope line. |
| `research` vs `why`, `how`, `recall` | mattpocock `research` for outside facts. | `why`'s confidence tiers. |
| `writing-for-agents` vs `authoring-a-skill` and Cursor `create-skill` | mattpocock. | Nothing. |
| `to-spec`, `to-tickets`, `wayfinder` vs `multi-phase-plan`, `orchestrate` | mattpocock. The pstack README says "i don't believe in planning". | Nothing. |
| `domain-modeling` vs `model-the-domain` | Both stay. One shapes words (glossary, ADRs); the other shapes data structures in code. | The names are close; liulab-mode's index should say which is which. |
| `technical-writing` vs `docs/agents/writing.md` | Both stay. Vale enforces this repo's caps and jargon list; `technical-writing` is the style for human docs, READMEs and protocols. | Nothing. |

## liulab-mode

**What it is (judgement).** A user-invoked lab skill that matches a task to a playbook and states the lab's working rules.
It serves the whole lab, so it holds lab policy, plus the maintainer's style wherever that style is lab policy.
That is a change from `automate-me`, which drafts one person's mode.

**From `poteto-mode`, take the shape.**

1. **A trigger table** ("Non-negotiables"): situation → skill. Draft lab rows:
   - Cluster work goes to `lab-hpc` first, and refuses if the preflight fails.
   - A number you will report goes to `explain-the-number`, plus `benchmark-checklist` for a speed claim.
   - Any prose goes to `unslop`.
   - A literature fact goes to `research`; Edison only on request.
   - A foggy multi-session effort goes to `wayfinder`.
   - A change to analysis code pins the outputs on a fixture first.
2. **An inline principles index.** One line per principle with its trigger, and the leaf page read on demand.
   The reply names each principle that changed a decision.
3. **An autonomy section.** Reversible work proceeds without asking.
   The always-pause list is the lab's: `sbatch`, `srun`, `scancel`, Edison spend, the shared package store, force-push, deleting data, messages to people outside the session, wet-lab steps.
   Keep "No is an acceptable answer".
4. **Reply rules.** Short declarative sentences. Frame the impact for whoever uses the result.
   Every claim carries its evidence or a label (measured, inferred, guess), mapped onto verified, read and unverified.
   Never fabricate a link or a citation; invented references are the science failure mode.
5. **A playbook router.** Copy the matched playbook's steps into the todo list verbatim, and keep a skipped step with its reason.
   The lab playbooks come from the ideas above:
   - Investigation.
   - Analysis: plan, fixture, full run, figure.
   - Long run: exit predicate, job-end wake, decision log.
   - Improve a metric.
   - Refactor analysis code.
   - Pause and pickup.
   - A fallback from `figure-it-out` for when nothing fits.
6. **Subagent rules.** A fresh subagent for each new piece of work, with the consolidated scope. You own its output and review it before reporting.

Leave behind the mode frontmatter, model routing, `poteto-agent`, `cursor-team-kit`, Bugbot, Origin, the PR-stack playbooks, Conventional Commits and the TypeScript scripts.

**From `automate-me`, take the method.**

1. Mine recent transcripts in three slices with parallel subagents, and keep only patterns seen in two or more slices.
   Claude Code keeps them under `~/.claude/projects/`; the Codex path is unverified.
2. Fill gaps in intent by asking the user in plain chat.
3. Cluster findings into its sections: response style, autonomy, understand first, subagents, prose and code, review and verify, process, skills. Drop any section with no rule that differs from the default.
4. Keep its guardrails. Don't overfit to one conversation. Reference skills by name instead of inlining them. Keep sections minimal. Write "the user", not a first name. Make it user-invoked by default.
5. Update mode mines only the history since the skill's last commit.

**Lab caution.** Transcripts hold hostnames, usernames and ssh output.
Keep the mining summaries local, and run the draft through the no-secrets sweep before it lands in this public repo.

**Delivery.** I know of no Claude Code equivalent of a Cursor custom mode (unverified).
The portable "always on" is a one-line pointer in `templates/CLAUDE-stub.md` and the matching `AGENTS.md` line for Codex and Kimi Code (unverified), plus `/lab:liulab-mode` typed at the start of a task.

## Non-upstream skills

| Skill | What it is | Fate (judgement) | Reason |
| --- | --- | --- | --- |
| `avoid-ai-writing` (`~/.agents/skills/`, from ClawHub, v3.0.0) | An AI-tell audit: 30 categories, a tiered 103-word table, a four-part output, a second pass. The local `SKILL.md` looks locally edited: it is newer than the bundled README and adds a grant-proposal voice rule (inferred). | Absorb into the lab's `unslop`, then retire | It does the same job as `unslop`. Its venue rule and second-pass audit are what `unslop` lacks. Carry the maintainer's local wording across. |
| `self-improvement` (`~/.claude/skills/`, from pskoett-skills) | `.learnings/` logs with web area tags (frontend, backend). Promotes "aggressively" to `CLAUDE.md`. Hooks inject a reminder on every prompt. Pairs with `self-healing`, OpenClaw and Copilot. | Retire | It overlaps mattpocock `retro` and the harness's own memory. "Promote aggressively" contradicts `writing-for-agents` and this repo's word caps. The hook costs tokens on every prompt. Its recurrence threshold is already covered by `correct`'s "a class counts once it has happened twice". |
| `find-skills` (`~/.agents/skills/`, from skills.sh) | Searches and installs skills with `npx skills add -g -y`. Web-development examples. | Retire | It is model-invoked on "how do I do X", which matches every science how-to question. It installs unvetted third-party skills globally and skips confirmation, against the one-install-path goal. Finding new skills is a maintainer task. |

## Open points for other tickets

- **Glossary name.** Rename `CONTEXT.md` to `GLOSSARY.md`, or carry the same edit in ten skills.
  A rename touches conformance rule 4 (`scripts/conformance.py`), `pyproject.toml`, `tests/lint.sh` and `docs/agents/domain.md`.
  I lean toward the rename.
- **Naming policy.** Keep upstream skill names, which needs an exception to `lab-*`, or rename and rewrite every edge.
- **Principles packaging.** 24 skills, or reference pages inside liulab-mode.
- **Codex invocation.** Add `agents/openai.yaml` to `lab-edison` and to every lab user-invoked skill, if Codex behaves as mattpocock's ADR says.
  `.agents/adr/0002-ship-as-a-claude-code-plugin.md` also records that Codex drops symlinks on install, which bears on the install path.
- **Kimi Code.** Every Kimi Code cell here is unverified. The install-path ticket should check how Kimi Code reads skills and frontmatter.
