---
name: hq-mode
description: hq's way of working for lab science and code - research facts instead of asking, count questions and lead with a recommendation, orchestrate subagents, verify on real data, finish with nothing open, plain words for biologists. Playbooks for an analysis, a cluster run, a figure, a paper or grant section, a talk, an experiment plan. Use for /hq-mode, or to work in hq's style.
disable-model-invocation: true
---

# hq mode

Read [references/working-style.md](references/working-style.md) in full before the first tool
call. It holds the rules every turn follows: asking, autonomy and the always-pause list,
delegation, and the reply. Then match the task below.

## Triggers

- Any question for the user → the asking rules first. A fact is never the user's to answer.
- An idea in a repo → `/grill-with-docs`. Too big for one session → `/wayfinder`. Settled →
  `/to-spec` → `/to-tickets` → the **Land the tickets** playbook. Never build inside a grill,
  spec or research session: the user types the next step.
- Something broken → `/diagnosing-bugs`. Raw issues arriving → `/triage`.
- A cluster, ssh, Slurm, GPU → `lab-hpc` before the first ssh. Notebooks → `lab-jupyter`.
  Containers → `lab-containers`. Edison runs only when the user types `/lab-edison`.
- A number you measured or will report → **explain-the-number** and
  [references/benchmark-checklist.md](references/benchmark-checklist.md).
- Any prose a person reads → `unslop` as the last pass. Docs, READMEs, PR bodies →
  `technical-writing`.
- A correction from the user → write it down at once where it lasts: the repo's `AGENTS.md`,
  the skill, or memory. Then ask what would stop it recurring.
- Work the user steps away from → a decision trail per
  [references/show-me-your-work.md](references/show-me-your-work.md).
- The end of any playbook → **Close the session**.

## Principles

[references/principles.md](references/principles.md) indexes the principles, each with when it
applies. Read a principle's page in full before you apply it, and name it in the reply.

## Playbooks

Copy the matched playbook's steps into the todo list, verbatim, before any task todos. A step
you skip stays with `skip: <reason>`. Each lives at `references/playbooks/<name>.md`.

### Science

- **analysis**: a question answered from data, ending in a checked number or figure.
- **cluster-run**: a pipeline or job array on a lab cluster.
- **method-research**: explain or compare an experimental method from its papers.
- **experiment-plan**: a plan, proposal page set or timeline for bench or compute work.
- **figure**: a data figure, schematic or illustration.

### Writing

- **paper-section**: a manuscript section, abstract, cover letter or co-author round.
- **grant-section**: a proposal section, a form or a CV within word limits.
- **talk**: a deck, its script, or a recorded talk.
- **review-a-document**: review the user's own document without editing it.
- **message**: polish a message the user drafted.

### Code

- **land-the-tickets**: build a set of tickets through subagents and land them.
- **improve-a-metric**: one change, one measurement, keep or revert.
- **refactor-analysis-code**: pin the outputs first, prove them unchanged after.
- **investigation**: a read-only question. Change nothing.

### Any

- **long-run**: a task driven to a checkable predicate without stopping.
- **close-the-session**: nothing open when the session ends.

No playbook fits → [references/playbooks/figure-it-out.md](references/playbooks/figure-it-out.md)
designs one.

## Attribution

Shape and principles derived from pstack's `poteto-mode` (MIT, cursor/plugins). The flow is
mattpocock/skills' `ask-matt` (MIT).
