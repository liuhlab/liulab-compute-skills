"""Kimi Code: the marketplace clone's skills folder in `extra_skill_dirs`.

Kimi reads neither plugin format, but it reads skill folders live, so pointing it at the
clone Claude Code keeps current is how it updates. The key is a top-level array in
`config.toml`, which the member may also use for their own folders; theirs survive, and so
does every other line of the file.
"""

from __future__ import annotations

import tomllib

from tests.lab_setup.conftest import FakeMachine

ENTRY = "~/.claude/plugins/marketplaces/liulab/skills"


def config(machine: FakeMachine) -> str:
    """Kimi's config file as text."""
    return (machine.home / ".kimi-code" / "config.toml").read_text()


def write_config(machine: FakeMachine, text: str) -> None:
    """Give Kimi a config file."""
    (machine.home / ".kimi-code" / "config.toml").write_text(text)


def test_kimi_with_no_config_gets_one_holding_the_clone(machine: FakeMachine) -> None:
    """Kimi writes its config on first run; before that the script starts it."""
    machine.run()

    assert tomllib.loads(config(machine)) == {"extra_skill_dirs": [ENTRY]}


def test_the_entry_goes_above_the_first_table_and_every_other_line_survives(
    machine: FakeMachine,
) -> None:
    """A top-level key after a table header would land inside that table."""
    before = '# my settings\ndefault_model = "k2"\n\n[providers.moonshot]\ntype = "kimi"\n'
    write_config(machine, before)

    machine.run()

    after = config(machine)
    assert tomllib.loads(after) == {
        "default_model": "k2",
        "extra_skill_dirs": [ENTRY],
        "providers": {"moonshot": {"type": "kimi"}},
    }
    assert after.replace(f'extra_skill_dirs = ["{ENTRY}"]\n', "") == before


def test_entries_the_member_wrote_stay_and_the_clone_is_added_after_them(
    machine: FakeMachine,
) -> None:
    """A multi-line array with a comment: their entries, their comment, their order."""
    before = (
        'default_model = "k2"\n'
        "extra_skill_dirs = [\n"
        '  "/opt/team-skills",  # the team folder\n'
        "  '~/my-skills',\n"
        "]\n"
        "\n"
        "[thinking]\n"
        "enabled = true\n"
    )
    write_config(machine, before)

    machine.run()

    after = config(machine)
    assert tomllib.loads(after)["extra_skill_dirs"] == ["/opt/team-skills", "~/my-skills", ENTRY]
    assert tomllib.loads(after)["thinking"] == {"enabled": True}
    for line in before.splitlines():
        assert line in after.splitlines()


def test_a_one_line_array_gets_the_clone_appended(machine: FakeMachine) -> None:
    """The common hand-written form."""
    write_config(machine, 'extra_skill_dirs = ["/opt/team-skills"]\n')

    machine.run()

    assert tomllib.loads(config(machine))["extra_skill_dirs"] == ["/opt/team-skills", ENTRY]


def test_the_clone_already_listed_by_its_full_path_is_not_listed_twice(
    machine: FakeMachine,
) -> None:
    """Kimi expands `~/` itself, so the absolute spelling of the same folder counts."""
    text = f'extra_skill_dirs = ["{machine.clone / "skills"}"]\n'
    write_config(machine, text)

    machine.run()

    assert config(machine) == text


def test_a_machine_without_kimi_is_told_so_and_gets_no_kimi_folder(
    machine: FakeMachine,
) -> None:
    """No Kimi home means no Kimi; creating one would make Kimi look installed."""
    (machine.home / ".kimi-code").rmdir()

    result = machine.run()

    assert not (machine.home / ".kimi-code").exists()
    assert "kimi" in result.stdout
    assert "skipped" in result.stdout
    assert result.returncode == 0, result.stdout + result.stderr


def test_a_config_that_is_not_toml_is_left_alone_and_the_run_fails(
    machine: FakeMachine,
) -> None:
    """The script cannot add to a file it cannot read without risking the rest of it."""
    write_config(machine, "extra_skill_dirs = [\n")

    result = machine.run()

    assert config(machine) == "extra_skill_dirs = [\n"
    assert result.returncode == 1
    assert "config.toml" in result.stdout
