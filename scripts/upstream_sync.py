#!/usr/bin/env python3
"""The upstream sync's merge-and-report step.

The maintainer runs it from `/lab-upstream-sync` (`.claude/commands/`), on a clean branch of
this repo, about monthly (`docs/adr/0012-upstream-skills-merge-from-a-pin.md`). It reads the
pins and the attribution record from `upstream/` (formats: `upstream/README.md`), reads each
upstream only through a fresh clone given on the command line, and writes only the lab tree.
It never touches the network.

`merge` brings every tracked skill from its pin to upstream's tip, one file at a time, with
`git merge-file`: the lab copy is ours, the file at the pin is the base, the tip's is theirs.
A skill is found under `skills_dir` by its frontmatter `name`, so a bucket move costs
nothing. A conflict is left in the file between `<<<<<<< lab` and `>>>>>>> upstream`, with the
pinned text between `||||||| pinned` and `=======`. A skill gone from the tip is deleted or
renamed: its lab copy, pin entry and gate exemption go, unless the lab forked it. A skill
upstream's plugin manifest lists at the tip and not at the pin arrives under its own name. A
forked skill is never merged. If the pinned commit is gone from the clone, because upstream
rewrote its history, every difference between the lab copy and the tip is marked as a
conflict instead. Then the pin moves to the tip, and a Markdown report goes to stdout.

`fork` makes a tracked skill lab-owned: its pin entry becomes an attribution record taken at
the pin's commit. Run it on a tree the merge has not touched, and commit it on its own.

Exit status: 0, done and nothing left to resolve; 1, done, with conflicts left in the files;
2, refused, with nothing written.
"""

from __future__ import annotations

import argparse
import difflib
import json
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

#: Where an upstream keeps its plugin manifest, relative to the directory holding `skills_dir`.
MANIFESTS = (".claude-plugin/plugin.json", ".cursor-plugin/plugin.json")
#: What the merge writes. It refuses to start while any of it has uncommitted changes, so that
#: everything it does can be read with `git diff` and undone with `git restore`.
WRITES = ("skills", "upstream", ".vale.ini", ".markdownlint-cli2.yaml")
ATTRIBUTION = "upstream/attribution.json"
VALE = ".vale.ini"
MARKDOWNLINT = ".markdownlint-cli2.yaml"
#: The adopted-skill section of `.vale.ini` and the filter lines of the markdownlint override:
#: the same two patterns `tests/lint.sh` reads.
_VALE_RE = re.compile(r"^\[skills/\{([^}]*)\}/\*\.md\][ \t]*$", re.MULTILINE)
_MDL_RE = re.compile(r'^([ \t]*)-[ \t]*"skills/([^/"*{}]+)/\*\*"[ \t]*\n', re.MULTILINE)
_NAME_RE = re.compile(r"^name:\s*(.+?)\s*$")


class RefusalError(Exception):
    """A reason the sync will not run. Raised before anything is written."""


# ---------------------------------------------------------------------------------------------
# git


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    run = subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=False)
    if check and run.returncode != 0:
        detail = run.stderr.decode(errors="replace").strip()
        raise RefusalError(f"`git {' '.join(args)}` failed in {cwd}: {detail}")
    return run


@dataclass(frozen=True)
class Blob:
    """One file's content and its git mode, `100644` or `100755`."""

    mode: str
    data: bytes


#: A skill's files, keyed by path relative to the skill's directory.
Files = dict[str, Blob]


