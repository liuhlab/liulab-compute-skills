# Upstream records

What the lab takes from its upstreams is recorded here and nowhere else. This is never a
copy of upstream: a sync clones the upstream and reads both ends from that clone
(`docs/adr/0012-upstream-skills-merge-from-a-pin.md`).

```text
upstream/
  attribution.json    one record per forked item
  <upstream>/
    LICENSE           the upstream's license, verbatim
    pin.json          only for an upstream the lab follows
```

`<upstream>` is a short name: `mattpocock` for mattpocock/skills, `pstack` for
cursor/plugins' `pstack`. A source the lab takes text from but does not follow gets a
directory holding its `LICENSE` and no pin.

## The pin: `<upstream>/pin.json`

```json
{
  "repo": "https://github.com/mattpocock/skills",
  "commit": "49dd158d1076134a641b33efb035946536778336",
  "sync": "merge",
  "skills_dir": "skills",
  "items": {
    "grilling": "skills/grilling"
  }
}
```

| Key | Meaning |
| --- | --- |
| `repo` | The upstream's clone URL. |
| `commit` | The full commit last synced (`merge`) or reviewed (`review`). |
| `sync` | `merge`: every item is a tracked skill, merged file by file on each sync with `commit` as the base. `review`: items are only diffed for the sync's summary, never merged. |
| `skills_dir` | Where the upstream keeps its skills. The sync finds a tracked skill under it by frontmatter `name`, so a bucket move costs nothing. |
| `items` | Upstream item name to the lab path it feeds, relative to the repo root. |

Under `merge`, every value is a whole skill, `skills/<name>`, and each name maps to itself
until one clashes (`docs/adr/0013-adopted-skills-keep-upstream-names.md`). Under `review`,
`items` also holds the items taken only as ideas, each mapped to the lab file it shaped, and
each item is named by its path under `skills_dir`: a skill by its directory, a file inside one
by its file path, such as `poteto-mode/playbooks/hillclimb.md`. pstack's `poteto-mode` calls
itself `Poteto Mode`, so a frontmatter name would not find it. An idea that shaped no lab file
is a skipped item and stays out, as `blast-radius` and `correct` do: `pr` and `retro`, where
their ideas were to go, ship as upstream wrote them.
Moving `commit` forward goes in the sync's one pull request.

## The attribution record: `attribution.json`

One record per forked item, keyed by its lab path: a whole skill, such as `skills/unslop`,
or one file, such as a reference page.

```json
{
  "skills/unslop": {
    "from": [
      {"upstream": "pstack", "item": "unslop", "commit": "978ca6e9c0e012047cd5058b8e829240336e704e"}
    ],
    "changes": "One line on what the lab changed."
  }
}
```

- `from` lists every source of the item's text, at least one. `upstream` names a directory
  here whose `LICENSE` covers it, `item` is the upstream's name for it, and `commit` is the
  full commit it was taken at.
- `changes` is optional.

Forking a tracked skill is one step: delete it from its pin's `items` and add its record
here, with the pin's `commit`. `python scripts/upstream_sync.py fork <name>` does both.

A forked skill is lab text and meets the gate, as `ketchup` does, unless meeting it would
reshape the upstream text. `unslop`, `technical-writing` and `bro` stay in both gate lists
below. The first two each run past the 600-word skill cap, and `unslop` numbers its rules as
ids the text cites, which markdownlint's MD029 rejects. Fitting them would move much of
upstream's text into `references/`, so every upstream change would be ported by hand into
another shape. `bro`'s body opens on prose with no heading, which MD041 rejects, and a heading
would change upstream's text; it meets vale's cap, and is on vale's list because lint wants
the two lists to agree. The cost is small: in a skill body vale checks only that cap, and
markdownlint still applies every rule outside the override's ten. Take a fork out of both
lists once it fits.

## Adopting a tracked skill

1. Copy the upstream skill directory, byte for byte, to `skills/<name>/`.
2. Map it in the pin's `items`.
3. Add its name to the adopted-skill section of `.vale.ini` and as a filter line in the
   override in `.markdownlint-cli2.yaml`. That is how upstream text passes the gate
   unchanged.

## Lab edits

A lab edit adds to a tracked skill's upstream text and removes no line of it (`GLOSSARY.md`).
Nothing in this directory records one: its record is the diff against the pin, with its
reason in the commit message and the changelog (ADR 0012). Lint never reads upstream, so
nothing automatic checks that an edit removed no line: read the diff against the pin.

- A branch or a loop path goes in place, in the upstream file.
- A whole new section goes in a side page beside that file, named `<topic>.lab.md`, with a
  one-line pointer from it. The suffix tells the gate it is lab text: `.vale.ini`'s
  `[skills/*/*.lab.md]` section and the markdownlint override's `!**/*.lab.md` line hold it
  to the rules for any page beside a skill body. `tests/test_side_pages.py` checks both.
- An edit that pushes against upstream's own steer gets an eval case named `<name>-*` in
  `tests/eval.sh`'s `CASES` list. An upstream rewording can undo it without a conflict, so a
  sync that changes the skill lists that case, and reruns it on the maintainer's yes.

Every edit to upstream text, a lab edit or a change to a fork, names the failure it answers:
one seen in a lab session or an eval, never a guess that an agent might miss something. An
edit made before this rule need not name one, and returning to upstream's text needs none.

## What reads these

- `tests/lint.sh`, section `adopted skill names`. A skill outside `lab-*` passes only when
  a `merge` pin maps it, when a record lists it, or when it is `hq-mode`. The section also
  fails a source with no `LICENSE`, a skill both tracked and forked, a `review` pin item
  mapped to a lab path that does not exist, and the two gate lists above when they miss a
  tracked skill, disagree, or name a skill nobody adopted.
- The upstream sync, `scripts/upstream_sync.py`, which the maintainer runs through
  `/lab-upstream-sync` in `.claude/commands/`. It writes both files back in the layouts above,
  and adopts a skill new upstream by the three steps above. It also reports lab text that
  still uses a name upstream removed. Lab text is every Markdown file in the repo but
  `CHANGELOG.md` and `docs/adr/`, so a new lab page needs no entry anywhere; in a tracked
  skill it is only the lines upstream did not write.
- Bash, through a one-liner. This prints the tracked names:

  ```bash
  python3 -c 'import json; print(*json.load(open("upstream/mattpocock/pin.json"))["items"], sep="\n")'
  ```
