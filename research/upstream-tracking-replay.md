# Replaying upstream's last 2.5 months through each tracking mechanism

Ticket #64, map #62. Written 2026-10-10. Every claim carries a tier:
**(verified)** means I ran it, **(read)** means I took it from source code or docs, and
**(unverified)** means I inferred it.

## Answer

Track upstream with a pinned pristine copy and a per-file `git merge-file` into the lab
copy. Where lab text and upstream text truly overlap, every git mechanism gives the same
conflicts: one hunk for mattpocock/skills in this window, three for pstack. The mechanisms
differ in how moves, deletions and file renames show up, and in whether a reader can see
what the lab changed. `npx skills update` is ruled out: it deletes local edits without a
word.

Lab edits: six in three mattpocock skills (`domain-modeling`, `wizard`,
`resolving-merge-conflicts`), three in two pstack skills (`how`, `poteto-mode`).

| Mechanism | mattpocock conflicts | pstack conflicts | Bucket move (`wizard`) | Deletion (`resolving-merge-conflicts`) | Lab delta readable as | Fits this repo |
| --- | --- | --- | --- | --- | --- | --- |
| 0. `npx skills update` | none: edits **wiped** | (not run) | relocated by name, edits wiped | warns, keeps the orphan | nothing (no record) | no |
| 1. Fork + merge | 4 files: 2 content (3 hunks, 2 of them in `plugin.json`), 2 modify/delete | 3 hunks | modify/delete (similarity 48% < 50%), clean only with `-X find-renames=40%` | modify/delete | `git diff upstream...main` | separate repo and plugin, or 9 root conflicts |
| 2a. Subtree, whole upstream | 3 files: 1 hunk, 2 modify/delete | (unverified: as 1) | modify/delete; no `-X` passthrough | modify/delete | diff against squash commit | lab manifest must list bucketed paths; gate floods |
| 2b. Subtree per skill (`split`) | 1 hunk | 3 hunks | clean, if you split the new path | split fails: "does not exist" | diff against squash commit (names a synthetic split SHA) | flat layout yes; slow, opaque provenance |
| 3. Pristine pin + `git merge-file` | 1 hunk | 3 hunks | clean (path found by name) | reported; lab copy kept | `diff -r upstream/<src>/<name> skills/<name>` | yes |
| 4. Overlay add-ons | 0 hunks, 2 loud orphans | 0 | absorbed (found by name) | orphan error | the overlay files themselves | yes, but cannot change upstream text |

Ranking:

1. **Pinned pristine copy + per-file three-way merge (3).** Its conflicts are the floor any
   text merge hits. A bucket move costs nothing because the skill is found by name. A
   deleted skill or a renamed file is reported out loud. The flat `skills/<name>/` layout
   comes for free, upstream's manifests are never touched, and one sync is one CalVer
   bump. It also takes in mechanism 4's main strength: a lab-only file next to the
   upstream text never conflicts. A `LAB-SCIENCE.md` plus a one-line pointer synced with
   0 conflicts (verified). The cost is a sync script (my prototype is 84 lines, before a
   by-name lookup), a pin file, and a rule that keeps the pristine directory out of
   markdownlint and shellcheck.
2. **Overlay add-ons (4).** No conflicts at all, and every break shows up as a build error.
   But it can only append. It cannot rewrite an upstream sentence, a `description` or
   pstack's Cursor model lines. Lab text lands at the end of the file rather than where it
   belongs, and the file that ships is a build output. Under mechanism 3 the same
   discipline works as a convention: put lab text in lab-only files.
3. **Per-skill subtree split (2b).** Its conflicts match mechanism 3 and it handles moves.
   But each squash records a synthetic split commit rather than the upstream commit.
   `git subtree split` walks the whole upstream history once per skill and needs the
   prefix checked out. There is no pristine copy to diff against.
4. **Whole-upstream subtree (2a).** It brings in all of upstream (181 files changed in the
   window). The lab manifest has to name bucketed paths by hand, and a move breaks them
   without a conflict. The gate sweeps the vendored text: markdownlint found 184 issues in
   75 files (verified).
5. **Fork (1).** Everything in 4 applies, and `plugin.json` also conflicts on every sync
   (2 hunks here). A fork is a separate repo and plugin, which breaks ADR 0001. Merging
   upstream into this repo instead gives 9 add/add conflicts at the root before any skill
   is involved (verified).

Work per sync:

| Mechanism | Steps each sync | Tooling |
| --- | --- | --- |
| 1. Fork | fetch, merge, resolve (manifest every time), port stranded moves, decide modify/delete, bump | git |
| 2a. Whole subtree | `subtree pull`, resolve, fix lab manifest paths, bump | git-subtree |
| 2b. Per-skill subtree | per skill: find the new path, `split`, `pull --squash`, resolve; bump | git-subtree; split walks all history |
| 3. Pristine + merge-file | run sync (finds paths by name, merges per file), resolve hunks, read the deleted/stale report, bump pin and CalVer | a script (84-line prototype), `PIN.json` |
| 4. Overlay | bump pin, build, rename or retire orphan overlays, read the stale report, bump CalVer | a build script (47-line prototype) |

One problem goes unseen under every mechanism. A lab line that still says `CONTEXT.md`
merges cleanly after upstream renamed that convention to `GLOSSARY.md`. A cheap check
catches it (verified, below). The check is easy to add to mechanisms 3 and 4.

## Setup

**Base pin (verified).** All 22 mattpocock entries in `~/.agents/.skill-lock.json` record a
`skillFolderHash` equal to `git rev-parse ed37663:<skill dir>`, so 22 of 22 match. Its parent
matches 21. `ed37663` (commit dated 2026-07-21) was the head of `main` from then until
`2ab9580` on 2026-07-28, which covers the install on 2026-07-25. So the base is pinned
exactly.

**Window `ed37663..49dd158` (verified).** 231 commits, 81 of them first-parent; 181 files
changed; plugin version 1.2.0 to 1.3.1. **Every one of the 22 installed skills changed**: no
tree hash matches at `49dd158`. The em-dash sweep `3216582` (2026-08-19) alone touched 99
files and about 1,150 lines. Upstream events used:

- `domain-modeling`: the convention moved from `CONTEXT.md` to `GLOSSARY.md` in `d80fa0f`
  (2026-09-17), `CONTEXT-FORMAT.md` was renamed `GLOSSARY-FORMAT.md` (70% similar), and
  the description was rewritten (`bd8e81b`, `e12e7ec`, `54bc6b6`).
- `wizard`: graduated from `in-progress/` to `engineering/` in `b3376f8` (2026-08-05)
  and was then reworked. `SKILL.md` is 48% similar from base to tip.
- `resolving-merge-conflicts`: removed in `daa01d8` (2026-09-24).
- `writing-great-skills` became `writing-for-agents` (`1fc6573`). Git sees a delete and an
  unrelated add. No mechanism links the two, and npx flags the old name as deleted
  without installing the new one (verified).

**Lab edits (one script, the same text in every layout).** DM1 rewrites the "Cross-reference
with code" sentence to cover notebooks and Slurm configs. DM2 adds a "Pin down science
terms" section that names `CONTEXT.md`. DM3 adds a rules bullet to `CONTEXT-FORMAT.md`. WZ1
adds an onboarding-wizard bullet, and WZ2 adds `pixi run shellcheck`. RMC1 adds an `nbdime`
step for `.ipynb` conflicts. In the fork, the lab also renamed the plugin and listed
`in-progress/wizard`.

## Evidence

### 0. `npx skills update` on an edited copy

Source: vercel-labs/skills `13e4063`, run as `skills@1.7.2`.

- **(read)** `update.ts` decides "changed" by comparing upstream's current hash with the
  hash **recorded in the lock** (global: the GitHub tree SHA; project: `computedHash`). It
  never hashes the local folder. On a change it runs `skills add … -y`. The installer's
  `cleanAndCreateDirectory` does `rm -rf` and then copies (`installer.ts:198`). Nothing in
  `src/` detects local modification.
- **(verified)** I ran it in a scratch project (`update -p -y`, telemetry off) with the
  four skills edited and a `LAB-NOTES.md` added. Project scope avoids touching the real
  `~/.agents`; the global flow makes the same comparison (read). Result: `domain-modeling` and `wizard`
  were replaced and **every lab edit was gone, the added file too**. `wizard` was moved to
  `engineering/` because its name is unique, and the lock's `skillPath` was rewritten.
  `resolving-merge-conflicts` and `writing-great-skills` showed as "deleted upstream" and
  were kept, because `-y` skips deletion; interactively it offers to remove them (read).
  They keep their edits but will never update again. Since all 22 installed skills changed
  in this window, any local edit to any of them would have been lost.

### 1. Fork, merged from upstream

Clone at `ed37663`, lab commit, `git merge 49dd158` (verified):

- `plugin.json`: 2 hunks. The lab's `name` conflicts with upstream's version and
  description lines. Upstream's new `engineering/wizard` path conflicts with the lab's
  `in-progress/wizard` line. This happens on every sync that touches the manifest.
