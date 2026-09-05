---
search:
  exclude: true
---

# Domain docs

**Single-context**: one `CONTEXT.md` and one `docs/adr/`, both at the repo root.

Before changing anything, read `CONTEXT.md` for the vocabulary and any decision record
covering the area you are about to touch. If either is missing, proceed silently —
`/domain-modeling` creates them lazily, when a term or a decision is actually resolved.

Use the glossary's words. When your output names a domain concept — an issue title, a
commit message, a line of a skill — use the term as `CONTEXT.md` defines it, not a synonym.
A concept defined nowhere is a signal: usually language this repo does not use,
occasionally a real gap.

If your output contradicts a decision record, say so rather than quietly overriding it.

## What goes where

`CONTEXT.md` is a glossary and nothing else — no procedure, no cluster fact, no scratch
notes. A decision record is written only when a decision is hard to reverse, surprising
without its context, and the result of a real trade-off. All three, or no record.

This repo has a fourth home the template does not, and it takes most of the traffic:

| The fact | Where it lives |
| --- | --- |
| What a term means | `CONTEXT.md` |
| A decision and its trade-off | `docs/adr/` |
| How a cluster behaves | `skills/lab-hpc/references/` |
| A repeatable procedure | the task-recipe skill that owns it |
| How the repo is worked on | `AGENTS.md` |
| What is still open | a GitHub issue |

**A cluster fact is not a decision.** Partition names, Slurm versions, which nodes reach
the internet — those are observations, and they belong in a reference page, verified on the
cluster and dated. Nobody decided them and they change without anyone here agreeing to it.
Writing one into a record freezes an observation in the one place that is never re-checked.

Both `CONTEXT.md` and `docs/adr/` are agent-facing and capped — see `writing.md`. Both are
also published, unlisted, so the repo's no-secrets policy applies to every word of them.
