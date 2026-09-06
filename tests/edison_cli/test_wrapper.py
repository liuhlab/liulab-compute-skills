"""`bin/edison-cli`: the file that makes the command a bare name, and the loop it must not make.

Claude Code puts `<plugin-root>/bin` on PATH, so this wrapper is what turns every command in
`skills/lab-edison/` into the short form its pages already write — and what makes a permission
rule outlive a release, since the explicit spelling carries the plugin's version in its path.

Two properties, and both are about the shipped file rather than about a function. It has to be
committed EXECUTABLE, because the plugin cache is a clone and a mode 644 wrapper is a command
nobody can run. And it must exec the MODULE and never the console script: the script inside the
pixi environment wears this same name, this file is earlier on PATH, and `pixi run … edison-cli`
would therefore re-enter this file until the machine gives up. Neither is visible in Python, so
neither is asserted anywhere else.

The wrapper is not RUN here. Doing that builds a pixi environment of hundreds of megabytes, and
`tests/preflight.sh` is where this repo asks what a real machine has.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
WRAPPER = REPO / "bin" / "edison-cli"


def test_the_wrapper_is_there_and_the_preflight_looks_for_it_where_it_is() -> None:
    """`preflight.command` reports the bare spelling off this path, so the two must agree."""
    from edison_cli import preflight

    assert WRAPPER.is_file(), "bin/edison-cli is the whole of issue #51"
    assert preflight.WRAPPER == WRAPPER


def test_the_wrapper_is_executable_on_disk_and_in_the_index() -> None:
    """A plugin is installed by cloning this repo, so the mode git records is the mode shipped."""
    assert os.access(WRAPPER, os.X_OK), "bin/edison-cli is not executable"
    listed = subprocess.run(
        ["git", "ls-files", "-s", "bin/edison-cli"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert listed.startswith("100755 "), f"git has it at the wrong mode: {listed.strip()!r}"


def test_the_wrapper_execs_the_module_and_never_its_own_name() -> None:
    """The recursion guard. `edison-cli` here would mean this file, not the console script."""
    text = WRAPPER.read_text(encoding="utf-8")
    runs = [line.strip() for line in text.splitlines() if re.match(r"^\s*exec\b", line)]
    assert runs, "the wrapper execs nothing"
    for line in runs:
        assert "python -m edison_cli" in line, f"not the module entry point: {line}"
        assert not re.search(r"\bedison-cli\b", line), f"this execs itself: {line}"


def test_the_command_is_spelled_bare_only_where_the_shell_can_find_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`STOP:` is pasted into the caller's own shell, so the spelling has to work there.

    Both directions, because the two failures are opposite and both are silent: a bare name
    where nothing is on PATH is a stop command that does not run, and the explicit form where
    the wrapper IS on PATH is the version-carrying spelling issue #51 exists to remove.
    """
    from edison_cli import preflight

    monkeypatch.setenv("PATH", str(WRAPPER.parent))
    assert preflight.on_path()
    assert preflight.command() == "edison-cli"

    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    assert not preflight.on_path()
    assert preflight.command().startswith("pixi run --manifest-path ")
    assert preflight.command().endswith("/pyproject.toml edison-cli")


def test_the_wrapper_resolves_the_plugin_from_its_own_location() -> None:
    """An agent harness resets the working directory between calls, so nothing may depend on it."""
    text = WRAPPER.read_text(encoding="utf-8")
    assert 'dirname -- "$0"' in text
    assert "--manifest-path" in text, "an activated pixi environment of the user's must not win"