class Clone:
    """A fresh clone of one upstream, read at any commit it holds."""

    def __init__(self, root: Path) -> None:
        if _git(root, "rev-parse", "--verify", "--quiet", "HEAD", check=False).returncode != 0:
            raise RefusalError(f"{root} is not a git clone with a commit at HEAD")
        self.root = root

    def has(self, commit: str) -> bool:
        """Whether `commit` is a commit in this clone."""
        return (
            _git(self.root, "cat-file", "-e", f"{commit}^{{commit}}", check=False).returncode == 0
        )

    def tip(self) -> str:
        """Return the full commit at `HEAD`, which a fresh clone puts at upstream's tip."""
        return _git(self.root, "rev-parse", "HEAD").stdout.decode().strip()

    def entries(self, commit: str, prefix: str) -> dict[str, tuple[str, str]]:
        """Every file under `prefix` at `commit`, as path -> (mode, blob)."""
        out = _git(self.root, "ls-tree", "-r", "-z", commit, "--", prefix).stdout.decode()
        found: dict[str, tuple[str, str]] = {}
        for record in filter(None, out.split("\0")):
            meta, path = record.split("\t", 1)
            mode, kind, sha = meta.split()
            if kind == "blob":
                found[path] = (mode, sha)
        return found

    def blob(self, sha: str) -> bytes:
        """Return the content of one blob."""
        return _git(self.root, "cat-file", "blob", sha).stdout

    def text(self, commit: str, path: str) -> str | None:
        """Return the file at `path` in `commit`, or None when there is none."""
        run = _git(self.root, "show", f"{commit}:{path}", check=False)
        return run.stdout.decode(errors="replace") if run.returncode == 0 else None


def frontmatter_name(text: str) -> str | None:
    """Return the `name:` of a SKILL.md's frontmatter, or None when it has none."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            return None
        match = _NAME_RE.match(line)
        if match:
            return match.group(1).strip("\"'")
    return None


class Snapshot:
    """An upstream's skills at one commit: found by frontmatter name, read file by file."""

    def __init__(self, clone: Clone, commit: str, skills_dir: str) -> None:
        self.clone = clone
        self.commit = commit
        self.entries = clone.entries(commit, skills_dir)
        self.listed_dirs = self._manifest(skills_dir)
        dirs: dict[str, list[str]] = {}
        for path, (_, sha) in sorted(self.entries.items()):
            if posixpath.basename(path) == "SKILL.md":
                name = frontmatter_name(clone.blob(sha).decode(errors="replace"))
                if name:
                    dirs.setdefault(name, []).append(posixpath.dirname(path))
        # Two directories wearing one name, as during a bucket move: the manifest's one wins.
        self.skills = {
            name: next((d for d in found if self._listed(d)), found[0])
            for name, found in dirs.items()
        }

    def _manifest(self, skills_dir: str) -> list[str] | None:
        """Return the skill directories the plugin manifest lists, or None with no manifest."""
        root = posixpath.dirname(skills_dir.rstrip("/"))
        for name in MANIFESTS:
            text = self.clone.text(self.commit, posixpath.join(root, name))
            if text is None:
                continue
            listed = json.loads(text).get("skills", [])
            listed = [listed] if isinstance(listed, str) else listed
            return [posixpath.normpath(posixpath.join(root, entry)) for entry in listed]
        return None

    def _listed(self, directory: str) -> bool:
        if self.listed_dirs is None:
            return True
        return any(directory == d or directory.startswith(d + "/") for d in self.listed_dirs)

    def listed(self) -> set[str]:
        """Return the names of the skills the plugin manifest ships."""
        return {name for name, d in self.skills.items() if self._listed(d)}

    def files(self, name: str) -> Files:
        """Return the files of skill `name`, keyed by path inside its directory."""
        prefix = self.skills[name] + "/"
        return {
            path.removeprefix(prefix): Blob(mode, self.clone.blob(sha))
            for path, (mode, sha) in self.entries.items()
            if path.startswith(prefix)
        }


# ---------------------------------------------------------------------------------------------
# The lab tree


