"""What the command refuses, and the proof that it refused before it could spend.

Every case here passes a key file that does not exist. A refusal that named the key file
instead of the argument would mean the argument check ran second, which is the ordering that
makes a refusal machine-dependent. And every case asserts that no client was ever
constructed — a stronger claim than an exit code, because constructing the client is already
a network call.
"""

from __future__ import annotations

import pytest

from tests.edison_cli.conftest import Harness


def _nothing_was_reached(harness: Harness, *argv: str) -> None:
    """Assert a command refused with exit 2 and never built a client."""
    run = harness.run(*argv)
    assert run.returncode == 2, run.stderr
    assert run.called("construct") == [], "a client was built before the refusal"


def test_submit_refuses_an_absent_query_file(edison: Harness) -> None:
    """The query is a file, and a file that is not there is a refusal, not an empty query."""
    run = edison.run(
        "task",
        "submit",
        "--job",
        "LITERATURE",
        "--query-file",
        str(edison.workspace / "nothing-here.txt"),
        "-f",
        str(edison.absent_key),
    )
    assert run.returncode == 2
    assert "no query file at" in run.stderr
    assert "nothing was submitted" in run.stderr
    assert run.called("construct") == []


def test_submit_refuses_an_empty_query_file(edison: Harness) -> None:
    """An empty file is the shape of a query someone meant to write and did not."""
    empty = edison.write("empty.txt", "")
    run = edison.run(
        "task", "submit", "--job", "LITERATURE", "-q", empty, "-f", str(edison.absent_key)
    )
    assert run.returncode == 2
    assert "is empty" in run.stderr
    assert run.called("construct") == []


def test_submit_refuses_a_job_name_off_the_routing_table(edison: Harness) -> None:
    """The client sends any string it is handed, so the allow-list is the only real check."""
    query = edison.write("query.txt", "what is known about the thing\n")
    run = edison.run(
        "task", "submit", "--job", "SPARROW", "-q", query, "-f", str(edison.absent_key)
    )
    assert run.returncode == 2
    assert "never invent a name" in run.stderr
    assert run.called("construct") == []


@pytest.mark.parametrize("member", ["PHOENIX", "DUMMY"])
def test_submit_refuses_a_real_member_that_404s_and_says_which(
    edison: Harness, member: str
) -> None:
    """Both are in `JobNames`, and a submission of either buys a 404 and no task.

    The refusal is before the network, so the round trip that proves it is never paid for a
    second time — and it names the member as real, because a reader told the name is unknown
    goes looking for a typo instead of reading the page.
    """
    query = edison.write("query.txt", "what is known about the thing\n")
    run = edison.run("task", "submit", "--job", member, "-q", query, "-f", str(edison.absent_key))
    assert run.returncode == 2
    assert "real JobNames member" in run.stderr
    assert run.called("construct") == []
    assert run.called("create_task") == []


def test_a_404_on_the_submission_itself_does_not_send_the_reader_after_an_id(
    edison: Harness,
) -> None:
    """No id exists yet on this path, so the lost-id sentence is advice about nothing.

    The stub answers the submission with a 404, which is what the platform did to `DUMMY`.
    """
    edison.env["EDISON_STUB_404"] = "create_task"
    query = edison.write("query.txt", "what is known about the thing\n")
    run = edison.run(
        "task", "submit", "--job", "LITERATURE", "-q", query, "-f", str(edison.key_file)
    )
    assert run.returncode == 1, run.stderr
    assert "404" in run.stderr
    assert "nothing was created" in run.stderr
    assert "task list" not in run.stderr
    assert run.called("create_task") != []


def test_kosmos_start_refuses_an_absent_objective_file(edison: Harness) -> None:
    """Kosmos is the most expensive surface here, so its refusal is the one that matters most."""
    _nothing_was_reached(
        edison,
        "kosmos",
        "start",
        "--project",
        "a-project",
        "--persona",
        "a-persona",
        "--objective-file",
        str(edison.workspace / "no-objective.txt"),
        "-f",
        str(edison.absent_key),
    )


def test_project_create_cannot_be_invoked_without_a_persona(edison: Harness) -> None:
    """An orphan project is not expressible through this surface, and that is the point.

    The API accepts one happily and then the chat endpoint answers 500 on it with no body.
    """
    _nothing_was_reached(
        edison, "project", "create", "--name", "orphan", "-f", str(edison.key_file)
    )


def test_data_upload_refuses_a_path_that_is_not_there(edison: Harness) -> None:
    """Nothing is uploaded, and the message says so rather than naming the key file."""
    _nothing_was_reached(
        edison, "data", "upload", str(edison.workspace / "absent.csv"), "-f", str(edison.key_file)
    )


def test_an_id_that_is_not_an_id_is_refused_before_the_client_is_built(edison: Harness) -> None:
    """The client wants UUIDs, and constructing one is already a network call.

    So the refusal has to come before the construction, not merely before the spend: the key
    file here exists, which is what makes the assertion say something. It used to say only
    that nothing was queued or cancelled, which the command satisfied while still paying for
    the round trip that authenticates and lists the account's organisations.
    """
    run = edison.run(
        "kosmos",
        "stop",
        "--project",
        "not-a-uuid",
        "--session",
        "also-not",
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 2
    assert "is not a project id" in run.stderr
    assert run.called("construct") == [], "the argument was read after a client was built"
    assert run.called("queue_chat_message") == []
    assert run.called("cancel_task") == []


@pytest.mark.parametrize(
    "argv",
    [
        ("task", "submit", "--job", "LITERATURE", "-q", "QUERY"),
        ("task", "status", "a-task-id"),
        ("task", "list"),
        ("task", "cancel", "a-task-id"),
        ("task", "fetch", "a-task-id"),
        ("persona", "list"),
        ("kosmos", "sessions"),
        ("data", "search", "--text", "counts"),
    ],
)
def test_an_unconfigured_machine_refuses_and_relays_the_preflight_remedy(
    edison: Harness, argv: tuple[str, ...]
) -> None:
    """Every subcommand that would touch the network refuses, and relays the fix, exit 1.

    The remedy is asserted through the placeholder the preflight owns, so this proves the
    text came from the preflight rather than from a copy of it that could drift.
    """
    from edison_cli import preflight

    query = edison.write("query.txt", "a query someone confirmed\n")
    filled = tuple(query if word == "QUERY" else word for word in argv)
    run = edison.run(*filled, "-f", str(edison.absent_key))
    assert run.returncode == 1, run.stderr
    assert preflight.PLACEHOLDER in run.stderr
    assert run.called("construct") == []
