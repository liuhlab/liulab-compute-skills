"""No marketplace clone: the script says so and changes nothing.

Kimi Code reads its skills from the clone and the `edison-cli` link points into it, so a
machine without one has nothing to set up. That happens before the two install commands, or
if Claude Code ever moves its clone; either way the member has to hear it, and Kimi must not
be pointed at a folder that is not there.
"""

from __future__ import annotations

import shutil

from tests.lab_setup.conftest import FakeMachine


def test_without_a_clone_it_refuses_names_the_folder_and_writes_nothing(
    machine: FakeMachine,
) -> None:
    """No Kimi entry, no settings, no link, no Codex install: every file is as it was."""
    shutil.rmtree(machine.clone)
    before = machine.snapshot()

    result = machine.run()

    assert result.returncode == 1
    assert "~/.claude/plugins/marketplaces/liulab" in result.stdout
    assert "claude plugin marketplace add liuhlab/liulab-skills" in result.stdout
    assert machine.snapshot() == before
    assert not (machine.home / ".kimi-code" / "config.toml").exists()
    assert machine.codex_calls() == []
