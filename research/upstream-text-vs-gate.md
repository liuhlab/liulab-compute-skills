# Whether upstream skill text passes this repo's gate

> **Provenance** — Source: `pixi run check` and `bash tests/lint.sh` on a local scratch branch off `269949e`, plus the gate's own source · Checked: 2026-10-10 · Default tier: verified

Ticket #66, under map #62. Inputs: mattpocock/skills at `49dd158` and cursor/plugins `pstack` at `978ca6e`
(v0.15.17). Every claim here is **verified** (I ran it) unless it is tagged *(read)*, taken from the gate's
source, a spec or the map without running it, or *(unverified)*, inferred.

## Answer

All eight copied skills fail the gate. Only three of the seven named steps catch anything: the naming policy
(8 of 8 skills), markdownlint (67 issues in 7 of 8 skills) and the vale word caps (4 files in 3 skills). The
1536-character description cap, conformance and the no-secrets sweep all pass untouched.

- **Configuration can absorb vale and markdownlint without touching upstream text.** One extra `.vale.ini`
  section plus one `overrides:` block in `.markdownlint-cli2.yaml` turned both green, and conformance still
  passed 13 of 13. The cost is that the word caps and six structure rules stop applying to exactly the longest
  bodies, and the repo gains two lists of upstream names that must agree.
- **The naming policy cannot be absorbed by configuration.** It is code in `tests/lint.sh` (`case lab-*`). You
  either change the policy, which means editing lint and `AGENTS.md` and probably writing an ADR, or rename the
  skills. Renaming forces edits to upstream text: the `name:` line, and also every cross-reference. Skills cite
  each other by name, and `poteto-mode` builds principle-skill names from a pattern.
- **`poteto-mode` needs a one-line upstream edit whatever else is decided.** Its `name: Poteto Mode` breaks the
  open Agent Skills spec *(read)*, and lint catches it.
- **Nothing trips the no-secrets policy, even in spirit.**

One more finding matters for #67. Upstream support files that sit outside `references/` match no vale section.
That covers mattpocock's flat `*-FORMAT.md` and `mocking.md` files and all 23 pstack `playbooks/`, so no word cap
reaches them today. Three playbooks are over the 1200-word document cap.

## Failure table

| Step | Skill | Failure | Absorbable by config? | How |
| --- | --- | --- | --- | --- |
| naming policy (`tests/lint.sh`) | all 8 | `skill '<name>' must be lab-*` | **No** | Change lint and `AGENTS.md` (policy), or rename: edits `name:` and cross-references |
| frontmatter name (`tests/lint.sh`) | poteto-mode | `frontmatter name 'Poteto' != dir 'poteto-mode'` | **No** | Edit `name:` to `poteto-mode`. Loosening lint would ship a non-spec skill |
| vale `Lab.LengthSkill` (600) | wayfinder | 1843 words | Yes | `.vale.ini` section, Length rules off |
| vale `Lab.LengthSkill` | unslop | 834 words | Yes | same section |
| vale `Lab.LengthSkill` | poteto-mode | 678 words | Yes | same section |
| vale `Lab.LengthDoc` (1200) | poteto-mode | `references/bugbot-triage.md` 1326 words | Yes | same section |
| markdownlint MD029 ol-prefix | unslop | 28 | Yes | `overrides:` filter. Editing would be *wrong*: the numbers are stable rule IDs |
| markdownlint MD041 first-line-h1 | poteto-mode, grilling, wayfinder | 23 + 1 + 1 | Yes | `overrides:` |
| markdownlint MD036 emphasis-as-heading | poteto-mode, tdd | 5 + 2 | Yes | `overrides:` |
| markdownlint MD040 fence language | domain-modeling, grilling, poteto-mode | 2 + 1 + 1 | Yes | `overrides:` |
| markdownlint MD032 blanks-around-lists | principle-prove-it-works, tdd | 1 + 1 | Yes | `overrides:` |
| markdownlint MD033 inline HTML | poteto-mode | 1 (`<title>`) | Yes | `overrides:` |
| description cap (1536) | all 8 | pass: 49 to 294 chars, also under the spec's 1024 | n/a | n/a |
| conformance | all 8 | pass, 13 of 13 rules | n/a | n/a |
| no-secrets sweep | all 8 | pass, all five sweeps | n/a | n/a |
| ruff, pyright, pytest, shellcheck | all 8 | pass | n/a | n/a |
| release (`tests/lint.sh`) | n/a | tagged version, tree moved | n/a | Scratch-state artifact; a real adoption bumps the version |