- `domain-modeling/SKILL.md`: 1 hunk. DM1 against the em-dash sweep: the upstream line
  changed only its punctuation.
- DM2 merged cleanly, so the file now says `GLOSSARY.md` everywhere except the lab's
  section, which still says `CONTEXT.md`.
- DM3 followed the rename into `GLOSSARY-FORMAT.md` cleanly.
- `wizard`: **modify/delete**. At 48% similarity the default 50% threshold does not pair
  the files. `template.sh` and `openai.yaml` moved to `engineering/` on their own, which
  leaves the lab's `SKILL.md` stranded beside a second `wizard`. With
  `-X find-renames=40%` the edits land in `engineering/wizard/SKILL.md` with no conflict.
- `resolving-merge-conflicts`: modify/delete.
- Into this repo instead: `git merge --allow-unrelated-histories ed37663` against
  `liulab-skills` gives 9 conflicts (`.claude-plugin/{marketplace,plugin}.json`,
  `.gitignore`, `AGENTS.md`, `CLAUDE.md`, `CHANGELOG.md`, `CONTEXT.md`, `LICENSE`,
  `README.md`).
- (read) Upstream versions with changesets and semver. A fork carries those files and
  conflicts with the lab's CalVer on the `version` line, which happened here.

### 2. `git subtree`

**2a, whole upstream at `vendor/mattpocock-skills/` (verified).** `subtree add --squash`,
then lab edits, then `subtree pull --squash`. Result: the same 3 skill files as the fork
(1 hunk, 2 modify/delete). There is no `plugin.json` conflict, because the lab's manifest is
its own. `git subtree` has no `-X` option (`git subtree -h`, git 2.50.1), so the `wizard`
move cannot be rescued. Upstream is bucketed and this repo is flat, so the lab's
`plugin.json` must list `./vendor/…/skills/engineering/<name>` by hand, and a bucket move
silently leaves a stale path (unverified). In a scratch clone, markdownlint over the
vendored tree found 184 issues in 75 files and shellcheck failed (verified).

**2b, one subtree per skill at `skills/<name>/` (verified).** `git subtree split
--prefix=skills/<bucket>/<name>` gives a history for that one skill, then `subtree add` /
`pull --squash` at the flat prefix. `domain-modeling`: 1 hunk, and the rename was followed.
`wizard`: **0 conflicts**, because the squash diffs old content against new whatever the
upstream path; you only have to know to split `engineering/wizard` this time. A deletion
shows up when `split` fails with "does not exist; use 'git subtree add'". Split also
refuses a prefix that is missing from the current checkout, so splitting the base meant
checking the base out first. The squash message records `content from commit 97d693d`,
which is a split commit, not an upstream one.

### 3. Pinned pristine copy + `git merge-file`

Layout: `upstream/mattpocock-skills/<name>/` (untouched, at the pin), `PIN.json` (commit plus
name-to-path map), and `skills/<name>/` (the lab copy). The sync script runs no git against
any repo. It runs `git merge-file` on plain files, given the new export and a file-rename map
from `git diff -M --name-status <old>:<path> <new>:<path>` (verified):

- `domain-modeling`: 1 hunk (DM1); `CONTEXT-FORMAT.md` renamed, with DM3 carried.
- `wizard`: 0 conflicts. The new path came from searching the tip for `*/wizard/SKILL.md`.
  A real script should look up the frontmatter name the way npx does.
- `resolving-merge-conflicts`: "UPSTREAM DELETED, lab copy kept; lab-edited files:
  SKILL.md".
- `diff -ru upstream/mattpocock-skills/domain-modeling skills/domain-modeling` prints
  DM1 to DM3 and nothing else. Anyone can read both copies on GitHub.
- (read) The pristine copies sit outside `skills/`, so neither the plugin's default `skills/`
  discovery nor `npx skills`' default search (root depth 1, `skills/` to depth 3, agent
  dirs, manifest paths; `skills.ts`) will load them twice.

### 4. Upstream untouched, lab add-ons beside it

An add-on file is never loaded on its own. A skill's body is `SKILL.md`, and a sibling file
is read only when `SKILL.md` points to it (read). So "untouched upstream" needs a loader. I
tested a build step: copy the upstream skill, found by frontmatter name, append
`overlays/<skill>/<file>.lab.md` under a marker, and optionally rewrite `name:` (verified):

- At base: everything built. At tip: `ORPHAN domain-modeling/CONTEXT-FORMAT.md.lab.md`
  (the rename), `ORPHAN resolving-merge-conflicts` (the deletion), `wizard` built from its
  new path, exit 1.
- DM1 cannot be expressed. It became an appended "also covers notebooks" note, away from
  the sentence it qualifies.
