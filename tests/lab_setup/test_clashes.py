"""The report of user-level skills that take a name the plugin ships.

Skills are called by bare names, so an old copy of `grilling` in a user folder shadows the
plugin's in all three agents without a word. The script lists every such copy with its path
and changes none of them: what to do with each is the member's call. The shipped names are
read from the marketplace clone, which is what Kimi loads and what the next update installs.
"""

from __future__ import annotations

from tests.lab_setup.conftest import FakeMachine, skill


def reported(stdout: str) -> str:
    """Keep the report's clash lines: the ones whose status is `clash`."""
    return "\n".join(line for line in stdout.splitlines() if line.startswith("clash "))


def test_every_user_level_copy_of_a_shipped_name_is_listed_with_its_path(
    machine: FakeMachine,
) -> None:
    """One planted clash per folder the agents read, each named by its own path."""
    home = machine.home
    skill(home / ".claude" / "skills", "grilling")
    elsewhere = skill(machine.root / "old-checkout" / "skills", "lab-hpc")
    (home / ".agents" / "skills").mkdir(parents=True)
    (home / ".agents" / "skills" / "lab-hpc").symlink_to(elsewhere)
    skill(home / ".codex" / "skills", "lab-setup")
    skill(home / ".kimi-code" / "skills", "grilling")
    (home / ".kimi-code" / "config.toml").write_text('extra_skill_dirs = ["~/team-skills"]\n')
    skill(home / "team-skills", "lab-hpc")

    result = machine.run()

    for path in (
        "~/.claude/skills/grilling",
        "~/.agents/skills/lab-hpc",
        "~/.codex/skills/lab-setup",
        "~/.kimi-code/skills/grilling",
        "~/team-skills/lab-hpc",
    ):
        assert path in reported(result.stdout), path
    assert (elsewhere / "SKILL.md").exists()
    assert (home / ".claude" / "skills" / "grilling" / "SKILL.md").exists()


def test_a_skill_renamed_in_its_frontmatter_clashes_by_that_name(machine: FakeMachine) -> None:
    """Codex and Kimi call a skill by the `name:` it declares, whatever its folder is called."""
    folder = skill(machine.home / ".agents" / "skills", "old-grill")
    (folder / "SKILL.md").write_text("---\nname: grilling\ndescription: Old.\n---\n")

    result = machine.run()

    assert "~/.agents/skills/old-grill" in reported(result.stdout)


def test_skills_with_names_of_their_own_are_not_listed(machine: FakeMachine) -> None:
    """A member's own skills are what user folders are for."""
    skill(machine.home / ".claude" / "skills", "my-analysis")

    result = machine.run()

    assert "my-analysis" not in result.stdout
    assert reported(result.stdout) == ""


def test_the_clone_itself_is_not_reported_as_a_clash(machine: FakeMachine) -> None:
    """After a run Kimi lists the clone among its folders; the clone is the plugin, not a copy."""
    machine.run()

    result = machine.run()

    assert "marketplaces" in (machine.home / ".kimi-code" / "config.toml").read_text()
    assert reported(result.stdout) == ""
