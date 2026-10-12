"""A lab side page beside an adopted skill meets the lab's writing gate.

A tracked skill's upstream text passes vale and markdownlint through an exemption that
names the skill (ADR 0012). A lab edit too long for an upstream file goes in a side page,
`<topic>.lab.md`, beside it: lab text in the skill's folder. These tests run the two tools
with the repo's own configuration on a copy of one adopted skill's folder, and check that
the exemption still covers the upstream page and no longer covers the side page.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
# A real adopted name, so the test reads the real exemption lists, not a fixture's.
SKILL = "skills/tdd"
UPSTREAM_PAGE = f"{SKILL}/tests.md"
SIDE_PAGE = f"{SKILL}/golden.lab.md"


def _tree(tmp_path: Path, text: str) -> Path:
    """Copy the gate's configuration into `tmp_path` and write `text` to both pages."""
    for name in (".vale.ini", ".markdownlint-cli2.yaml"):
        shutil.copy(REPO / name, tmp_path / name)
    shutil.copytree(REPO / "styles", tmp_path / "styles")
    for page in (UPSTREAM_PAGE, SIDE_PAGE):
        path = tmp_path / page
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp_path


def _run(tool: str, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run one gate tool from `cwd`, as `pixi run check` runs it from the repo root."""
    exe = shutil.which(tool)
    if exe is None:
        pytest.fail(f"{tool} is not on PATH; run the tests through `pixi run test`")
    return subprocess.run(
        [exe, *args], cwd=cwd, capture_output=True, text=True, check=False, timeout=120
    )


def test_markdownlint_holds_a_side_page_to_the_rules_upstream_is_spared(tmp_path: Path) -> None:
    """A page that opens on prose passes in upstream text and fails as a side page."""
    root = _tree(tmp_path, "A page that opens on prose, as upstream skill bodies do.\n")

    result = _run("markdownlint-cli2", cwd=root)
    report = result.stdout + result.stderr

    assert result.returncode == 1, report
    assert f"{SIDE_PAGE}:1" in report
    assert "MD041" in report
    assert UPSTREAM_PAGE not in report


def test_vale_caps_a_side_page_and_leaves_upstream_text_uncapped(tmp_path: Path) -> None:
    """1,300 words pass in upstream text and break the 1,200-word cap as a side page."""
    root = _tree(tmp_path, "# Golden fixtures\n\n" + "word " * 1300 + "\n")

    # Relative paths: an absolute one matches no `.vale.ini` section and checks nothing.
    result = _run("vale", "--output=line", UPSTREAM_PAGE, SIDE_PAGE, cwd=root)
    report = result.stdout + result.stderr

    assert result.returncode == 1, report
    assert f"{SIDE_PAGE}:1:1:Lab.LengthDoc" in report
    assert UPSTREAM_PAGE not in report
