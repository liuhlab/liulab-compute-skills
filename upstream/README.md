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
| `skills_dir` | Where the upstream keeps its skills. The sync finds an item under it by frontmatter `name`, so a bucket move costs nothing. |
| `items` | Upstream item name to the lab path it feeds, relative to the repo root. |

Under `merge`, every value is a whole skill, `skills/<name>`, and each name maps to itself
until one clashes (`docs/adr/0013-adopted-skills-keep-upstream-names.md`). Under `review`,
`items` also holds the items taken only as ideas, each mapped to the lab file it shaped.
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
here, with the pin's `commit`.

## Adopting a tracked skill

1. Copy the upstream skill directory, byte for byte, to `skills/<name>/`.
2. Map it in the pin's `items`.
3. Add its name to the adopted-skill section of `.vale.ini` and as a filter line in the
   override in `.markdownlint-cli2.yaml`. That is how upstream text passes the gate
   unchanged.

## A lab edit to a tracked skill

A lab edit only adds lines, and nothing here records it: its record is the diff against the
pin, with its reason in the commit message and the changelog (ADR 0012). The pin still maps
the whole skill, and nothing in the gate compares it with upstream.

- A branch or a loop path goes in place, in the upstream file.
- A whole new section goes in a lab-only page, `skills/<name>/LAB-<topic>.md`, with a
  one-line pointer from the upstream file. The skill's gate exemption covers that page too,
  so keep it to what a reference page beside a lab skill would pass.
- An edit that pushes against upstream's own steer gets an eval case named `<name>-*` in
  `tests/eval.sh`. An upstream rewording can undo it without a conflict, so a sync that
  changes the skill reruns that case.

## What reads these

- `tests/lint.sh`, section `adopted skill names`. A skill outside `lab-*` passes only when
  a `merge` pin maps it, when a record lists it, or when it is `hq-mode`. The section also
  fails a source with no `LICENSE`, a skill both tracked and forked, and the two gate lists
  above when they miss a tracked skill, disagree, or name a skill nobody adopted.
- The upstream sync, from Python, with `json.load`.
- Bash, through a one-liner. This prints the tracked names:

  ```bash
  python3 -c 'import json; print(*json.load(open("upstream/mattpocock/pin.json"))["items"], sep="\n")'
  ```
