"""Kosmos: the stop ordering that costs money to get wrong, and the receipts a run leaves.

The ordering test is the most valuable one in this suite. There is no run-level cancel on the
platform, and cancelling tasks one at a time on a live run makes the orchestrator dispatch
replacements about a minute later — so a `stop` that sweeps before it queues the halt loses a
race it is paying for.
"""

from __future__ import annotations

from tests.edison_cli.conftest import ACCOUNT, PERSONA_ID, PROJECT_ID, SESSION_ID, Harness

# A real entry, and a collection rather than a single file — ten files zipped behind one URI.
# That is the ordinary shape on this surface: a run is briefed with a folder of context, not one
# table. Both shapes are spelled `data_entry:<uuid>`, so the test uses the one people attach.
DATA_URI = "data_entry:24d88c92-48dc-4d97-a2f9-d5ef24cb60c2"
SECOND_URI = "data_entry:66666666-6666-4666-8666-666666666666"


def _stopped(edison: Harness) -> object:
    """Stop a run against the fake platform."""
    return edison.run(
        "kosmos",
        "stop",
        "--project",
        PROJECT_ID,
        "--session",
        SESSION_ID,
        "-f",
        str(edison.key_file),
    )


def test_stop_queues_the_halt_before_it_cancels_anything(edison: Harness) -> None:
    """Reversing these two is the failure mode that costs money."""
    run = _stopped(edison)
    assert run.returncode == 0, run.stderr
    queued = run.order_of("queue_chat_message")
    cancelled = run.order_of("cancel_task")
    assert queued != -1, "the halt was never queued"
    assert cancelled != -1, "nothing was swept"
    assert queued < cancelled, "the sweep ran before the halt was queued"


def test_stop_queues_the_halt_before_it_even_lists_the_tasks(edison: Harness) -> None:
    """The listing is the first step of the sweep, so the halt has to precede that too."""
    run = _stopped(edison)
    assert run.order_of("queue_chat_message") < run.order_of("get_tasks")


def test_stop_sweeps_only_the_tasks_that_can_still_spend(edison: Harness) -> None:
    """A finished task costs nothing to cancel, but a needless call is a needless failure."""
    run = _stopped(edison)
    cancelled = {call["task_id"] for call in run.called("cancel_task")}
    assert len(cancelled) == 2, f"expected the two live tasks, got {cancelled}"