## Commands run

1. Baseline on clean `269949e`: `pixi install`, then `pixi run check`. All eight static steps and `skill-lint`
   passed.
2. On a local scratch branch, I copied each skill directory verbatim and flattened it to `skills/<name>/`:
   mattpocock `grilling`, `domain-modeling`, `wayfinder` and `tdd`; pstack `unslop`, the whole `poteto-mode`
   directory, `principle-prove-it-works` (a typical principle at 209 words) and `principle-type-system-discipline`
   (the longest at 565, the edge case). I committed them locally so that the steps reading `git ls-files`
   (conformance, shellcheck) would see them.
3. `pixi run check`: `vale` and `markdownlint` FAIL, the other six static steps pass. **`skill-lint` did not
   run.** `check` depends on `check-static`, so a red static step hides every lint failure. I ran
   `bash tests/lint.sh` on its own to see them.
4. Word counts for every copied markdown file: `vale --config=<temp ini> --output=line skills/<each>`. The temp
   ini held a metric rule that always fires and prints vale's own `words` count, the counter the caps use.
5. Absorption probes, uncommitted on the scratch branch: append a `.vale.ini` section, then run
   `pixi run vale` and `pixi run conformance`. Append markdownlint `overrides:`, then run `pixi run markdownlint`,
   plus a probe file with a bare code fence in `skills/lab-hpc/` and in `skills/tdd/`.
6. Rename probe: `mv skills/grilling skills/lab-grilling`, then `bash tests/lint.sh`.
7. Static `shellcheck` over all five upstream `*.sh` files, including ones outside the sample. Then `grep` over
   the copies for URLs, emails, host-like names, `~/.ssh`, `/home/`, key headers and secret words.
8. Then I discarded everything: restored both configs, switched back, deleted the scratch branch.
   `git status` was clean.

## Detail by step

### Naming policy: not absorbable

`tests/lint.sh` fails every skill directory not named `lab-*`. The message says "(not liulab-*)", but the
check accepts `lab-*` and nothing else. No config file feeds it, so an exemption is an edit to the lint, a
change to `AGENTS.md`'s naming policy, and probably an ADR. That is a policy decision, not configuration.
Conformance rule 6 has the opposite shape: no repo-local skill may *start* with `lab-`, and it is already
waived here. Upstream names pass it as they are, and renamed ones would fall under the existing waiver.

Renaming forces upstream edits beyond the directory. The probe showed that `skills/lab-grilling` with an
untouched `name: grilling` fails `frontmatter name 'grilling' != dir 'lab-grilling'`. Renaming also breaks the
cross-references:

- `wayfinder` names `grilling`, `research` and `prototype` in its body.
- `poteto-mode` cites `/unslop`, `/prototype` and `/poteto-mode`.
- `poteto-mode` says each principle "is the `principle-<title>` skill, with the title in kebab case". Renaming
  the principles to `lab-principle-*` breaks that rule, not just one link.

Every sync would have to re-apply all of these edits.

Keeping upstream names has a cost too. Map #62 records user-level copies from `npx skills`, and on the
maintainer's machine these include `grilling`, `tdd` and `domain-modeling` *(read)*. A plugin copy under the
same bare name likely puts two same-named entries in the listing until that migration happens *(unverified)*.

### poteto-mode frontmatter: forces a one-line edit

The upstream file has `name: Poteto Mode`. The spec says `name` takes lowercase letters, digits and hyphens
only, and "must match the parent directory name" (agentskills.io/specification, *read*). Lint reads the first
word, `Poteto`, and fails it. The keys `mode`, `icon`, `color` and `reminder` are Cursor-specific and outside
the spec, which wants extras under `metadata`. No step in the gate reads them.

### Vale word caps: absorbable, at a real cost

This section made vale report 0 errors in 76 files, and conformance still passed 13 of 13:

```ini
[skills/{grilling,domain-modeling,wayfinder,tdd,unslop,poteto-mode,principle-prove-it-works,principle-type-system-discipline}/*.md]
BasedOnStyles = Lab
Lab.Jargon = NO
Lab.Readability = NO
Lab.LengthDoc = NO
Lab.LengthSkill = NO
Lab.LengthAdr = NO
```

Conformance rule 3 pairs each `[tool.liulab.agent-docs]` key with the one header that spells it. This header
spells no key, so rule 3 neither sees it nor objects, as the run confirms. Vale's `*` matches `/`, so
`*.md` also reaches `references/` and `playbooks/`.

