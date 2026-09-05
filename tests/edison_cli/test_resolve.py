"""Names instead of ids, and the two edges where the resolver refuses rather than chooses.

A UUID is what the platform wants and nothing a person can hold in their head, so a name is
accepted anywhere an id is. The danger is entirely in the ambiguous cases: nothing found, and
more than one found. Both refuse here, and the duplicate refusal prints every candidate so
the next command can be unambiguous.

The cache exists so that typing a name twice does not list twice. It is never consulted by
anything that spends or destroys, and the last test is why.
"""

from __future__ import annotations

import json

from tests.edison_cli.conftest import OTHER_ID, PERSONA_ID, PROJECT_ID, SESSION_ID, Harness


def test_a_persona_name_resolves_to_its_id(edison: Harness) -> None:
    """`--persona Kosmos` is what a person can type; the UUID is what the platform takes."""
    run = edison.run("project", "list", "--persona", "Kosmos", "-f", str(edison.key_file))
    assert run.returncode == 0, run.stderr
    assert run.called("list_persona_owned_projects")[0]["persona_id"] == PERSONA_ID


def test_a_project_name_resolves_inside_its_persona(edison: Harness) -> None:
    """A project name is unique only within a persona, which is why one has to be named."""
    run = edison.run(
        "kosmos",
        "tasks",
        "--project",
        "a project",
        "--persona",
        PERSONA_ID,
        "--session",
        SESSION_ID,
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 0, run.stderr
    assert run.first_line == f"PROJECT_ID: {PROJECT_ID}"


def test_an_id_still_works_everywhere_a_name_does(edison: Harness) -> None:
    """Accepting a name must not cost anyone the id they already had."""
    run = edison.run("project", "list", "--persona", PERSONA_ID, "-f", str(edison.key_file))
    assert run.returncode == 0, run.stderr
    assert run.called("http_get") == [], "an id should need no listing at all"


def test_a_name_nothing_matches_is_refused(edison: Harness) -> None:
    """Refused, and told what was looked for and where to see what there is."""
    run = edison.run("project", "list", "--persona", "Nobody", "-f", str(edison.key_file))
    assert run.returncode == 1
    assert "no persona called 'Nobody'" in run.stderr
    assert run.called("list_persona_owned_projects") == []


def test_a_duplicate_persona_name_refuses_and_prints_every_candidate(edison: Harness) -> None:
    """It never picks one. Both ids go on the screen so the next command can be exact."""
    edison.env["EDISON_STUB_DUPLICATES"] = "personas"
    run = edison.run("project", "list", "--persona", "Kosmos", "-f", str(edison.key_file))
    assert run.returncode == 1
    assert "2 personas are called 'Kosmos'" in run.stderr
    assert PERSONA_ID in run.stderr
    assert OTHER_ID in run.stderr
    assert run.called("list_persona_owned_projects") == []


def test_a_duplicate_project_name_refuses_and_prints_every_candidate(edison: Harness) -> None:
    """The same edge one level down, where the client's own getter would have picked."""
    edison.env["EDISON_STUB_DUPLICATES"] = "projects"
    run = edison.run(
        "kosmos",
        "tasks",
        "--project",
        "a project",
        "--persona",
        PERSONA_ID,
        "--session",
        SESSION_ID,
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 1
    assert "2 projects are called 'a project'" in run.stderr
    assert PROJECT_ID in run.stderr
    assert OTHER_ID in run.stderr


def test_a_project_name_without_a_persona_is_refused_as_a_usage_error(edison: Harness) -> None:
    """There is nothing to resolve it against, and guessing is the thing this refuses to do."""
    run = edison.run(
        "kosmos",
        "tasks",
        "--project",
        "a project",
        "--session",
        SESSION_ID,
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 2
    assert "unique only inside a persona" in run.stderr


def test_a_name_looked_up_once_is_remembered(edison: Harness) -> None:
    """The cache is a convenience: typing a name twice should not list twice."""
    first = edison.run(
        "kosmos",
        "tasks",
        "--project",
        "a project",
        "--persona",
        PERSONA_ID,
        "--session",
        SESSION_ID,
        "-f",
        str(edison.key_file),
    )
    assert first.returncode == 0, first.stderr
    assert first.called("list_persona_owned_projects") != []

    second = edison.run(
        "kosmos",
        "tasks",
        "--project",
        "a project",
        "--persona",
        PERSONA_ID,
        "--session",
        SESSION_ID,
        "-f",
        str(edison.key_file),
    )
    assert second.returncode == 0, second.stderr
    assert second.called("list_persona_owned_projects") == []
    assert second.first_line == f"PROJECT_ID: {PROJECT_ID}"


def test_the_cache_holds_names_and_ids_and_nothing_else(edison: Harness) -> None:
    """Not the key, not one byte of the key file — it is a directory of names."""
    from tests.edison_cli.conftest import FIXTURE_KEY

    edison.run("project", "list", "--persona", "Kosmos", "-f", str(edison.key_file))
    body = edison.cache.read_text(encoding="utf-8")
    assert FIXTURE_KEY not in body
    known = json.loads(body)
    assert known["personas"][""]["Kosmos"] == PERSONA_ID
    assert known["projects"][PERSONA_ID]["a project"] == PROJECT_ID


def test_no_cache_looks_the_name_up_again(edison: Harness) -> None:
    """The way to bypass a stale entry, and the way to refresh what is remembered."""
    edison.run(
        "kosmos",
        "tasks",
        "--project",
        "a project",
        "--persona",
        PERSONA_ID,
        "--session",
        SESSION_ID,
        "-f",
        str(edison.key_file),
    )
    again = edison.run(
        "kosmos",
        "tasks",
        "--project",
        "a project",
        "--persona",
        PERSONA_ID,
        "--session",
        SESSION_ID,
        "--no-cache",
        "-f",
        str(edison.key_file),
    )
    assert again.returncode == 0, again.stderr
    assert again.called("list_persona_owned_projects") != []


def test_a_destructive_command_ignores_a_poisoned_cache(edison: Harness) -> None:
    """A stale name pointing at an id that was deleted and recreated deletes the wrong project.

    So `project delete` resolves live, whatever the cache says, and the summary it prints
    names what the resolution actually found.
    """
    poison = {"projects": {PERSONA_ID: {"a project": OTHER_ID}}}
    edison.cache.write_text(json.dumps(poison), encoding="utf-8")

    run = edison.run(
        "project",
        "delete",
        "--project",
        "a project",
        "--persona",
        PERSONA_ID,
        "--keep-tasks",
        "--yes",
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 0, run.stderr
    assert run.called("list_persona_owned_projects") != [], "the cache was trusted"
    assert run.called("delete_project")[0]["project_id"] == PROJECT_ID
    assert OTHER_ID not in run.stdout


def test_delete_names_an_empty_project_from_its_persona(edison: Harness) -> None:
    """The defect this replaced: the name came from the tasks, and an empty project has none."""
    run = edison.run(
        "project",
        "delete",
        "--project",
        PROJECT_ID,
        "--persona",
        PERSONA_ID,
        "--keep-tasks",
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 2
    assert "PROJECT_NAME: a project" in run.stdout
    assert "DELETED: no" in run.stdout
