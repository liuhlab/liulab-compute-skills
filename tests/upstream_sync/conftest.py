"""Fixture git repos for the upstream sync: an upstream with a history, and a lab tree.

The sync reads an upstream only through a clone and writes only the lab tree, so a test builds
both here and runs `scripts/upstream_sync.py` against them. The upstream keeps its skills in
buckets under `skills/` and lists them in `.claude-plugin/plugin.json`, as mattpocock/skills
does. The lab tree holds a flat copy of each adopted skill at the pin, the pin itself, the
attribution record and the two gate lists that exempt upstream text, as this repo does.

git reads no config but the test's own. A maintainer's global `commit.gpgsign`, hooks or
default branch would otherwise decide whether a fixture builds, and the real home directory
is never touched.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "upstream_sync.py"
UPSTREAM = "mattpocock"
PIN = f"upstream/{UPSTREAM}/pin.json"
ATTRIBUTION = "upstream/attribution.json"


def numbered(name: str) -> list[str]:
    """Ten body lines, far enough apart that edits to different lines merge cleanly."""
    return [f"Step {i} of {name}." for i in range(1, 11)]


def skill(name: str, lines: list[str] | None = None) -> str:
    """Return a `SKILL.md` for `name`: frontmatter, a title, then `lines` or ten numbered."""
    body = numbered(name) if lines is None else lines
    head = f"---\nname: {name}\ndescription: Fixture skill {name} for the sync tests.\n---\n"
    return head + f"\n# {name}\n\n" + "\n\n".join(body) + "\n"


class Tree:
    """A git repo on disk that a test writes, commits and reads by repo-relative path."""

    def __init__(self, root: Path, env: dict[str, str]) -> None:
        """Create the directory and an empty repo on `main`."""
        self.root = root
        self.env = env
        root.mkdir(parents=True)
        self.git("init", "-q", "-b", "main")

    def git(self, *args: str) -> str:
        """Run git in this repo and return its stripped stdout."""
        return subprocess.run(
            ["git", *args], cwd=self.root, env=self.env, capture_output=True, text=True, check=True
        ).stdout.strip()

    def show(self, commit: str, rel: str) -> str:
        """Return the text at `rel` in `commit`, exactly as committed."""
        return subprocess.run(
            ["git", "show", f"{commit}:{rel}"],
            cwd=self.root,
            env=self.env,
            capture_output=True,
            text=True,
            check=True,
        ).stdout

    def write(self, rel: str, text: str) -> None:
        """Write `text` at `rel`, creating directories on the way."""
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def read(self, rel: str) -> str:
        """Return the text at `rel`."""
        return (self.root / rel).read_text(encoding="utf-8")

    def exists(self, rel: str) -> bool:
        """Whether anything is at `rel`."""
        return (self.root / rel).exists()

    def remove(self, rel: str) -> None:
        """Delete the file or directory at `rel`."""
        path = self.root / rel
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    def commit(self, message: str = "fixture") -> str:
        """Commit everything and return the full commit."""
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def json(self, rel: str) -> dict:
        """Return the JSON object at `rel`."""
        return json.loads(self.read(rel))


class Upstream(Tree):
    """The upstream: skills in buckets under `skills/`, listed in its plugin manifest."""

    def __init__(self, root: Path, env: dict[str, str]) -> None:
        """Start with an empty manifest."""
        super().__init__(root, env)
        self.listed: list[str] = []
        self._manifest()

    def add(self, name: str, bucket: str = "engineering", text: str | None = None) -> None:
        """Add a skill at `skills/<bucket>/<name>` and list it in the manifest."""
        self.write(f"skills/{bucket}/{name}/SKILL.md", skill(name) if text is None else text)
        self.listed.append(f"./skills/{bucket}/{name}")
        self._manifest()

    def drop(self, name: str, bucket: str = "engineering") -> None:
        """Delete a skill's directory and take it out of the manifest."""
        self.remove(f"skills/{bucket}/{name}")
        self.listed.remove(f"./skills/{bucket}/{name}")
        self._manifest()

    def _manifest(self) -> None:
        manifest = {"name": "fixture-skills", "version": "1.0.0", "skills": self.listed}
        self.write(".claude-plugin/plugin.json", json.dumps(manifest, indent=2) + "\n")