What it costs:

- The cap exists because "a body is an interface". Exempting upstream switches that off for the bodies that
  break it worst: `wayfinder` is three times the cap, and every session that loads it pays for that.
- Every adopted skill must be added to that header.
- A more honest option is still configuration: declare the upstream class in `[tool.liulab.agent-docs]`, either
  as `false` (like `CONTEXT.md`) or with a new `Lab.LengthUpstream` rule. That is a styles diff, a key and a
  section, and it puts the exemption in the table conformance prints on every run.
- Meeting the cap instead means moving detail out of `wayfinder`, `unslop` and `poteto-mode` into `references/`,
  which is a large edit that conflicts with every sync.

The blind spot described in the Answer (support files outside `references/`) means `orchestrate.md` (2441
words), `autopilot-full.md` (1566) and `babysit.md` (1256) pass today only because nothing checks them.
Widening the glob to cap them would turn into three more failures that no config change can fix.

### markdownlint: absorbable, centrally

markdownlint-cli2 v0.23.2 supports root-level `overrides:` with glob `filter`s. One block with the same skill list
and `MD029`, `MD032`, `MD033`, `MD036`, `MD040` and `MD041` off took the run from 67 issues to 0. The probe showed
it does not leak: the bare fence in `skills/lab-hpc/` was still flagged, and the one in `skills/tdd/` was not.

Other routes are worse:

- A directory-scoped `.markdownlint.yaml` inside each skill adds files to the upstream tree that a sync must keep.
- Turning a rule off globally loses it on lab text, which passes all six today.
- `ignores:` drops every rule, and the config's own comment rejects an ignores list.

The cost of `overrides:` is a second list of upstream names that must stay in step with the vale header. That is
the "two lists that must agree" drift `.markdownlint-cli2.yaml` warns about.

`unslop`'s gaps are deliberate. The file says "Rule numbers are stable ids that other skills cite. A removed rule
leaves a gap." So renumbering to satisfy MD029 would break meaning, and configuration is the only correct fix.
The other failures are cosmetic, but fixing them still means editing upstream text: 23 `poteto-mode` playbooks
open on `###`, and some fences have no language.

### The steps that pass, and what they don't see

- **Conformance, 13 of 13.** Rule 5 (location) holds for the flattened layout. Rule 6 is not triggered. Rule 10
  ignores `bun.lock`, because it looks only for Python resolvers.
- **shellcheck** reads `git ls-files '*.sh'`, and `poteto-mode/scripts/worktree-audit.sh` is clean.
  `watch-pr` is a bun script with no suffix, so shellcheck correctly skips it.
- **ruff and pyright** see no Python. `poteto-mode` ships 15 `.ts`/`.mjs` files and the `watch-pr` bun
  script, plus `package.json` and `bun.lock`, and **no gate step reads any of them**. They also need `bun`, a
  second runtime that pixi does not manage.
- **Outside the sample:** mattpocock's `engineering/wizard/template.sh` fails shellcheck (one SC1087 error, two
  SC2329 notes). The other upstream scripts are clean. Excluding the path from the `shellcheck` task's pathspec,
  or adding a `.shellcheckrc` in the skill, would absorb it. But `pyproject.toml` says findings are "silenced at
  [their] line with a `shellcheck disable` directive saying why", so the policy-conforming fix edits upstream.

### No-secrets sweep, and the spirit of the policy

All five sweeps pass: IP literals, key material, the Edison key, ssh-config usernames, ssh-config hostnames.
The grep found only public-forge URLs, which the sweep already exempts. Specifically:

- `github.com` links and a `https://github.com/<owner>/<repo>/pull/<number>` placeholder.
- The `git@github.com` and `ssh://git@github.com/` prefixes that `watch-pr` parses out of remotes.
- An `orch@example.com` test identity on the reserved example domain.

`bun.lock` holds no IP-shaped version strings. Nothing names a private host, a user or a key path.

## For #67

The edits a sync must re-apply are set by the naming decision, not by text quality. If `lab-*` holds, each
adopted skill carries a `name:` edit and its cross-reference edits. `poteto-mode` adds one spec fix either way.
Everything else is configuration keyed on a list of skill names. Rule 5 requires `skills/<name>/SKILL.md`, so a
subdirectory cannot group upstream skills. A shared name pattern is the only single-glob handle, and with one the
vale section and the markdownlint filter could not drift apart.
