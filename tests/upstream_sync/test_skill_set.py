"""Skills arriving and leaving: deletions, renames, new skills, and the forked ones left alone.

A tracked skill gone from the tip loses its lab copy, its pin entry and its gate exemption,
because the set should not keep dead skills; a forked one stays, because the lab owns it. A
rename is that deletion plus a new skill. A new skill is one upstream's plugin manifest lists
at the tip and did not list at the pin, so a skill the lab skipped never comes back by itself.
"""

from __future__ import annotations

from tests.upstream_sync.conftest import ATTRIBUTION, PIN, MakeLab, Upstream, numbered, skill


def test_an_upstream_deletion_removes_an_unforked_skill(
    upstream: Upstream, make_lab: MakeLab
) -> None:
    """The lab copy, the pin entry and both gate exemptions go, and the report names the edits."""
    upstream.add("grilling", bucket="productivity")
    upstream.add("resolving-merge-conflicts")
    base = upstream.commit()
    lab = make_lab(
        upstream,
        base,
        tracked={"grilling": "productivity", "resolving-merge-conflicts": "engineering"},
    )
    lab.write("skills/resolving-merge-conflicts/NOTEBOOKS.md", "# nbdime for notebooks\n")
    lab.commit("lab edit")
    upstream.drop("resolving-merge-conflicts")
    upstream.commit()

    run = lab.merge(upstream)

    assert run.returncode == 0, run.stdout + run.stderr
    assert not lab.exists("skills/resolving-merge-conflicts")
    assert lab.json(PIN)["items"] == {"grilling": "skills/grilling"}
    vale, mdl = lab.gate_names()
    assert "[skills/{grilling}/*.md]" in vale
    assert '"skills/grilling/**"' in mdl
    assert "resolving-merge-conflicts" not in vale + mdl
    assert "### Deleted upstream" in run.stdout
    assert "Removed `skills/resolving-merge-conflicts`" in run.stdout
    assert "lab edits in `NOTEBOOKS.md`" in run.stdout


def test_an_upstream_deletion_keeps_a_forked_skill(upstream: Upstream, make_lab: MakeLab) -> None:
    """The lab owns a forked skill, so its original going away upstream is news, not a removal."""
    upstream.add("grilling", bucket="productivity")
    upstream.add("teach", bucket="productivity")
    base = upstream.commit()
    lab = make_lab(
        upstream, base, tracked={"grilling": "productivity"}, forked={"teach": "productivity"}
    )
    upstream.drop("teach", bucket="productivity")
    upstream.commit()

    run = lab.merge(upstream)

    assert run.returncode == 0, run.stdout + run.stderr
    assert lab.read("skills/teach/SKILL.md") == skill("teach")
    assert "skills/teach" in lab.json(ATTRIBUTION)
    assert "[skills/{grilling,teach}/*.md]" in lab.gate_names()[0]
    assert "`teach`, the original of forked `skills/teach`, is gone upstream" in run.stdout


def test_a_renamed_skill_is_a_deletion_plus_a_new_skill(
    upstream: Upstream, make_lab: MakeLab
) -> None:
    """The old name goes with its lab copy, the new name arrives as upstream wrote it."""
    upstream.add("writing-great-skills", bucket="productivity")
    base = upstream.commit()
    lab = make_lab(upstream, base, tracked={"writing-great-skills": "productivity"})
    lines = numbered("writing-great-skills")
    lab.write(
        "skills/writing-great-skills/SKILL.md", skill("writing-great-skills", [*lines, "Lab."])
    )
    lab.commit("lab edit")
    upstream.drop("writing-great-skills", bucket="productivity")
    upstream.add("writing-for-agents", bucket="productivity")
    upstream.commit()

    run = lab.merge(upstream)

    assert run.returncode == 0, run.stdout + run.stderr
    assert not lab.exists("skills/writing-great-skills")
    assert lab.read("skills/writing-for-agents/SKILL.md") == skill("writing-for-agents")
    assert lab.json(PIN)["items"] == {"writing-for-agents": "skills/writing-for-agents"}
    vale, mdl = lab.gate_names()
    assert "[skills/{writing-for-agents}/*.md]" in vale
    assert '"skills/writing-for-agents/**"' in mdl
    assert "writing-great-skills" not in vale + mdl
    assert "Removed `skills/writing-great-skills`" in run.stdout
    assert "lab edits in `SKILL.md`" in run.stdout
    assert "`writing-for-agents`: added at `skills/writing-for-agents`" in run.stdout


