---
search:
  exclude: true
---

# The version names one tree, so every merged change bumps it

Every change that merges to `main` bumps the patch in `.claude-plugin/plugin.json` —
whether it touched a skill, a test or a comment. `tests/lint.sh` enforces it: if a tag
`v<version>` exists, this tree must be identical to it. An untagged version is an
unreleased bump and passes; a tagged one that has moved fails and names the files that
moved.

## Why every change and not just skills

The release flow used to say bump when skills change. That reads as a rule about
user-facing behaviour, and under `source: "./"` it is not one. The repo root is the plugin,
so `claude plugin update` clones the whole tree — tests, docs, styles and tooling all
install alongside the skills. Nothing is held back, so nothing is exempt.

Left as a habit it failed inside a day. `2026.9.3` was tagged, two test-only pull requests
merged on top, and the plugin cache and `main` both answered `2026.9.3` with different
bytes. Asking which version a machine ran had stopped answering what it had.

## Why not keep the number loose

The alternative was to bump for skills alone and write down that the version tracks
behaviour while the commit identifies content. Less churn, and honest as far as it goes,
but it leaves the number ambiguous on purpose — and a version that cannot be compared is a
poor thing to print in a changelog or ask a lab member for. Excluding paths from what ships
would remove the problem at its root; whether the plugin format allows it was not
established, and a rule resting on an unchecked assumption is what produced this.

## What it costs

Patch numbers climb faster, and the changelog gains entries no lab member can observe. An
entry may honestly read "test fixtures only". That is the price of the number meaning
something.

In exchange a release stops being a judgement call about significance, which is exactly
what made it skippable.

Undoing this is deleting one check and this file. Tags already cut keep their meaning
either way, which is what makes it cheap to reverse.
