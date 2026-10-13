---
search:
  exclude: true
---

# Domain docs

**Single-context**: one `GLOSSARY.md` and one `docs/adr/`, both at the repo root.

Before changing anything, read `GLOSSARY.md` for the vocabulary and any decision record
covering the area you are about to touch. If either is missing, proceed silently —
`/domain-modeling` creates them lazily, when a term or a decision is actually resolved.

Use the glossary's words. When your output names a domain concept — an issue title, a
commit message, a line of a skill — use the term as `GLOSSARY.md` defines it, not a synonym.
A concept defined nowhere is a signal: usually language this repo does not use,
occasionally a real gap.

If your output contradicts a decision record, say so rather than quietly overriding it.
A record whose detail went stale, such as a path that moved or a claim about another agent that
proved wrong, is amended in place, and the commit message says so. A reversed decision gets a
new record whose "What this reverses" section names the old one, which stays as written.

## What goes where

`GLOSSARY.md` is a glossary and nothing else — no procedure, no cluster fact, no scratch
notes. A decision record is written only when a decision is hard to reverse, surprising
without its context, and the result of a real trade-off. All three, or no record.

This repo has a fourth home the template does not, and it takes most of the traffic:

| The fact | Where it lives |
| --- | --- |
| What a term means | `GLOSSARY.md` |
| A decision and its trade-off | `docs/adr/` |
| How a cluster behaves | `skills/lab-hpc/references/` |
| A one-line cluster tip | a bullet in `lab-hpc` |
| How a vendor platform behaves | the owning skill's `references/`, under a provenance block |
| A repeatable procedure | the task-recipe skill that owns it |
| How the repo is worked on | `AGENTS.md` and the pages its read-next table names |
| What is still open | a GitHub issue |

A recipe never repeats a cluster fact; it points at the reference page
(`docs/adr/0002-facts-vs-recipes.md`).

**A cluster fact is not a decision.** Partition names, Slurm versions, which nodes reach
the internet — those are observations, and they belong in a reference page, verified on the
cluster and dated. Nobody decided them and they change without anyone here agreeing to it.
Writing one into a record freezes an observation in the one place that is never re-checked.

**A vendor fact is not a decision either**, and it is weaker than a cluster fact: the vendor
changes it, and the only place several of them can be observed costs money to reach. So it
carries its tier as well as its date — see `GLOSSARY.md` on the provenance block, and
`docs/adr/0009-facts-carry-their-provenance.md` for why three tiers and not more.

Both `GLOSSARY.md` and `docs/adr/` are agent-facing and capped — see `writing.md`. Both are
also published, unlisted, so the repo's no-secrets policy applies to every word of them.

## Writing a fact down

A fact in a reference page is checked and dated, never written from memory. A cluster fact is
re-checked with read-only commands from a compute node, the only place several of them can be
seen at all. A vendor fact carries its provenance block too, and lint fails a `lab-edison`
reference page without one.

**Record configuration, never measurements.** Configuration is what an agent must type: a
partition's wall limit, `MaxNodes`, `DefaultTime`, a port, a module name, the topology. A
measurement is free space, a percentage, node states, a queue wait, a timing or a count of
images. It is true for one afternoon and a confident lie after, and the agent cannot tell
which. Write the guidance it stood for and the command that gives a live value
("`/large_storage` fills up, check `df -h`", not "81% used"). A version is configuration when
behaviour depends on it (Slurm 18.08 is why ircbc needs `squeue -u $USER`), and a measurement
otherwise. The rule holds for the README and the site pages too.