- Other loaders (unverified): a separate lab skill that triggers next to the upstream one,
  where the agent may load only one; or text in each repo's `AGENTS.md`, which costs a
  per-repo step the map rules out.

### Cross-cutting findings

- **The `lab-*` rename collides with descriptions (verified).** The naming policy needs
  `name: lab-<x>`. Line 2 changes, sits next to `description:`, and `git merge-file` gives a
  conflict whenever upstream edits the description. In this window that happened to 7 of the
  22 mattpocock engineering and productivity skills, and to 7 of the 40 pstack skills. A
  build step (4) does the rename with no conflict.
- **The gate (verified).** With the three skills at `skills/<name>/`, `pixi run check`
  fails markdownlint (MD040 twice in `domain-modeling`, MD041 in
  `resolving-merge-conflicts`) and shellcheck (`wizard/template.sh`, SC1087). The skill lint
  fails the naming policy for all three, plus the expected "version already tagged, tree
  moved". Vale passed. Mechanisms 2b, 3 and 4 all hit this, so derived skills need
  exclusions or fix-up edits.
- **Versioning (read).** Under ADR 0008 every sync is a merged change: a CalVer bump, a
  `CHANGELOG.md` entry and a tag. This works for 2b, 3 and 4 in this repo. A fork carries
  upstream's semver.
- **Stale-vocabulary check (verified).** Take the backticked tokens on removed lines of
  upstream's diff, drop those that still appear on added lines, and grep the lab text. For
  `domain-modeling` the stale set was `CONTEXT.md` and `CONTEXT-MAP.md`. It flagged DM2.

## pstack replay

Window `04166ac` (2026-07-23, v0.11.8, the last pstack commit before the install date;
pstack has no install record) to `978ca6e` (v0.15.17). 43 of the 337 repo commits touched
`pstack/`: 47 files added, 95 modified, 3 deleted, and no skill moved or was deleted
(verified). Its layout is `pstack/skills/<name>/`, flat like this repo.

Edits: PH1 swaps `how`'s Cursor explorer model for `sonnet`, PH2 adds a Slurm-pipeline
example, and PP1 adds a lab trigger to `poteto-mode`.

- **Fork, 2b and 3: 3 hunks each (verified).** `how` has 2 hunks. Nine commits touched
  its `SKILL.md` in the window, three of them model-default bumps (`63d938c`, `70b2dc8`,
  `df58112`) and two prose rewrites (`e8d856f`, `00b14f1`), so one hunk covers about 90
  lab-side lines. `poteto-mode` has 1, in a trigger list upstream extended. Mechanism 3
  also reported `how/references/critic-prompt.md` and `critique-rubric.md` deleted, and
  new playbooks, references and a `scripts/` tree added to `poteto-mode`.
- **Overlay: 0 conflicts, 0 orphans (verified).** But PH1 becomes a blanket "use `sonnet`
  wherever a model is named" note that contradicts the upstream text under it. Porting
  pstack means rewriting Cursor-specific lines, so pure overlay fits pstack worse than
  mattpocock.
- **Fork scope (verified).** The cursor/plugins window changes 719 files. The repo holds
  16 other plugin directories, and a fork would carry them all.
- **Manifest and frontmatter (read).** `.cursor-plugin/plugin.json` uses `"skills":
  "./skills/"`, which this repo's layout already matches. `poteto-mode` has `name: Poteto
  Mode` and the Cursor-only keys `mode`, `icon`, `color` and `reminder`; `tdd` and `teach`
  share names with mattpocock skills. All of these need lab edits or build-time rewrites.
  Since the base, `poteto-mode` has also gained a TypeScript `scripts/` tree with
  `bun.lock`, which would come under the gate.

## Commands

All runs used fresh clones in a scratch directory outside the worktree.

```bash
git ls-tree -r -d ed37663 skills          # compared with the lock's skillFolderHash
git merge --no-edit [-X find-renames=40%] 49dd158        # fork
git merge --allow-unrelated-histories <ed37663>          # fork into liulab-skills
git subtree add|pull --prefix=vendor/mattpocock-skills ../mp <ref> --squash
git subtree split --prefix=skills/engineering/wizard tip -b wz-tip   # then pull at skills/wizard
git diff -M --name-status base:skills/in-progress/wizard tip:skills/engineering/wizard
git merge-file -p -L lab -L pinned -L upstream <lab> <pinned> <new>  # per file
npx -y skills@1.7.2 update -p -y          # scratch project, DO_NOT_TRACK=1
pixi run check; pixi run skill-lint       # in scratch clones of liulab-skills
```
