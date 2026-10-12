---
search:
  exclude: true
---

# Upstream skills merge from a pin, and pstack is only reviewed

The lab follows two upstreams. mattpocock/skills is **merged**: the repo stores a pin, the
upstream commit last synced plus a map from upstream name to lab name, and a sync merges
each file of a tracked skill into the flat copy at `skills/<name>/` with `git merge-file`,
the pin as base and upstream's tip as theirs. No copy of upstream is stored. cursor/plugins
`pstack` is **reviewed**: it has a pin of its own, and every item the lab takes from it is
forked from day one.

Every adopted skill is tracked or forked. A tracked skill is merged on every sync; its
upstream text changes only by a lab edit, which adds a capability. A new section goes in a
lab-only side page with a one-line pointer; a branch or a loop path goes in place. A forked
skill is lab-owned and leaves the pin; upstream changes to its original arrive as ideas,
ported by hand. Every mattpocock skill starts tracked; the maintainer forks one when merging
it costs more than it saves, by judgement and no threshold.

The sync is a maintainer-only command in `.claude/commands/`, not shipped, run by hand about
monthly. One run merges, reports conflicts, deletions, stale words and dropped edits,
summarises what is new in both upstreams, and opens one pull request: one version under
ADR 0008.

## Why a pin and a per-file merge

Replayed over upstream's last 2.5 months, every git mechanism gave the same conflicts where
texts overlapped; moves, deletions and renames told them apart. The per-file merge finds a
skill by name, so a bucket move costs nothing and a deletion is reported. `npx skills update`
silently wiped lab edits. A pin ships nothing extra under `source: "./"`, and if upstream
rewrites history, that sync falls back to a two-way diff.

## Why pstack is only reviewed

Nothing the lab takes from pstack arrives unchanged. Its principles become reference pages
and its other items lose text, such as Cursor paths, and a tracked skill may only gain text. Most of its churn cuts tokens for frontier models in Cursor, and the lab runs
other agents on other models, so those cuts are read, not absorbed.

## What it costs

- A lab edit's only record is the diff against the pin, with its reason in the commit
  message and the changelog.
- An upstream rename is a deletion plus a new skill, and its lab edits are ported by hand.
- Every sync needs the maintainer.

ADRs 0001, 0004 and 0008 stand.
