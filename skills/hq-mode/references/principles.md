---
search:
  exclude: true
---

# Principles

Read a principle's page in full before you apply it: `references/principles/<name>.md`. Each
entry says when it applies. Pages marked *lab edit* carry a science change from the bias pass,
provisional until that review settles. Forked from pstack's `principle-*` skills (MIT).

A **system boundary** is where outside data enters. For the shape of a module, say **seam**
(`codebase-design`'s word).

## Core

- **laziness-protocol.** Sizing a diff, or tempted by a new layer. The smallest change that
  solves it; bias to deletion.
- **foundational-thinking.** Before writing logic: the data shape, scaffold before feature,
  what concurrent jobs share.
- **redesign-from-first-principles.** A new requirement in an old design. Redesign as if it had
  been there from day one.
- **attack-the-premise.** Two fixes that share a premise have both failed. Break the result down
  per sample and per batch, then question the premise.
- **subtract-before-you-add.** Remove dead weight first, then build on the simpler base.
- **minimize-reader-load.** Code that is hard to trace. Fewer layers, less hidden state.
- **outcome-oriented-execution.** A planned rewrite or migration. Converge on the target; no
  throwaway compatibility states.
- **experience-first.** Who consumes the work: a bench user, a colleague importing the package.
  Choose their experience over your convenience.
- **exhaust-the-design-space** (*lab edit*). A decision with no precedent: compare 2 or 3
  options. For an analysis choice, fix the criterion before seeing results and report every
  option tried.
- **build-the-lever.** Non-trivial work. Build the script that does or proves it, not by hand.

## Architecture

- **model-the-domain** (*lab edit*). Logic that branches a lot or repeats a shape. Encode the
  domain in a structure. Stages that checkpoint to disk stay; their shared rules go in one
  module.
- **boundary-discipline** (*lab edit*). Validation and error handling. Guard at system
  boundaries. A number a step can silently change (row counts, NA counts, ranges) is a result
  check: assert it at that step.
- **make-operations-idempotent** (*lab edit*). Steps that rerun after a crash or a requeue.
  Write to a temporary name, then rename; skip an output only if it exists and validates; a
  lock names its host and job.
- **migrate-callers-then-delete-legacy-apis.** A new internal API with old callers. Migrate and
  delete in one change.
- **separate-before-serializing-shared-state.** Jobs or agents that might write the same file.
  Remove the sharing first: per-job outputs.

## Verification

- **prove-it-works.** Before saying done. Check the real artifact, not a proxy.
- **fix-root-causes.** Debugging. Reproduce first; ask why until you reach the cause.
- **sequence-verifiable-units** (*lab edit*). Multi-step work. Small units, each ending in a
  check. When each unit is a long batch job, prove one as a pilot, then run the rest
  concurrently and check each as it finishes.
- **explain-the-number** (*lab edit*). Before you trust or report a number. For a performance
  number, name what bounds it. For a result number, rule out leakage, batch confounding,
  duplicated samples and a changed denominator.

## Delegation

- **guard-the-context-window.** Large outputs, long files, fan-out. Bulk goes to subagents;
  summaries stay here.
- **never-block-on-the-human.** Tempted to ask "should I?" about reversible work. Proceed and
  report. The always-pause list in `working-style.md` overrides this page.

## Meta

- **encode-lessons-in-structure.** You are writing the same instruction twice. Make it a lint, a
  check or a script.
