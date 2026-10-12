"""`edison-cli` as a bare command in every agent: a link on PATH into the marketplace clone.

Only Claude Code puts a plugin's `bin/` on PATH. A link to the clone's launcher, in a user
bin folder the member's shell already searches, gives Codex and Kimi Code the same command,
and the launcher follows that link back to its project. A file already there is the
member's, and stays.
"""

from __future__ import annotations

from tests.lab_setup.conftest import FakeMachine


def test_the_launcher_is_linked_into_the_user_bin_folder_on_path(machine: FakeMachine) -> None:
    """The link points at the clone's launcher, by absolute path."""
    result = machine.run()

    link = machine.bin_dir / "edison-cli"
    assert link.is_symlink()
    assert link.readlink() == machine.clone / "bin" / "edison-cli"
    assert result.returncode == 0, result.stdout + result.stderr


def test_home_bin_is_used_when_it_is_the_user_folder_on_path(machine: FakeMachine) -> None:
    """`~/bin` is the older convention, and some machines have only that one."""
    home_bin = machine.home / "bin"
    home_bin.mkdir()

    machine.run(path=[machine.stubs, home_bin])

    assert (home_bin / "edison-cli").is_symlink()
    assert not (machine.bin_dir / "edison-cli").exists()


def test_no_user_bin_folder_on_path_means_no_link_and_a_message(machine: FakeMachine) -> None:
    """A folder the shell never searches would make a link nobody can call."""
    result = machine.run(path=[machine.stubs])

    assert not (machine.bin_dir / "edison-cli").exists()
    assert "edison-cli" in result.stdout
    assert "skipped" in result.stdout
    assert result.returncode == 0, result.stdout + result.stderr


def test_another_edison_cli_already_there_is_left_alone(machine: FakeMachine) -> None:
    """The script removes nothing, so someone else's command keeps its name."""
    theirs = machine.bin_dir / "edison-cli"
    theirs.write_text("#!/bin/sh\necho mine\n")

    result = machine.run()

    assert not theirs.is_symlink()
    assert theirs.read_text() == "#!/bin/sh\necho mine\n"
    assert "~/.local/bin/edison-cli" in result.stdout
