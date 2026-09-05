---
search:
  exclude: true
---

# CalVer in the manifest, and marketplace updates stay manual

The `version` in `.claude-plugin/plugin.json` is CalVer `YYYY.M.PATCH` — year, month
written without a leading zero, then a counter that increments per release within the month
and resets when the month changes. It is bumped in the same commit as its `CHANGELOG.md`
entry. Installed machines pick a release up only when someone runs
`claude plugin marketplace update liulab`.

## Why CalVer

What ships here is prose an agent reads, not an API anything links against. There is no
breaking change to signal, so semver's three numbers would be a compatibility claim nobody
can evaluate: a rewritten safety rule is a larger change than a new skill, and semver has
no way to say so. A date says the only thing a reader of an installed copy actually needs —
how old it is.

The month is written without a leading zero because semver parsers reject `2026.07.0`, and
the plugin manifest is read by one. The patch counter resets with the month so the number
stays short and its meaning stays obvious.

## Why updates stay manual

Background auto-update of a marketplace needs a `GITHUB_TOKEN` present on every machine
that installs the plugin. Handing one out to each lab machine, and keeping it valid, costs
more than the thing it buys: a Markdown skill that is one release behind still gives
correct cluster advice, because the facts in it were true when they were verified.

## What it costs

A machine can silently run an old copy, and nothing here can tell. Two consequences worth
knowing:

- **Evals hit the installed plugin, not the working tree.** Push and run
  `claude plugin update lab-compute@liulab` before `tests/eval.sh`, or you are testing the
  previous release. Plain `install` does not upgrade in place.
- **A fix to a safety rule does not propagate on its own.** If a release changes one, say
  so where people will see it, rather than assuming the version number carries it.
