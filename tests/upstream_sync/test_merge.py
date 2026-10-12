"""The per-file three-way merge: the pin is the base, upstream's tip is theirs, the lab is ours.

A tracked skill's upstream text changes only by a lab edit, so most of a sync is upstream's
changes landing around the lab's. These tests read the merged files and the report, and the
exit status that tells the maintainer whether anything is left to resolve.
"""

from __future__ import annotations

from pathlib import Path

from tests.upstream_sync.conftest import PIN, MakeLab, Upstream, numbered, skill


def test_a_clean_merge_takes_upstream_changes_and_keeps_lab_edits(
    upstream: Upstream, make_lab: MakeLab
) -> None:
    """Upstream rewrites one line, the lab added another: both survive, and the run exits 0."""
    upstream.add("grilling", bucket="productivity")
    base = upstream.commit()
    lab = make_lab(upstream, base, tracked={"grilling": "productivity"})
    lines = numbered("grilling")
    lab_lines = [*lines[:8], "A lab line: run it on the cluster.", *lines[8:]]
    lab.write("skills/grilling/SKILL.md", skill("grilling", lab_lines))
    lab.write("skills/grilling/LAB-SCIENCE.md", "# Lab side page\n")
    lab.commit("lab edit")
    up_lines = ["Step 1 of grilling, rewritten upstream.", *lines[1:]]
    upstream.write("skills/productivity/grilling/SKILL.md", skill("grilling", up_lines))
    upstream.write("skills/productivity/grilling/NEW.md", "# New upstream page\n")
    upstream.commit()

    run = lab.merge(upstream)

    assert run.returncode == 0, run.stdout + run.stderr
    assert lab.read("skills/grilling/SKILL.md") == skill("grilling", [up_lines[0], *lab_lines[1:]])
    assert lab.read("skills/grilling/NEW.md") == "# New upstream page\n"
    assert lab.read("skills/grilling/LAB-SCIENCE.md") == "# Lab side page\n"
    assert "skills/grilling" in run.stdout
    assert "Conflicts" not in run.stdout
    assert lab.json(PIN)["items"] == {"grilling": "skills/grilling"}


def test_a_conflict_is_left_between_markers_and_the_run_exits_1(
    upstream: Upstream, make_lab: MakeLab
) -> None:
    """Both sides rewrote one line: the file carries all three texts and the report names it."""
    upstream.add("tdd")
    base = upstream.commit()
    lab = make_lab(upstream, base, tracked={"tdd": "engineering"})
    lines = numbered("tdd")
    lab_lines = [*lines[:4], "Step 5, the lab's way.", *lines[5:]]
    lab.write("skills/tdd/SKILL.md", skill("tdd", lab_lines))
    lab.commit("lab edit")
    up_lines = [*lines[:4], "Step 5, upstream's way.", *lines[5:]]
    upstream.write("skills/engineering/tdd/SKILL.md", skill("tdd", up_lines))
    upstream.commit()

    run = lab.merge(upstream)

    assert run.returncode == 1, run.stdout + run.stderr
    assert (
        "<<<<<<< lab\nStep 5, the lab's way.\n"
        "||||||| pinned\nStep 5 of tdd.\n"
        "=======\nStep 5, upstream's way.\n>>>>>>> upstream\n"
    ) in lab.read("skills/tdd/SKILL.md")
    assert "### Conflicts" in run.stdout
    assert "`skills/tdd/SKILL.md`: 1 conflict(s)" in run.stdout


def test_a_file_the_lab_edited_and_upstream_deleted_is_kept_and_reported(
    upstream: Upstream, make_lab: MakeLab
) -> None:
    """Deleting a file the lab changed would lose the edit, so it stays and counts as a conflict."""
    upstream.add("tdd")
    upstream.write("skills/engineering/tdd/mocking.md", "# Mocking\n")
    base = upstream.commit()
    lab = make_lab(upstream, base, tracked={"tdd": "engineering"})
    lab.write("skills/tdd/mocking.md", "# Mocking\n\nA lab line about fixtures.\n")
    lab.commit("lab edit")
    upstream.remove("skills/engineering/tdd/mocking.md")
    upstream.commit()

    run = lab.merge(upstream)

    assert run.returncode == 1, run.stdout + run.stderr
    assert lab.read("skills/tdd/mocking.md") == "# Mocking\n\nA lab line about fixtures.\n"
    assert "`skills/tdd/mocking.md`: edited in the lab, deleted or renamed upstream" in run.stdout