@dataclass
class Pin:
    """One `upstream/<upstream>/pin.json`, read and written in the format upstream/README.md gives."""

    upstream: str
    path: Path
    data: dict[str, Any]

    @property
    def commit(self) -> str:
        """The commit last synced or reviewed."""
        return self.data["commit"]

    @property
    def items(self) -> dict[str, str]:
        """Upstream item name to the lab path it feeds."""
        return self.data["items"]

    def save(self) -> None:
        """Write the pin back, two-space indented as the README shows it."""
        text = json.dumps(self.data, indent=2, ensure_ascii=False) + "\n"
        self.path.write_text(text, encoding="utf-8")


class Lab:
    """The lab tree: this repo, or a fixture shaped like it."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def pins(self) -> dict[str, Pin]:
        """Every pin under `upstream/`, keyed by upstream short name."""
        pins: dict[str, Pin] = {}
        for path in sorted((self.root / "upstream").glob("*/pin.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except ValueError as e:
                raise RefusalError(f"{path} is not valid JSON: {e}") from e
            keys = ("repo", "commit", "sync", "skills_dir", "items")
            if not isinstance(data, dict) or any(k not in data for k in keys):
                raise RefusalError(f"{path} lacks one of {', '.join(keys)} (upstream/README.md)")
            pins[path.parent.name] = Pin(path.parent.name, path, data)
        if not pins:
            raise RefusalError(f"no upstream/<upstream>/pin.json under {self.root}")
        return pins

    def attribution(self) -> dict[str, Any]:
        """Return the attribution records, keyed by lab path; empty when the file is absent."""
        path = self.root / ATTRIBUTION
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def save_attribution(self, records: dict[str, Any]) -> None:
        """Write the records in the README's shape, each source on one line."""
        (self.root / ATTRIBUTION).write_text(dump_attribution(records), encoding="utf-8")

    def require_clean(self) -> None:
        """Refuse a tree that is not a git checkout, or that has changes the sync would mix in."""
        run = _git(self.root, "status", "--porcelain", "--untracked-files=all", "--", *WRITES)
        if run.stdout.strip():
            raise RefusalError(
                "uncommitted changes under "
                + ", ".join(WRITES)
                + ": commit or discard them first, so `git diff` shows the sync and nothing else\n"
                + run.stdout.decode(errors="replace").rstrip()
            )

    def files(self, path: str) -> Files:
        """Return the tracked files of the lab skill at `path`, keyed by path inside it."""
        out = _git(self.root, "ls-files", "-s", "-z", "--", path).stdout.decode()
        found: Files = {}
        for record in filter(None, out.split("\0")):
            meta, rel = record.split("\t", 1)
            mode = meta.split()[0]
            found[rel.removeprefix(path + "/")] = Blob(mode, (self.root / rel).read_bytes())
        return found

    def write(self, rel: str, blob: Blob | None) -> None:
        """Write `blob` at `rel`, or delete the file there when it is None."""
        path = self.root / rel
        if blob is None:
            if path.exists():
                path.unlink()
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob.data)
        path.chmod(0o755 if blob.mode == "100755" else 0o644)

    def remove_skill(self, path: str) -> None:
        """Delete a skill's directory."""
        shutil.rmtree(self.root / path, ignore_errors=True)


def dump_attribution(records: dict[str, Any]) -> str:
    """Format the records as upstream/README.md shows them, each source on one line."""
    if not records:
        return "{}\n"
    out = ["{"]
    for i, (path, record) in enumerate(records.items()):
        out.append(f"  {json.dumps(path)}: {{")
        fields = list(record.items())
        for j, (key, value) in enumerate(fields):
            comma = "," if j < len(fields) - 1 else ""
            if key == "from" and isinstance(value, list):
                out.append('    "from": [')
                sources = [f"      {json.dumps(s, ensure_ascii=False)}" for s in value]
                out.append(",\n".join(sources))
                out.append(f"    ]{comma}")
            else:
                out.append(f"    {json.dumps(key)}: {json.dumps(value, ensure_ascii=False)}{comma}")
        out.append("  }" + ("," if i < len(records) - 1 else ""))
    out.append("}")
    return "\n".join(out) + "\n"