class Lab(Tree):
    """The lab tree, holding adopted skills flat under `skills/<name>/`."""

    def sync(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run the sync script against this tree with `args` and return what it did."""
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args, "--lab", str(self.root)],
            cwd=self.root,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )

    def merge(
        self, clone: Upstream | None = None, **others: Upstream
    ) -> subprocess.CompletedProcess[str]:
        """Run `merge` with `clone` as mattpocock's clone, and `others` keyed by upstream name."""
        clones = ({UPSTREAM: clone} if clone else {}) | others
        args = [arg for name, up in clones.items() for arg in ("--clone", f"{name}={up.root}")]
        return self.sync("merge", *args)

    def gate_names(self) -> tuple[str, str]:
        """Return `.vale.ini` and `.markdownlint-cli2.yaml`, which hold the gate lists."""
        return self.read(".vale.ini"), self.read(".markdownlint-cli2.yaml")


def gate_files(names: list[str]) -> tuple[str, str]:
    """Return a `.vale.ini` and a `.markdownlint-cli2.yaml` exempting `names`, as the repo does."""
    vale = (
        "StylesPath = styles\n\n"
        f"[skills/{{{','.join(names)}}}/*.md]\n"
        "BasedOnStyles = Lab\nLab.LengthSkill = NO\n"
    )
    lines = "".join(f'      - "skills/{name}/**"\n' for name in names)
    mdl = (
        "gitignore: true\n\noverrides:\n  - filter:\n"
        f"{lines}"
        "    combine: merge\n    config:\n      MD041: false\n"
    )
    return vale, mdl


@pytest.fixture
def env(tmp_path: Path) -> dict[str, str]:
    """Return an environment where git reads only the fixture's identity, under a fake home."""
    home = tmp_path / "home"
    home.mkdir()
    clean = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    clean.update(
        HOME=str(home),
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_AUTHOR_NAME="Fixture",
        GIT_AUTHOR_EMAIL="fixture@example.invalid",
        GIT_COMMITTER_NAME="Fixture",
        GIT_COMMITTER_EMAIL="fixture@example.invalid",
    )
    return clean


@pytest.fixture
def upstream(tmp_path: Path, env: dict[str, str]) -> Upstream:
    """Return an upstream repo with nothing committed yet."""
    return Upstream(tmp_path / "upstream", env)


MakeLab = Callable[..., Lab]


@pytest.fixture
def make_lab(tmp_path: Path, env: dict[str, str]) -> MakeLab:
    """Build the lab tree from `upstream` at `base`: tracked and forked skills, pin, gate lists.

    `tracked` and `forked` map a skill name to its upstream bucket. Each skill is copied flat
    to `skills/<name>/` byte for byte, as adopting one does, and the tree is committed.
    """

    def build(
        upstream: Upstream,
        base: str,
        tracked: dict[str, str],
        forked: dict[str, str] | None = None,
    ) -> Lab:
        forked = forked or {}
        lab = Lab(tmp_path / "lab", env)
        for name, bucket in {**tracked, **forked}.items():
            prefix = f"skills/{bucket}/{name}/"
            for rel in upstream.git("ls-tree", "-r", "--name-only", base, prefix).splitlines():
                lab.write(f"skills/{name}/{rel.removeprefix(prefix)}", upstream.show(base, rel))
        pin = {
            "repo": "https://example.invalid/fixture-skills",
            "commit": base,
            "sync": "merge",
            "skills_dir": "skills",
            "items": {name: f"skills/{name}" for name in tracked},
        }
        lab.write(PIN, json.dumps(pin, indent=2) + "\n")
        lab.write(f"upstream/{UPSTREAM}/LICENSE", "MIT License\n")
        records = {
            f"skills/{name}": {"from": [{"upstream": UPSTREAM, "item": name, "commit": base}]}
            for name in forked
        }
        lab.write(ATTRIBUTION, json.dumps(records, indent=2) + "\n")
        vale, mdl = gate_files(sorted({**tracked, **forked}))
        lab.write(".vale.ini", vale)
        lab.write(".markdownlint-cli2.yaml", mdl)
        lab.commit("adopt")
        return lab

    return build
