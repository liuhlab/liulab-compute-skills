# 8. The version identifies the content, so every shipped change bumps it

Date: 2026-09-05

## Status

Accepted.

## Context

`.claude-plugin/marketplace.json` declares `source: "./"`, so the repo root is the plugin
and `claude plugin update` clones the whole tree. Tests, docs, styles and tooling are all
installed alongside the skills. Nothing is held back.

The release flow said to bump when skills change. That reads as a rule about user-facing
behaviour, and under `source: "./"` it is not one: a test-only change ships too. Twice in
one afternoon a pull request merged with no bump, and the result was two commits declaring
`2026.9.3` with different bytes — one in the plugin cache, one on `main`. Asking which
version a machine ran stopped answering what it had.

The alternative considered was to keep bumping for skills alone and write down that the
version tracks behaviour while the commit identifies content. It is less churn and it is
honest, but it leaves the number ambiguous by design, and a version that cannot be compared
is a poor thing to put in a changelog. Excluding paths from what ships was not available to
check at the time.

## Decision

A version names one tree. Every change that merges to `main` bumps the patch, whether it
touched a skill, a test or a comment.

`tests/lint.sh` enforces it: if a tag `v<version>` exists, this tree must be identical to
it. An un-tagged version is an unreleased bump and passes. A tagged one that has moved
fails and names the files that moved. CI checks out with full history so the rule has tags
to read, and treats a missing tag list as a failure rather than a pass.

## Consequences

CalVer patch numbers climb faster, and the changelog gains entries for changes no lab
member can observe. That is the cost of the number meaning something.

A release is no longer a judgement call about significance, which is what made it skippable.
The changelog stops being a list of interesting changes and becomes a log of releases, so an
entry may honestly read "test fixtures only".

Reverting means deleting one check and this record. The tags already cut keep their meaning
either way, which is what makes this cheap to undo.