def regate(lab: Lab, add: set[str], drop: set[str]) -> list[str]:
    """Add and drop names in the two gate lists that exempt upstream text.

    Returns a line for each list that could not be edited, for the maintainer to do by hand.
    """
    misses: list[str] = []
    if not add and not drop:
        return misses
    vale = lab.root / VALE
    text = vale.read_text(encoding="utf-8") if vale.exists() else ""
    match = _VALE_RE.search(text)
    if match:
        names = {n.strip() for n in match.group(1).split(",") if n.strip()}
        names = sorted((names | add) - drop)
        text = text[: match.start(1)] + ",".join(names) + text[match.end(1) :]
        vale.write_text(text, encoding="utf-8")
    else:
        misses.append(f"`{VALE}` has no `[skills/{{...}}/*.md]` section")
    mdl = lab.root / MARKDOWNLINT
    text = mdl.read_text(encoding="utf-8") if mdl.exists() else ""
    lines = list(_MDL_RE.finditer(text))
    if lines:
        names = sorted(({m.group(2) for m in lines} | add) - drop)
        indent = lines[0].group(1)
        block = "".join(f'{indent}- "skills/{n}/**"\n' for n in names)
        text = text[: lines[0].start()] + block + text[lines[-1].end() :]
        mdl.write_text(text, encoding="utf-8")
    else:
        misses.append(f'`{MARKDOWNLINT}` has no `- "skills/<name>/**"` filter lines')
    return misses


# ---------------------------------------------------------------------------------------------
# Merging


@dataclass
class FileMerge:
    """One file of one tracked skill: the three inputs, what was written and what is left."""

    path: str  # repo-relative lab path
    base: Blob | None
    ours: Blob | None
    theirs: Blob | None
    result: Blob | None
    conflicts: int = 0
    why: str = ""  # a conflict that is not a text hunk, in words


def _merge_file(ours: bytes, base: bytes, theirs: bytes) -> tuple[bytes, int] | None:
    """Run `git merge-file` on three texts: the merged text and its conflict count, or None.

    `--diff3` is explicit, so a maintainer's `merge.conflictStyle` cannot change the result.
    """
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for name, data in (("lab", ours), ("pinned", base), ("upstream", theirs)):
            path = Path(tmp) / name
            path.write_bytes(data)
            paths.append(str(path))
        labels = ["-L", "lab", "-L", "pinned", "-L", "upstream"]
        run = subprocess.run(
            ["git", "merge-file", "-p", "--diff3", *labels, *paths],
            cwd=tmp,
            capture_output=True,
            check=False,
        )
    if run.returncode < 0 or run.returncode > 127:
        return None
    return run.stdout, run.returncode


def three_way(path: str, base: Files, ours: Files, theirs: Files) -> list[FileMerge]:
    """Merge every file of one skill, keyed by path inside it, with `base` as the pin."""
    merges = []
    for rel in sorted(set(base) | set(ours) | set(theirs)):
        b, o, t = base.get(rel), ours.get(rel), theirs.get(rel)
        merge = FileMerge(f"{path}/{rel}", b, o, t, o)
        if o == t or b == t:
            pass
        elif b == o:
            merge.result = t
        elif o is None:
            merge.conflicts, merge.why = 1, "deleted in the lab, changed upstream"
        elif t is None:
            merge.conflicts, merge.why = 1, "edited in the lab, deleted or renamed upstream"
        else:
            merged = _merge_file(o.data, b.data if b else b"", t.data)
            if merged is None:
                merge.conflicts, merge.why = 1, "changed on both sides, and git cannot merge it"
            else:
                merge.result, merge.conflicts = Blob(t.mode, merged[0]), merged[1]
        merges.append(merge)
    return merges


