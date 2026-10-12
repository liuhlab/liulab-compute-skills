"""Claude Code: the `liulab` marketplace updates itself once `autoUpdate` is on.

The switch is the `autoUpdate` key on the `liulab` entry under `extraKnownMarketplaces` in
the user settings, which `claude plugin marketplace add` writes without it. The script turns
it on and keeps everything else in the file.
"""

from __future__ import annotations

import json

from tests.lab_setup.conftest import FakeMachine


def test_a_fresh_machine_gets_the_liulab_marketplace_with_auto_update_on(
    machine: FakeMachine,
) -> None:
    """No settings file yet: the entry is written whole, with the GitHub source."""
    result = machine.run()

    settings = json.loads((machine.home / ".claude" / "settings.json").read_text())
    assert settings["extraKnownMarketplaces"]["liulab"] == {
        "source": {"source": "github", "repo": "liuhlab/liulab-skills"},
        "autoUpdate": True,
    }
    assert result.returncode == 0, result.stdout + result.stderr


def test_auto_update_is_added_to_the_entry_the_install_wrote_and_nothing_else_moves(
    machine: FakeMachine,
) -> None:
    """The member's other settings, and the entry's own source, survive untouched."""
    path = machine.home / ".claude" / "settings.json"
    before = {
        "model": "opus",
        "permissions": {"allow": ["Bash(edison-cli:*)"]},
        "extraKnownMarketplaces": {
            "liulab": {"source": {"source": "git", "url": "https://example.org/x.git"}},
            "other": {"source": {"source": "github", "repo": "someone/else"}},
        },
    }
    path.write_text(json.dumps(before))

    machine.run()

    after = json.loads(path.read_text())
    before["extraKnownMarketplaces"]["liulab"]["autoUpdate"] = True
    assert after == before


def test_a_settings_file_that_is_not_json_is_left_alone_and_the_run_fails(
    machine: FakeMachine,
) -> None:
    """Rewriting a file the script cannot read would lose whatever the member put there."""
    path = machine.home / ".claude" / "settings.json"
    path.write_text("{ not json")

    result = machine.run()

    assert path.read_text() == "{ not json"
    assert result.returncode == 1
    assert "settings.json" in result.stdout
