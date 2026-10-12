"""Dropped edits: a line the lab added against the old pin that is gone after the merge.

This is the guard that keeps a lab edit from vanishing without a word. The merge reports it,
and `recheck` reports it again once the maintainer has resolved the conflicts, because a
resolution is where an edit is most easily lost. Both are deterministic and cost no tokens.
"""

from __future__ import annotations

from tests.upstream_sync.conftest import Lab, MakeLab, Upstream, numbered, skill


def test_the_lab_edits_of_a_skill_upstream_deleted_are_listed(
    upstream: Upstream, make_lab: MakeLab
) -> None:
    """Each line the lab added is named, and a whole lab page is named once, with its size."""
    upstream.add("grilling", bucket="productivity")
    upstream.add("resolving-merge-conflicts")
    base = upstream.commit()
    lab = make_lab(
        upstream,
        base,
        tracked={"grilling": "productivity", "resolving-merge-conflicts": "engineering"},
    )
    lines = numbered("resolving-merge-conflicts")
    lab_line = "For a notebook, resolve with `nbdime`."
    lab.write(
        "skills/resolving-merge-conflicts/SKILL.md",
        skill("resolving-merge-conflicts", [*lines[:3], lab_line, *lines[3:]]),
    )
    lab.write("skills/resolving-merge-conflicts/NOTEBOOKS.md", "# nbdime\n\nTwo lines.\n")
    lab.commit("lab edit")
    upstream.drop("resolving-merge-conflicts")
    upstream.commit("retire the skill")

    run = lab.merge(upstream)

    assert run.returncode == 0, run.stdout + run.stderr
    assert (
        "### Dropped edits\n\n"
        "- `skills/resolving-merge-conflicts/NOTEBOOKS.md`: a lab file, gone with its 2 line(s).\n"
        f"- `skills/resolving-merge-conflicts/SKILL.md`: {lab_line}\n"
    ) in run.stdout


def test_a_clean_merge_drops_nothing(upstream: Upstream, make_lab: MakeLab) -> None:
    """Upstream's changes land around the lab's line, and the report has no section for drops."""
    upstream.add("tdd")
    base = upstream.commit()
    lab = make_lab(upstream, base, tracked={"tdd": "engineering"})
    lines = numbered("tdd")
    lab.write("skills/tdd/SKILL.md", skill("tdd", [*lines, "A golden fixture is a test."]))
    lab.commit("lab edit")
    upstream.write("skills/engineering/tdd/SKILL.md", skill("tdd", ["Step 1, new.", *lines[1:]]))
    upstream.commit()

    run = lab.merge(upstream)

    assert run.returncode == 0, run.stdout + run.stderr
    assert "skills/tdd" in run.stdout
    assert "Dropped edits" not in run.stdout


def _conflicted_tdd(upstream: Upstream, make_lab: MakeLab) -> tuple[Lab, list[str], str, str]:
    """Merge a `tdd` whose step 5 both sides rewrote; return the lab, the lines and both steps."""
    upstream.add("tdd")
    base = upstream.commit()
    lab = make_lab(upstream, base, tracked={"tdd": "engineering"})
    lines = numbered("tdd")
    ours, theirs = "Step 5, with a golden fixture.", "Step 5, upstream's way."
    lab.write("skills/tdd/SKILL.md", skill("tdd", [*lines[:4], ours, *lines[5:]]))
    lab.commit("lab edit")
    upstream.write(
        "skills/engineering/tdd/SKILL.md", skill("tdd", [*lines[:4], theirs, *lines[5:]])
    )
    upstream.commit()
    assert lab.merge(upstream).returncode == 1
    return lab, lines, ours, theirs


def test_recheck_names_a_lab_line_a_resolution_dropped(
    upstream: Upstream, make_lab: MakeLab
) -> None:
    """Taking upstream's side of a conflict loses the lab's line: recheck says so and exits 1."""
    lab, lines, ours, theirs = _conflicted_tdd(upstream, make_lab)
    lab.write("skills/tdd/SKILL.md", skill("tdd", [*lines[:4], theirs, *lines[5:]]))

    run = lab.recheck(upstream)

    assert run.returncode == 1, run.stdout + run.stderr
    assert f"### Dropped edits\n\n- `skills/tdd/SKILL.md`: {ours}\n" in run.stdout


def test_recheck_passes_a_resolution_that_keeps_the_lab_line(
    upstream: Upstream, make_lab: MakeLab
) -> None:
    """The lab's line kept beside upstream's new one: nothing to report, and exit 0."""
    lab, lines, ours, theirs = _conflicted_tdd(upstream, make_lab)
    lab.write("skills/tdd/SKILL.md", skill("tdd", [*lines[:4], theirs, ours, *lines[5:]]))

    run = lab.recheck(upstream)

    assert run.returncode == 0, run.stdout + run.stderr
    assert "Dropped edits" not in run.stdout
    assert "Nothing to report." in run.stdout


def test_recheck_finds_a_renamed_skills_edits_where_they_were_ported(
    upstream: Upstream, make_lab: MakeLab
) -> None:
    """Upstream renamed the skill; once the lab line is in the new one, it is not dropped."""
    upstream.add("writing-great-skills", bucket="productivity")
    base = upstream.commit()
    lab = make_lab(upstream, base, tracked={"writing-great-skills": "productivity"})
    lab_line = "Name the units of every number."
    lab.write(
        "skills/writing-great-skills/SKILL.md",
        skill("writing-great-skills", [*numbered("writing-great-skills"), lab_line]),
    )
    lab.commit("lab edit")
    upstream.drop("writing-great-skills", bucket="productivity")
    upstream.add("writing-for-agents", bucket="productivity")
    upstream.commit("rename")
    merged = lab.merge(upstream)
    assert f"- `skills/writing-great-skills/SKILL.md`: {lab_line}\n" in merged.stdout
    lab.write(
        "skills/writing-for-agents/SKILL.md",
        skill("writing-for-agents", [*numbered("writing-for-agents"), lab_line]),
    )

    run = lab.recheck(upstream)

    assert run.returncode == 0, run.stdout + run.stderr
    assert "Dropped edits" not in run.stdout