def _marked(ours: bytes, theirs: bytes) -> tuple[bytes, int] | None:
    """Every difference between two texts as a conflict, lab text first; None for binary."""
    try:
        a = ours.decode().splitlines(keepends=True)
        b = theirs.decode().splitlines(keepends=True)
    except UnicodeDecodeError:
        return None
    out: list[str] = []
    count = 0

    def chunk(lines: list[str]) -> list[str]:
        return (
            [*lines[:-1], lines[-1] if lines[-1].endswith("\n") else lines[-1] + "\n"]
            if lines
            else []
        )

    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            out += a[i1:i2]
            continue
        count += 1
        out += [
            "<<<<<<< lab\n",
            *chunk(a[i1:i2]),
            "=======\n",
            *chunk(b[j1:j2]),
            ">>>>>>> upstream\n",
        ]
    return "".join(out).encode(), count


def two_way(path: str, ours: Files, theirs: Files) -> list[FileMerge]:
    """With no pin to merge from, mark every difference between the lab copy and the tip."""
    merges = []
    for rel in sorted(set(ours) | set(theirs)):
        o, t = ours.get(rel), theirs.get(rel)
        merge = FileMerge(f"{path}/{rel}", None, o, t, o)
        if o == t or t is None:
            pass
        elif o is None:
            merge.result = t
        else:
            marked = _marked(o.data, t.data)
            if marked is None:
                merge.conflicts, merge.why = 1, "differs from upstream, and is not text"
            elif marked[1]:
                merge.result, merge.conflicts = Blob(t.mode, marked[0]), marked[1]
            else:
                merge.result = t
        merges.append(merge)
    return merges


@dataclass
class Result:
    """What one merge pin's sync read and did. The report is rendered from this alone.

    `files` holds every file of every tracked skill with its three inputs and what was
    written, removed skills included, so a check over the merge needs nothing else.
    """

    upstream: str
    pin: str  # repo-relative path of the pin file
    base: str
    tip: str
    now: Snapshot
    then: Snapshot | None  # None when the pinned commit is gone from the clone
    files: list[FileMerge] = field(default_factory=list)
    merged: dict[str, list[FileMerge]] = field(default_factory=dict)  # lab path -> its files
    deleted: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    forked: dict[str, str] = field(default_factory=dict)  # lab path -> upstream item
    notes: list[str] = field(default_factory=list)

    @property
    def pin_lost(self) -> bool:
        """Whether the sync fell back to a two-way diff."""
        return self.then is None

    @property
    def conflicts(self) -> list[FileMerge]:
        """Return the files left with something to resolve."""
        return [f for f in self.files if f.conflicts]


def _short(commit: str) -> str:
    return commit[:7]


def _lab_edited(base: Files, ours: Files) -> list[str]:
    return sorted(rel for rel in set(base) | set(ours) if base.get(rel) != ours.get(rel))