def test_a_bucket_move_upstream_costs_nothing(upstream: Upstream, make_lab: MakeLab) -> None:
    """The skill is found by its frontmatter name, so moving its directory is not a deletion."""
    upstream.add("wizard", bucket="in-progress")
    base = upstream.commit()
    lab = make_lab(upstream, base, tracked={"wizard": "in-progress"})
    lines = numbered("wizard")
    lab_lines = [*lines, "A lab line at the end."]
    lab.write("skills/wizard/SKILL.md", skill("wizard", lab_lines))
    lab.commit("lab edit")
    upstream.drop("wizard", bucket="in-progress")
    upstream.add("wizard", text=skill("wizard", ["Step 1, after graduating.", *lines[1:]]))
    upstream.commit()

    run = lab.merge(upstream)

    assert run.returncode == 0, run.stdout + run.stderr
    assert lab.read("skills/wizard/SKILL.md") == skill(
        "wizard", ["Step 1, after graduating.", *lab_lines[1:]]
    )
    assert "Deleted upstream" not in run.stdout
    assert lab.json(PIN)["items"] == {"wizard": "skills/wizard"}


def test_the_pin_moves_to_upstreams_tip(upstream: Upstream, make_lab: MakeLab) -> None:
    """After the merge the pin names the tip in full, and nothing else in it changes."""
    upstream.add("grilling", bucket="productivity")
    base = upstream.commit()
    lab = make_lab(upstream, base, tracked={"grilling": "productivity"})
    before = lab.json(PIN)
    upstream.write("skills/productivity/grilling/extra.md", "# Extra\n")
    tip = upstream.commit()

    run = lab.merge(upstream)

    assert run.returncode == 0, run.stdout + run.stderr
    assert lab.json(PIN) == {**before, "commit": tip}
    assert lab.read(PIN).startswith('{\n  "repo": ')
    assert f"moved from `{base[:7]}` to `{tip[:7]}`" in run.stdout


def test_a_lost_pin_falls_back_to_a_two_way_diff_and_says_so(
    upstream: Upstream, make_lab: MakeLab, env: dict[str, str], tmp_path: Path
) -> None:
    """Upstream rewrote its history, so every difference is marked and the run exits 1."""
    upstream.add("grilling", bucket="productivity")
    base = upstream.commit()
    lab = make_lab(upstream, base, tracked={"grilling": "productivity"})
    lines = numbered("grilling")
    lab.write("skills/grilling/SKILL.md", skill("grilling", [*lines, "A lab line."]))
    lab.write("skills/grilling/LAB.md", "# Lab side page\n")
    lab.commit("lab edit")
    rewritten = Upstream(tmp_path / "rewritten", env)
    new_text = skill("grilling", ["Step 1, new.", *lines[1:]])
    rewritten.add("grilling", bucket="productivity", text=new_text)
    rewritten.write("skills/productivity/grilling/NEW.md", "# New\n")
    tip = rewritten.commit("history rewritten")

    run = lab.merge(rewritten)

    assert run.returncode == 1, run.stdout + run.stderr
    assert "### Pin lost" in run.stdout
    assert "two-way diff" in run.stdout
    text = lab.read("skills/grilling/SKILL.md")
    assert "<<<<<<< lab\nStep 1 of grilling.\n=======\nStep 1, new.\n>>>>>>> upstream\n" in text
    assert "<<<<<<< lab\n\nA lab line.\n=======\n>>>>>>> upstream\n" in text
    assert lab.read("skills/grilling/NEW.md") == "# New\n"
    assert lab.read("skills/grilling/LAB.md") == "# Lab side page\n"
    assert "`skills/grilling/LAB.md` is only in the lab copy" in run.stdout
    assert lab.json(PIN)["commit"] == tip
