"""Kosmos: the stop ordering that costs money to get wrong, and the receipts a run leaves.

The ordering test is the most valuable one in this suite. There is no run-level cancel on the
platform, and cancelling tasks one at a time on a live run makes the orchestrator dispatch
replacements about a minute later — so a `stop` that sweeps before it queues the halt loses a
race it is paying for.
"""

from __future__ import annotations

import json

import pytest

from edison_cli.datasets import PREFIX
from edison_cli.kosmos import ECHO_LINES
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


def _started_with(edison: Harness, objective: str) -> object:
    """Start a run whose objective is exactly this text."""
    return edison.run(
        "kosmos",
        "start",
        "--project",
        PROJECT_ID,
        "--persona",
        PERSONA_ID,
        "--objective-file",
        edison.write("objective.txt", objective),
        "-f",
        str(edison.key_file),
    )


def test_start_caps_the_objective_echo_and_says_how_many_lines_it_cut(edison: Harness) -> None:
    """A long objective used to bury the receipt, and a harness then truncated it away.

    The first live run echoed 675 lines between `DATA:` and `SESSION_ID`. That put the whole
    output past the harness's inline limit, so the caller was shown a preview taken from the
    top and never saw `STOP:` — the only halt path a run that is actively spending has.
    """
    run = _started_with(edison, "".join(f"line {n} of the objective\n" for n in range(400)))
    assert run.returncode == 0, run.stderr
    echoed = [line for line in run.stderr.splitlines() if line.startswith("  | ")]
    assert len(echoed) == ECHO_LINES + 1, f"the echo was not capped: {len(echoed)} lines"
    assert echoed[-1] == f"  | … [+{400 - ECHO_LINES} lines cut]"
    # The point of the cap: everything after the echo is still there to be read.
    assert "STOP: " in run.stdout
    assert f"SESSION_ID: {SESSION_ID}" in run.stdout


def test_start_echoes_a_short_objective_whole_and_marks_nothing(edison: Harness) -> None:
    """A marker on an echo nothing was taken off would be a wrong answer of its own."""
    run = _started_with(edison, "compare the two cohorts\nand say which is which\n")
    assert run.returncode == 0, run.stderr
    echoed = [line for line in run.stderr.splitlines() if line.startswith("  | ")]
    assert echoed == ["  | compare the two cohorts", "  | and say which is which"]


def test_start_sends_the_whole_objective_however_much_of_it_was_echoed(edison: Harness) -> None:
    """The cap is on the narration alone. Sending a clipped objective would be a real bug."""
    objective = "".join(f"line {n} of the objective\n" for n in range(400))
    run = _started_with(edison, objective)
    assert run.called("send_chat_message")[0]["chars"] == len(objective)


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


def _status(edison: Harness) -> object:
    """Poll the run against the fake platform."""
    return edison.run(
        "kosmos",
        "status",
        "--project",
        PROJECT_ID,
        "--session",
        SESSION_ID,
        "-f",
        str(edison.key_file),
    )


def test_status_reads_what_the_run_said_out_of_the_tool_call_arguments(edison: Harness) -> None:
    """Assistant `content` is empty on this platform. Read it alone and a healthy run looks dead."""
    run = _status(edison)
    assert run.returncode == 0, run.stderr
    assert "what the run said" in run.stdout
    assert "N_UTTERANCES: 1" in run.stdout


def test_status_prints_what_the_platform_stored_as_the_attachment(edison: Harness) -> None:
    """`start` says what we sent. Only `info` says what the platform kept, and it is free."""
    stems = [DATA_URI.removeprefix(PREFIX), SECOND_URI.removeprefix(PREFIX)]
    edison.env["EDISON_STUB_INFO"] = json.dumps({"data_storage_ids": stems})
    run = _status(edison)
    assert run.returncode == 0, run.stderr
    lines = run.stdout.splitlines()
    assert [line for line in lines if line.startswith("ATTACHED: ")] == [
        f"ATTACHED: {DATA_URI}",
        f"ATTACHED: {SECOND_URI}",
    ]
    # Beside the fan-out and the utterance count, which is where a run's facts are read.
    assert lines.index(f"ATTACHED: {DATA_URI}") > lines.index("N_TASKS: 3")
    assert lines.index(f"ATTACHED: {SECOND_URI}") < lines.index("N_UTTERANCES: 1")


def test_status_spells_an_attachment_exactly_as_start_spelled_it(edison: Harness) -> None:
    """The spelling has to match, or the two receipts cannot be compared.

    We send `data_entry:<uuid>` and the platform keeps the stem. Comparing the two is the only
    reason to print both, so the difference is normalised away before either is printed.
    """
    objective = edison.write("objective.txt", "compare the two cohorts\n")
    started = edison.run(
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
    sent = next(line for line in started.stdout.splitlines() if line.startswith("DATA: "))
    edison.env["EDISON_STUB_INFO"] = json.dumps(
        {"data_storage_ids": [DATA_URI.removeprefix(PREFIX)]}
    )
    kept = next(line for line in _status(edison).stdout.splitlines() if line.startswith("ATTACHED"))
    assert sent.removeprefix("DATA: ") == kept.removeprefix("ATTACHED: ")


def test_status_of_a_run_with_no_data_prints_no_attached_line(edison: Harness) -> None:
    """A placeholder line would read exactly like an attachment the platform threw away."""
    run = _status(edison)
    assert run.returncode == 0, run.stderr
    assert "ATTACHED" not in run.stdout
    assert "N_UTTERANCES: 1" in run.stdout


@pytest.mark.parametrize(
    "info",
    [
        "null",
        '"a string where a dict was promised"',
        '{"data_storage_ids": null}',
        '{"data_storage_ids": "one-id-not-in-a-list"}',
        '{"something_else": ["an id"]}',
    ],
    ids=["none", "not-a-dict", "null-ids", "ids-not-a-list", "no-ids-key"],
)
def test_status_survives_an_info_shaped_however_the_platform_shaped_it(
    edison: Harness, info: str
) -> None:
    """One odd turn must not cost the reader the rest of `status`.

    `info` is `dict | None` and its contents are the platform's, so the fan-out, the
    utterances and the exit code all have to survive whatever arrives in it.
    """
    edison.env["EDISON_STUB_INFO"] = info
    run = _status(edison)
    assert run.returncode == 0, run.stderr
    assert "ATTACHED" not in run.stdout
    assert "N_TASKS: 3" in run.stdout
    assert "what the run said" in run.stdout


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