def sync_pin(lab: Lab, pin: Pin, clone: Clone, records: dict[str, Any]) -> Result:
    """Merge every skill one merge pin tracks, then move the pin to the tip."""
    tip = clone.tip()
    skills_dir = pin.data["skills_dir"]
    now = Snapshot(clone, tip, skills_dir)
    then = Snapshot(clone, pin.commit, skills_dir) if clone.has(pin.commit) else None
    rel_pin = pin.path.relative_to(lab.root).as_posix()
    result = Result(pin.upstream, rel_pin, pin.commit, tip, now, then)
    result.forked = {
        path: source.get("item")
        for path, record in records.items()
        for source in record.get("from", [])
        if source.get("upstream") == pin.upstream
    }
    originals = set(result.forked.values())

    for path, item in sorted(result.forked.items()):
        if item not in now.skills:
            result.deleted.append(
                f"`{item}`, the original of forked `{path}`, is gone upstream. The lab copy stays."
            )

    gone: set[str] = set()
    for item, path in sorted(pin.items.items()):
        if path in records:
            result.notes.append(f"`{path}` is tracked and forked at once, so it was not merged.")
            continue
        ours = lab.files(path)
        if item not in now.skills:
            base = then.files(item) if then is not None and item in then.skills else {}
            line = f"`{item}`: gone from upstream's tip, deleted or renamed. Removed `{path}`."
            edited = _lab_edited(base, ours) if then is not None else []
            if edited:
                names = ", ".join(f"`{rel}`" for rel in edited)
                line += f" It carried lab edits in {names}: port them by hand from git."
            result.files += [
                FileMerge(f"{path}/{rel}", base.get(rel), ours.get(rel), None, None)
                for rel in sorted(set(base) | set(ours))
            ]
            lab.remove_skill(path)
            del pin.items[item]
            gone.add(posixpath.basename(path))
            result.deleted.append(line)
            continue
        theirs = now.files(item)
        if then is None:
            merges = two_way(path, ours, theirs)
            result.notes += [
                f"`{m.path}` is only in the lab copy: a lab page, or a file upstream deleted. "
                "Without the pin the sync cannot tell, so it stays."
                for m in merges
                if m.theirs is None
            ]
        else:
            base = then.files(item) if item in then.skills else {}
            merges = three_way(path, base, ours, theirs)
        for merge in merges:
            if merge.result != merge.ours:
                lab.write(merge.path, merge.result)
        result.files += merges
        result.merged[path] = merges

    arrived: set[str] = set()
    candidates = sorted(now.listed() - set(pin.items) - originals - gone)
    if then is None:
        if candidates:
            names = ", ".join(f"`{n}`" for n in candidates)
            result.notes.append(
                f"Not added, because without the pin a new skill looks like a skipped one: {names}."
            )
    else:
        for name in sorted(set(candidates) - then.listed()):
            path = f"skills/{name}"
            if (lab.root / path).exists():
                result.notes.append(
                    f"`{name}` is new upstream, and `{path}` is taken: map it to another name "
                    "in the pin by hand (docs/adr/0013)."
                )
                continue
            for rel, blob in sorted(now.files(name).items()):
                lab.write(f"{path}/{rel}", blob)
            pin.items[name] = path
            arrived.add(name)
            result.added.append(f"`{name}`: added at `{path}` and mapped in the pin.")

    result.notes += regate(lab, arrived, gone)
    pin.data["commit"] = tip
    pin.save()
    return result


# ---------------------------------------------------------------------------------------------
# The report


def _section(title: str, lines: list[str]) -> list[str]:
    return [f"### {title}", "", *(f"- {line}" for line in lines), ""] if lines else []


def render(results: list[Result]) -> str:
    """Return the report in Markdown, so it can go into the pull request as it is."""
    out = ["# Upstream sync", ""]
    for r in results:
        out += [f"## {r.upstream}: `{_short(r.base)}` to `{_short(r.tip)}`", ""]
        if r.pin_lost:
            out += _section(
                "Pin lost",
                [
                    f"`{_short(r.base)}` is not in the clone: upstream rewrote its history. This "
                    "sync fell back to a two-way diff. Every difference between a lab copy and "
                    "upstream's tip is marked as a conflict, the lab's text first. Keep the "
                    "lab's edits and take upstream's text."
                ],
            )
        conflicts = []
        for f in r.conflicts:
            if f.why:
                conflicts.append(f"`{f.path}`: {f.why}. The lab's copy is in place.")
            else:
                conflicts.append(f"`{f.path}`: {f.conflicts} conflict(s) between the markers.")
        out += _section("Conflicts", conflicts)
        out += _section("Deleted upstream", r.deleted)
        out += _section("New skills", r.added)
        forked = [f"`{path}`, from `{item}`" for path, item in sorted(r.forked.items())]
        out += _section("Forked, not merged", forked)
        merged = []
        for path, merges in sorted(r.merged.items()):
            changed = sum(1 for m in merges if m.result != m.ours)
            merged.append(
                f"`{path}`: {changed} file(s) changed." if changed else f"`{path}`: unchanged."
            )
        out += _section("Merged", merged)
        out += _section("Notes", r.notes)
        moved = f"moved from `{_short(r.base)}` to `{_short(r.tip)}`"
        stayed = f"stays at `{_short(r.tip)}`: upstream has not moved"
        out += _section("Pin", [f"`{r.pin}` {moved if r.base != r.tip else stayed}."])
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------------------------------------
# Commands


