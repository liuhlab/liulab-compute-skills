---
search:
  exclude: true
---

# Cluster facts live in the core skill; procedures live in recipe skills

`lab-hpc` is the core skill and holds the foundational facts: which cluster is which, the
safety rules, and the per-cluster reference pages under `references/`. `lab-jupyter` and
`lab-containers` are task-recipe skills: one repeatable procedure each, with their own
trigger vocabulary. A recipe builds on `lab-hpc` and never repeats a cluster fact — it
points at the reference.

New content is routed by what it is, not by who needs it:

| The content | Where it goes |
| --- | --- |
| A cluster fact | `skills/lab-hpc/references/` |
| A repeatable multi-step procedure | its own `lab-*` skill |
| A one-liner | a bullet in `lab-hpc` |

## Why

A cluster fact copied into two skills goes stale in one of them, and nothing in the gate
can tell which copy is right. Lint proves a file is well-formed; it cannot know that
`squeue --me` does not exist on Slurm 18.08. The two clusters differ sharply — arc runs
modern Slurm with cost and queue tiers, ircbc runs Slurm 18.08 with no internet on its
compute nodes — so a fact that drifted is not a stale sentence, it is an agent issuing a
wrong command against a real cluster.

The two kinds of content also change for different reasons and on different evidence. A
fact is re-verified with read-only commands on a login node and carries a date. A procedure
changes when a step or a flag changes, and is tested by an eval case. Keeping them apart
means each is edited against the evidence that can actually settle it.

## What it costs

A recipe reads as incomplete on its own: an agent has to follow a pointer to `lab-hpc`
before it can act. That is accepted because `lab-hpc`'s description makes it load first and
its step 0 runs before anything else — the pointer is followed in practice, not in theory.

The routing table is also a judgement call at the margin, and a one-liner that keeps
growing eventually wants to become its own skill. Move it when it does; do not let the
table's third row become where procedures accumulate.
