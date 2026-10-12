"""The lab defaults: one marked block in each agent's user-level instructions file.

The block points Claude Code, Codex and Kimi Code at one page in the marketplace clone, so a
change to the page reaches every machine with no rerun. The files are the member's own: text
outside the block is theirs and survives, and a rerun replaces only the block.
"""

from __future__ import annotations

import re
from pathlib import Path

from tests.lab_setup.conftest import REPO, FakeMachine

PAGE = "~/.claude/plugins/marketplaces/liulab/skills/lab-setup/references/defaults.md"
BEGIN = "<!-- BEGIN lab defaults"
END = "<!-- END lab defaults -->"


def files(machine: FakeMachine) -> dict[str, Path]:
    """Each agent's user-level instructions file in the fake home."""
    home = machine.home
    return {
        "Claude Code": home / ".claude" / "CLAUDE.md",
        "Codex": home / ".codex" / "AGENTS.md",
        "Kimi Code": home / ".kimi-code" / "AGENTS.md",
    }


def blocks(text: str) -> list[str]:
    """Every marked block in `text`, markers included."""
    found, start = [], text.find(BEGIN)
    while start >= 0:
        end = text.index(END, start) + len(END)
        found.append(text[start:end])
        start = text.find(BEGIN, end)
    return found


def test_a_fresh_machine_points_all_three_agents_at_the_page(machine: FakeMachine) -> None:
    """One block per file, each naming the page in the clone that Claude Code keeps current."""
    result = machine.run()

    for agent, path in files(machine).items():
        found = blocks(path.read_text())
        assert len(found) == 1, agent
        assert PAGE in found[0], agent
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_members_own_text_stays_and_the_block_goes_below_it(machine: FakeMachine) -> None:
    """A file that ends without a newline still keeps every byte the member wrote."""
    path = files(machine)["Claude Code"]
    path.parent.mkdir(parents=True, exist_ok=True)
    before = "# My rules\n\nUse uv, never conda."
    path.write_text(before)

    machine.run()

    after = path.read_text()
    assert after.startswith(before + "\n")
    assert after[len(before) :].strip() == blocks(after)[0]


def test_a_rerun_replaces_only_the_block(machine: FakeMachine) -> None:
    """An older release's block, with text around it: the text stays, the block is current."""
    path = files(machine)["Kimi Code"]
    top, bottom = "# Mine\n\nAlways answer in English.\n\n", "\n## Later notes\n\nKeep me.\n"
    old = f"{BEGIN} from an older release -->\n## Lab defaults\n\nRead the old page.\n{END}\n"
    path.write_text(top + old + bottom)

    machine.run()

    after = path.read_text()
    (block,) = blocks(after)
    assert after == top + block + "\n" + bottom
    assert block == blocks(files(machine)["Codex"].read_text())[0]
    assert "old page" not in after


def test_markers_that_do_not_pair_are_left_alone_and_the_run_fails(machine: FakeMachine) -> None:
    """With no end marker, replacing "the block" would eat the member's text below it."""
    torn = f"{BEGIN} -->\n## Lab defaults\n\n# My own section, written below by hand\n"
    twice = f"{BEGIN} -->\nOne.\n{END}\n\n{BEGIN} -->\nTwo.\n{END}\n"
    claude_md, kimi_md = files(machine)["Claude Code"], files(machine)["Kimi Code"]
    claude_md.parent.mkdir(parents=True, exist_ok=True)
    claude_md.write_text(torn)
    kimi_md.write_text(twice)

    result = machine.run()

    assert claude_md.read_text() == torn
    assert kimi_md.read_text() == twice
    assert result.returncode == 1
    failed = [line for line in result.stdout.splitlines() if line.startswith("failed")]
    assert any("~/.claude/CLAUDE.md" in line for line in failed), result.stdout
    assert any("~/.kimi-code/AGENTS.md" in line for line in failed), result.stdout