def test_a_new_skill_in_the_manifest_arrives_by_default(
    upstream: Upstream, make_lab: MakeLab
) -> None:
    """Listed at the tip and not at the pin: copied, mapped and exempted. Unlisted ones stay out."""
    upstream.add("grilling", bucket="productivity")
    upstream.add("wizard")  # listed at the pin, and the lab skipped it
    base = upstream.commit()
    lab = make_lab(upstream, base, tracked={"grilling": "productivity"})
    upstream.add("handoff", bucket="productivity")
    upstream.write("skills/productivity/handoff/template.md", "# Template\n")
    upstream.write("skills/in-progress/draft/SKILL.md", skill("draft"))  # under skills/, unlisted
    upstream.commit()

    run = lab.merge(upstream)

    assert run.returncode == 0, run.stdout + run.stderr
    assert lab.read("skills/handoff/SKILL.md") == skill("handoff")
    assert lab.read("skills/handoff/template.md") == "# Template\n"
    assert lab.json(PIN)["items"] == {
        "grilling": "skills/grilling",
        "handoff": "skills/handoff",
    }
    vale, mdl = lab.gate_names()
    assert "[skills/{grilling,handoff}/*.md]" in vale
    assert '      - "skills/grilling/**"\n      - "skills/handoff/**"\n' in mdl
    assert not lab.exists("skills/wizard")
    assert not lab.exists("skills/draft")
    assert "### New skills" in run.stdout
    assert "wizard" not in run.stdout


def test_a_forked_skill_is_never_merged(upstream: Upstream, make_lab: MakeLab) -> None:
    """Upstream changed the original of a forked skill; the lab copy is left byte for byte."""
    upstream.add("grilling", bucket="productivity")
    upstream.add("teach", bucket="productivity")
    base = upstream.commit()
    lab = make_lab(
        upstream, base, tracked={"grilling": "productivity"}, forked={"teach": "productivity"}
    )
    lab_text = skill("teach", ["The lab's own way to teach."])
    lab.write("skills/teach/SKILL.md", lab_text)
    lab.commit("lab owns it")
    upstream.write(
        "skills/productivity/teach/SKILL.md", skill("teach", ["Upstream's new way to teach."])
    )
    upstream.write("skills/productivity/teach/extra.md", "# Extra\n")
    upstream.commit()

    run = lab.merge(upstream)

    assert run.returncode == 0, run.stdout + run.stderr
    assert lab.read("skills/teach/SKILL.md") == lab_text
    assert not lab.exists("skills/teach/extra.md")
    assert "teach" not in lab.json(PIN)["items"]
    assert "### Forked, not merged" in run.stdout
    assert "`skills/teach`, from `teach`" in run.stdout
    assert "### New skills" not in run.stdout


def test_a_forked_skill_left_in_the_name_map_is_still_not_merged(
    upstream: Upstream, make_lab: MakeLab
) -> None:
    """A record written by hand with the pin entry forgotten: the record wins, and it is said."""
    upstream.add("teach", bucket="productivity")
    base = upstream.commit()
    lab = make_lab(upstream, base, tracked={"teach": "productivity"})
    lab.write(
        ATTRIBUTION,
        f'{{"skills/teach": {{"from": [{{"upstream": "mattpocock", "item": "teach", "commit": "{base}"}}]}}}}\n',
    )
    lab.commit("forked by hand")
    upstream.write("skills/productivity/teach/SKILL.md", skill("teach", ["Upstream's new way."]))
    upstream.commit()

    run = lab.merge(upstream)

    assert run.returncode == 0, run.stdout + run.stderr
    assert lab.read("skills/teach/SKILL.md") == skill("teach")
    assert "`skills/teach` is tracked and forked at once, so it was not merged" in run.stdout
