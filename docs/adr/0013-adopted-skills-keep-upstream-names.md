---
search:
  exclude: true
---

# Adopted skills keep their upstream names

An adopted skill keeps the name upstream gave it, typed bare: `/grilling` in Claude Code
and Kimi Code, `$grilling` in Codex. A `lab-*` name marks a skill the lab wrote or derived,
and an adopted skill never takes one, tracked or forked. The one exception is the mode,
`hq-mode`. Lint admits a name outside `lab-*` only when the repo records the skill as
adopted, in the pin's name map when tracked or its attribution record when forked, or when
the name is `hq-mode`. Nothing in the repo writes `lab:` in front of a skill.

## Why upstream names

Upstream skills name each other in their text: `wayfinder` names `grilling`, `research` and
`prototype`. A `lab-` rename would re-apply a `name:` edit and every one of those references
on every sync, and a rename adds no capability, so it breaks the edit rule of ADR 0012.
Forking changes who owns a skill and not its name, because tracked skills still call it by
that name. The name map renames an upstream skill only if one arrives with a name that
clashes.

## Why the mode is `hq-mode`

It follows pstack's `<handle>-mode` convention, the one `poteto-mode` uses; the maintainer
chose it. Its text says "the user", never "hq", so any lab member who types `/hq-mode` gets
the working style applied to their own work.

## What it costs

- The `lab:` prefix guaranteed reaching the lab copy. A bare name reaches whichever skill
  holds it, so a stale user-level copy shadows the plugin's in all three agents without a
  word. `/lab-setup` reports such copies and removes none.
- In Kimi Code a repo's skill silently replaces the lab's copy of the same name. Conformance
  rule 6 widens from "no `lab-` prefix" to "no name the plugin ships".

## What this changes

ADR 0001 named the plugin `lab` because "the plugin name is the prefix people type". That
reason is gone; the decision stands, and the plugin keeps the name. The naming policy in
`AGENTS.md`, "internal names are `lab`/`lab-*`", narrows to skills the lab wrote or derived.
ADRs 0004 and 0008 stand.