def test_an_agent_that_is_not_installed_is_skipped_and_gets_no_folder(
    machine: FakeMachine,
) -> None:
    """No Codex on PATH and no Kimi home: Claude Code alone is pointed at the page."""
    (machine.home / ".kimi-code").rmdir()

    result = machine.run("--only", "defaults", path=[machine.bin_dir])

    assert not (machine.home / ".codex").exists()
    assert not (machine.home / ".kimi-code").exists()
    assert len(blocks(files(machine)["Claude Code"].read_text())) == 1
    skipped = [line for line in result.stdout.splitlines() if line.startswith("skipped")]
    assert any("Codex" in line for line in skipped), result.stdout
    assert any("Kimi Code" in line for line in skipped), result.stdout
    assert result.returncode == 0, result.stdout + result.stderr


def test_a_dry_run_says_which_files_gain_a_block_and_which_get_theirs_replaced(
    machine: FakeMachine,
) -> None:
    """What the member is asked to agree to, before anything is written."""
    old = f"{BEGIN} -->\nRead the old page.\n{END}\n"
    files(machine)["Kimi Code"].write_text(old)

    result = machine.run("--only", "defaults", "--dry-run")

    lines = result.stdout.splitlines()
    assert any(
        line.startswith("would change") and "add" in line and "~/.claude/CLAUDE.md" in line
        for line in lines
    ), result.stdout
    assert any(
        line.startswith("would change") and "replace" in line and "~/.kimi-code/AGENTS.md" in line
        for line in lines
    ), result.stdout
    assert files(machine)["Kimi Code"].read_text() == old
    assert not files(machine)["Claude Code"].exists()


def test_a_codex_override_file_is_reported_because_codex_reads_it_instead(
    machine: FakeMachine,
) -> None:
    """Codex reads `AGENTS.override.md` in place of `AGENTS.md` while it has text."""
    override = machine.home / ".codex" / "AGENTS.override.md"
    override.parent.mkdir()
    override.write_text("Answer tersely this week.\n")

    result = machine.run("--only", "defaults")

    assert override.read_text() == "Answer tersely this week.\n"
    assert len(blocks(files(machine)["Codex"].read_text())) == 1
    codex = [line for line in result.stdout.splitlines() if "~/.codex/AGENTS.md" in line]
    (line,) = codex
    assert "AGENTS.override.md" in line, result.stdout


def follow_the_block(tmp_path: Path) -> tuple[Path, Path]:
    """Set up a home whose marketplace clone is this repo; return the clone and the page."""
    machine = FakeMachine(tmp_path)
    machine.clone.parent.mkdir(parents=True)
    machine.clone.symlink_to(REPO, target_is_directory=True)
    machine.run("--only", "defaults")
    (block,) = blocks(files(machine)["Claude Code"].read_text())
    (pointer,) = re.findall(r"^@~/(\S+)$", block, re.MULTILINE)
    return machine.clone, machine.home / pointer


def test_the_block_leads_to_a_page_the_plugin_ships_and_on_to_every_seed_page(
    tmp_path: Path,
) -> None:
    """If upstream renames a seed page, the defaults page points at nothing: caught here."""
    clone, page = follow_the_block(tmp_path)

    assert page.is_file(), page
    named = set(re.findall(r"`(skills/[^`\s]+)`", page.read_text()))
    for seed in ("issue-tracker-github.md", "triage-labels.md", "domain.md"):
        assert f"skills/setup-matt-pocock-skills/{seed}" in named, seed
    assert "skills/hq-mode/references/working-style.md" in named
    for path in sorted(named):
        assert (clone / path).exists(), f"the defaults page names {path}, which does not ship"


def test_the_page_keeps_every_lab_line_and_says_what_a_repo_page_overrides(
    tmp_path: Path,
) -> None:
    """The lines the lab adds to upstream's seeds, each as the words that must stay in it."""
    _, page = follow_the_block(tmp_path)
    text = " ".join(page.read_text().split())

    for words in (
        ("missing label", "first use"),
        ("public", "hostnames", "usernames", "key paths", "ssh output"),
        ("`lab-hpc`", "before any ssh or Slurm"),
        ("never compute on a login node",),
        ("`ircbc`", "hangs", "VPN"),
        ("non-trivial task", "working-style page first"),
        ("`docs/agents/`", "overrides only that one default"),
    ):
        for word in words:
            assert word.lower() in text.lower(), (word, words)