def _clones(specs: list[str], pins: dict[str, Pin]) -> dict[str, Clone]:
    clones: dict[str, Clone] = {}
    for spec in specs:
        name, sep, path = spec.partition("=")
        if not sep or not name or not path:
            raise RefusalError(f"--clone takes NAME=DIR, not `{spec}`")
        if name not in pins:
            raise RefusalError(f"--clone names `{name}`, and there is no upstream/{name}/pin.json")
        clones[name] = Clone(Path(path).resolve())
    for name, pin in pins.items():
        if pin.data["sync"] == "merge" and name not in clones:
            raise RefusalError(
                f"no clone of `{name}`: run `git clone {pin.data['repo']} <dir>`, then pass "
                f"`--clone {name}=<dir>`"
            )
    return clones


def merge(lab: Lab, specs: list[str]) -> int:
    """Run the merge for every merge pin, print the report, and return the exit status."""
    pins = lab.pins()
    clones = _clones(specs, pins)
    lab.require_clean()
    records = lab.attribution()
    results = [
        sync_pin(lab, pin, clones[name], records)
        for name, pin in sorted(pins.items())
        if pin.data["sync"] == "merge"
    ]
    print(render(results), end="")
    return 1 if any(r.conflicts for r in results) else 0


def fork(lab: Lab, name: str, changes: str | None) -> int:
    """Move tracked skill `name` from its pin's name map to an attribution record."""
    path = f"skills/{name}"
    tracked = [
        (pin, item)
        for pin in lab.pins().values()
        if pin.data["sync"] == "merge"
        for item, mapped in pin.items.items()
        if mapped == path
    ]
    if not tracked:
        raise RefusalError(f"`{path}` is not a tracked skill: no merge pin maps it")
    records = lab.attribution()
    if path in records:
        raise RefusalError(f"`{path}` already has an attribution record")
    pin, item = tracked[0]
    record: dict[str, Any] = {
        "from": [{"upstream": pin.upstream, "item": item, "commit": pin.commit}]
    }
    if changes:
        record["changes"] = changes
    del pin.items[item]
    pin.save()
    records[path] = record
    lab.save_attribution(records)
    print(
        f"Forked `{path}`: removed `{item}` from upstream/{pin.upstream}/pin.json and recorded it "
        f"in {ATTRIBUTION} at `{_short(pin.commit)}`. Commit this on its own."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse the command line, run one command, and return its exit status."""
    parser = argparse.ArgumentParser(
        prog="upstream_sync.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--lab", type=Path, default=Path(), help="the lab tree (default: .)")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("merge", help="merge every tracked skill from its pin to the tip")
    run.add_argument(
        "--clone",
        action="append",
        default=[],
        metavar="NAME=DIR",
        help="a fresh clone of upstream NAME; one per merged upstream",
    )
    run.add_argument("--lab", type=Path, default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    split = commands.add_parser("fork", help="make a tracked skill lab-owned")
    split.add_argument("name", help="the skill's directory name under skills/")
    split.add_argument("--changes", help="one line on what the lab changes, for the record")
    split.add_argument("--lab", type=Path, default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    lab = Lab(args.lab.resolve())
    try:
        if args.command == "merge":
            return merge(lab, args.clone)
        return fork(lab, args.name, args.changes)
    except RefusalError as e:
        print(f"upstream_sync: refused, nothing written: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
