"""The one irreversible command, and the three guards that stand in front of it.

`project delete` is the only call here that destroys something, and the client's own default
takes a project's paid run history with it. Every guard below is asserted by what the fake
platform was and was not asked to do, not by an exit code alone.
"""

from __future__ import annotations

from tests.edison_cli.conftest import PERSONA_ID, PROJECT_ID, Harness


def test_without_yes_it_deletes_nothing_and_still_leaves_the_summary(edison: Harness) -> None:
    """The receipt exists whether or not the delete proceeds, so a refusal is still informative."""
    run = edison.run(
        "project", "delete", "--project", PROJECT_ID, "--delete-tasks", "-f", str(edison.key_file)
    )
    assert run.returncode == 2, run.stderr
    assert run.called("delete_project") == []
    assert run.first_line == f"PROJECT_ID: {PROJECT_ID}"
    assert "PROJECT_NAME: a project" in run.stdout
    assert "N_TASKS: 3" in run.stdout
    assert "DELETED: no" in run.stdout


def test_without_a_trajectory_flag_it_refuses_before_it_reads_anything(edison: Harness) -> None:
    """The client's default is destructive, so inheriting it silently is not an option."""
    run = edison.run(
        "project", "delete", "--project", PROJECT_ID, "--yes", "-f", str(edison.key_file)
    )
    assert run.returncode == 2, run.stderr
    assert "--delete-tasks or --keep-tasks" in run.stderr
    assert run.called("construct") == []
    assert run.called("delete_project") == []


def test_the_confirmed_delete_passes_the_disposition_through(edison: Harness) -> None:
    """Whichever the caller chose is what the client is told, with no default in between."""
    kept = edison.run(
        "project",
        "delete",
        "--project",
        PROJECT_ID,
        "--keep-tasks",
        "--yes",
        "-f",
        str(edison.key_file),
    )
    assert kept.returncode == 0, kept.stderr
    assert kept.called("delete_project")[0]["delete_trajectories"] is False
    assert "DELETED: yes" in kept.stdout


def test_the_confirmed_delete_can_take_the_history_too(edison: Harness) -> None:
    """The other half, so a green test cannot come from one branch that never fires."""
    run = edison.run(
        "project",
        "delete",
        "--project",
        PROJECT_ID,
        "--delete-tasks",
        "--yes",
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 0, run.stderr
    assert run.called("delete_project")[0]["delete_trajectories"] is True


def test_a_successful_delete_forgets_the_name_the_cache_still_pointed_at(edison: Harness) -> None:
    """Resolving live protects `delete` and nothing after it.

    The cached name outlived the project, so the seven commands that DO read the cache could
    still resolve it — the stale-name hazard arriving one command later. The listing is done
    first so the entry genuinely exists, and the delete goes by id, which reaches the platform
    without listing anything and so cannot refresh the cache as a side effect.
    """
    listed = edison.run("project", "list", "--persona", PERSONA_ID, "-f", str(edison.key_file))
    assert listed.returncode == 0, listed.stderr
    assert PROJECT_ID in edison.cache.read_text(encoding="utf-8")

    gone = edison.run(
        "project",
        "delete",
        "--project",
        PROJECT_ID,
        "--keep-tasks",
        "--yes",
        "-f",
        str(edison.key_file),
    )
    assert gone.returncode == 0, gone.stderr
    assert "DELETED: yes" in gone.stdout
    assert PROJECT_ID not in edison.cache.read_text(encoding="utf-8")
    # The persona's scope survives: only the entry pointing at what was destroyed goes.
    assert PERSONA_ID in edison.cache.read_text(encoding="utf-8")


def test_a_refused_delete_forgets_nothing(edison: Harness) -> None:
    """Nothing was destroyed, so the remembered name is still true and still useful."""
    edison.run("project", "list", "--persona", PERSONA_ID, "-f", str(edison.key_file))
    run = edison.run(
        "project", "delete", "--project", PROJECT_ID, "--keep-tasks", "-f", str(edison.key_file)
    )
    assert run.returncode == 2
    assert PROJECT_ID in edison.cache.read_text(encoding="utf-8")


def test_a_project_name_with_no_persona_deletes_nothing(edison: Harness) -> None:
    """A name is addressable — given a persona. Without one there is nothing to resolve it in.

    `get_project_by_name` answers with a UUID or a list of them, and a delete cannot guess,
    so the refusal is the whole behaviour: exit 2, and the client never asked to delete.
    """
    run = edison.run(
        "project",
        "delete",
        "--project",
        "a project",
        "--keep-tasks",
        "--yes",
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 2
    assert "is not a project id" in run.stderr
    assert run.called("delete_project") == []
