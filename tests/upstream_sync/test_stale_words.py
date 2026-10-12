"""Stale words: lab text that still uses a token upstream removed between the pin and the tip.

A clean merge cannot see these. Upstream renames `CONTEXT.md` to `GLOSSARY.md` everywhere it
owns, and a lab line saying `CONTEXT.md` merges without a conflict and is wrong from then on.
These tests read the report's `Stale words` section after a merge.
"""

from __future__ import annotations

from tests.upstream_sync.conftest import MakeLab, Upstream, numbered, skill


def test_a_lab_edit_still_using_a_word_upstream_removed_is_reported(
    upstream: Upstream, make_lab: MakeLab
) -> None:
    """The lab's added line is flagged where it lies; upstream's own text never is."""
    old = ["Write each term to `CONTEXT.md`.", *numbered("domain-modeling")]
    upstream.add("domain-modeling", text=skill("domain-modeling", old))
    base = upstream.commit()
    lab = make_lab(upstream, base, tracked={"domain-modeling": "engineering"})
    lab_line = "Science terms go in `CONTEXT.md` with their units."
    lab.write("skills/domain-modeling/SKILL.md", skill("domain-modeling", [*old, lab_line]))
    lab.commit("lab edit")
    new = ["Write each term to `GLOSSARY.md`, which was CONTEXT.md.", *old[1:]]
    upstream.write("skills/engineering/domain-modeling/SKILL.md", skill("domain-modeling", new))
    upstream.commit("rename the glossary")

    run = lab.merge(upstream)

    assert run.returncode == 0, run.stdout + run.stderr
    merged = lab.read("skills/domain-modeling/SKILL.md")
    assert merged == skill("domain-modeling", [*new, lab_line])
    line = merged.splitlines().index(lab_line) + 1
    assert "### Stale words" in run.stdout
    assert f"- `CONTEXT.md` in `skills/domain-modeling/SKILL.md:{line}`.\n" in run.stdout


def test_every_lab_page_is_read_wherever_it_lives_and_history_is_not(
    upstream: Upstream, make_lab: MakeLab
) -> None:
    """A lab page is read the day it lands, the defaults page included; the changelog never is."""
    upstream.add("domain-modeling", text=skill("domain-modeling", ["Keep a `CONTEXT.md`."]))
    base = upstream.commit()
    lab = make_lab(upstream, base, tracked={"domain-modeling": "engineering"})
    pages = {
        "defaults/lab-defaults.md": "# Lab defaults\n\nThe glossary is `CONTEXT.md`.\n",
        "skills/lab-hpc/SKILL.md": "# lab-hpc\n\nRecord cluster terms in CONTEXT.md.\n",
        "CHANGELOG.md": "# Changelog\n\n- The glossary was `CONTEXT.md`.\n",
        "docs/adr/0001-glossary.md": "# Glossary\n\nWe chose `CONTEXT.md`.\n",
    }
    for path, text in pages.items():
        lab.write(path, text)
    lab.commit("lab pages")
    lab.write("docs/agents/domain.md", "# Domain\n\nRead `CONTEXT.md` first.\n")  # not added yet
    upstream.write(
        "skills/engineering/domain-modeling/SKILL.md",
        skill("domain-modeling", ["Keep a `GLOSSARY.md`."]),
    )
    upstream.commit("rename the glossary")

    run = lab.merge(upstream)

    assert run.returncode == 0, run.stdout + run.stderr
    assert (
        "- `CONTEXT.md` in `defaults/lab-defaults.md:3`, `docs/agents/domain.md:3`, "
        "`skills/lab-hpc/SKILL.md:3`.\n"
    ) in run.stdout


def test_a_link_to_a_page_upstream_renamed_is_reported(
    upstream: Upstream, make_lab: MakeLab
) -> None:
    """The defaults page links upstream's seed pages by path, so a renamed page is a stale word."""
    setup = "setup-matt-pocock-skills"
    upstream.add(setup, text=skill(setup, ["See [the GitHub page](issue-tracker-github.md)."]))
    upstream.write(f"skills/engineering/{setup}/issue-tracker-github.md", "# GitHub issues\n")
    base = upstream.commit()
    lab = make_lab(upstream, base, tracked={setup: "engineering"})
    lab.write(
        "defaults/lab-defaults.md",
        f"# Lab defaults\n\n- [Issue tracker](../skills/{setup}/issue-tracker-github.md)\n",
    )
    lab.commit("defaults page")
    upstream.remove(f"skills/engineering/{setup}/issue-tracker-github.md")
    upstream.write(f"skills/engineering/{setup}/tracker-github.md", "# GitHub issues\n")
    upstream.write(
        f"skills/engineering/{setup}/SKILL.md",
        skill(setup, ["See [the GitHub page](tracker-github.md)."]),
    )
    upstream.commit("rename a seed page")

    run = lab.merge(upstream)

    assert run.returncode == 0, run.stdout + run.stderr
    assert not lab.exists(f"skills/{setup}/issue-tracker-github.md")
    assert "- `issue-tracker-github.md` in `defaults/lab-defaults.md:3`.\n" in run.stdout


def test_a_word_upstream_still_uses_elsewhere_is_not_stale(
    upstream: Upstream, make_lab: MakeLab
) -> None:
    """Upstream dropped `gh issue create` from one skill and kept it in another: nothing to say."""
    upstream.add("triage", text=skill("triage", ["Open one with `gh issue create`."]))
    upstream.add("to-tickets", text=skill("to-tickets", ["File each with `gh issue create`."]))
    base = upstream.commit()
    lab = make_lab(upstream, base, tracked={"triage": "engineering", "to-tickets": "engineering"})
    lab.write("skills/lab-hpc/SKILL.md", "# lab-hpc\n\nFile faults with `gh issue create`.\n")
    lab.commit("lab page")
    upstream.write("skills/engineering/triage/SKILL.md", skill("triage", ["Label it."]))
    upstream.commit("triage stops filing")

    run = lab.merge(upstream)

    assert run.returncode == 0, run.stdout + run.stderr
    assert "Stale words" not in run.stdout


def test_a_plain_word_upstream_stopped_quoting_is_not_stale(
    upstream: Upstream, make_lab: MakeLab
) -> None:
    """`true` or `plan` in lab prose is English, not a name upstream retired; `--dry-run` is one."""
    upstream.add("triage", text=skill("triage", ["Set `true`, write a `plan`, pass `--dry-run`."]))
    base = upstream.commit()
    lab = make_lab(upstream, base, tracked={"triage": "engineering"})
    lab.write("skills/lab-hpc/SKILL.md", "# lab-hpc\n\nIt is true: plan first, then --dry-run.\n")
    lab.commit("lab page")
    upstream.write("skills/engineering/triage/SKILL.md", skill("triage", ["Label it."]))
    upstream.commit()

    run = lab.merge(upstream)

    assert run.returncode == 0, run.stdout + run.stderr
    assert "### Stale words\n\n- `--dry-run` in `skills/lab-hpc/SKILL.md:3`.\n\n" in run.stdout