def test_start_prints_the_ids_and_a_runnable_stop_command(edison: Harness) -> None:
    """A run that was paid for is always reachable, and the way to halt it is on the screen."""
    objective = edison.write("objective.txt", "survey the thing and compare the methods\n")
    run = edison.run(
        "kosmos",
        "start",
        "--project",
        PROJECT_ID,
        "--persona",
        PERSONA_ID,
        "--objective-file",
        objective,
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 0, run.stderr
    lines = run.stdout.splitlines()
    assert lines[0] == f"PROJECT_ID: {PROJECT_ID}"
    stop_line = next(line for line in lines if line.startswith("STOP: "))
    assert f"--project {PROJECT_ID}" in stop_line
    assert f"--session {SESSION_ID}" in stop_line
    assert "kosmos stop" in stop_line
    assert f"SESSION_ID: {SESSION_ID}" in run.stdout


def test_start_reads_the_job_name_off_the_persona_rather_than_guessing(edison: Harness) -> None:
    """`metadata.persona_job_name` is free and authoritative; a guessed job name is neither."""
    objective = edison.write("objective.txt", "an objective\n")
    run = edison.run(
        "kosmos",
        "start",
        "--project",
        PROJECT_ID,
        "--persona",
        PERSONA_ID,
        "--objective-file",
        objective,
        "-f",
        str(edison.key_file),
    )
    assert "JOB_NAME: job-futurehouse-data-analysis-aries" in run.stdout
    assert "PERSONA_OWNS_PROJECT: yes" in run.stdout
    assert run.order_of("http_get") < run.order_of("send_chat_message")


def test_start_attaches_every_repeated_data_uri(edison: Harness) -> None:
    """A run with no data was the whole bug: the client takes the field and nothing filled it."""
    objective = edison.write("objective.txt", "compare the two cohorts\n")
    run = edison.run(
        "kosmos",
        "start",
        "--project",
        PROJECT_ID,
        "--persona",
        PERSONA_ID,
        "--objective-file",
        objective,
        "-d",
        DATA_URI,
        "-d",
        SECOND_URI,
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 0, run.stderr
    sent = run.called("send_chat_message")[0]["kwargs"]
    # Byte for byte, prefix included: normalising it is the platform's job, not this command's.
    assert sent["data_storage_ids"] == [DATA_URI, SECOND_URI]


def test_start_prints_a_data_line_for_every_attachment_before_it_spends(edison: Harness) -> None:
    """An attachment that silently did not happen is the same bug again, so it leaves a receipt."""
    objective = edison.write("objective.txt", "compare the two cohorts\n")
    run = edison.run(
        "kosmos",
        "start",
        "--project",
        PROJECT_ID,
        "--persona",
        PERSONA_ID,
        "--objective-file",
        objective,
        "-d",
        DATA_URI,
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 0, run.stderr
    lines = run.stdout.splitlines()
    assert lines[0] == f"PROJECT_ID: {PROJECT_ID}"
    # The session id comes out of the response, so a DATA line above it was printed before the
    # send — while nothing had been charged and the attachment could still be corrected.
    assert lines.index(f"DATA: {DATA_URI}") < lines.index(f"SESSION_ID: {SESSION_ID}")


def test_start_without_data_sends_no_attachment_and_prints_no_data_line(edison: Harness) -> None:
    """The other half: an empty list must not become an empty attachment or a bare receipt."""
    objective = edison.write("objective.txt", "compare the two cohorts\n")
    run = edison.run(
        "kosmos",
        "start",
        "--project",
        PROJECT_ID,
        "--persona",
        PERSONA_ID,
        "--objective-file",
        objective,
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 0, run.stderr
    assert run.called("send_chat_message")[0]["kwargs"]["data_storage_ids"] is None
    assert "DATA:" not in run.stdout


def test_start_refuses_a_project_the_persona_does_not_own(edison: Harness) -> None:
    """The platform accepts an orphan project and then answers 500 with no body on it."""
    objective = edison.write("objective.txt", "an objective\n")
    run = edison.run(
        "kosmos",
        "start",
        "--project",
        "99999999-9999-4999-8999-999999999999",
        "--persona",
        PERSONA_ID,
        "--objective-file",
        objective,
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 1
    assert "does not own" in run.stderr
    assert run.called("send_chat_message") == []


def test_status_reads_what_the_run_said_out_of_the_tool_call_arguments(edison: Harness) -> None:
    """Assistant `content` is empty on this platform. Read it alone and a healthy run looks dead."""
    run = edison.run(
        "kosmos",
        "status",
        "--project",
        PROJECT_ID,
        "--session",
        SESSION_ID,
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 0, run.stderr
    assert "what the run said" in run.stdout
    assert "N_UTTERANCES: 1" in run.stdout


def test_sessions_prints_the_project_beside_the_session(edison: Harness) -> None:
    """Every other kosmos subcommand needs both ids, so a bare session id is a dead end."""
    run = edison.run("kosmos", "sessions", "-f", str(edison.key_file))
    assert run.returncode == 0, run.stderr
    line = next(line for line in run.stdout.splitlines() if line.startswith("SESSION: "))
    assert SESSION_ID in line
    assert PROJECT_ID in line, "the session id alone cannot be used by status, tasks or stop"


def test_no_kosmos_command_prints_an_account_identifier(edison: Harness) -> None:
    """The caller already knows whose account it is; a transcript does not need to."""
    run = edison.run(
        "kosmos",
        "tasks",
        "--project",
        PROJECT_ID,
        "--session",
        SESSION_ID,
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 0, run.stderr
    assert ACCOUNT not in run.stdout
