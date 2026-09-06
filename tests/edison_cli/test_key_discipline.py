"""The key's route to the client, and the three places it must never appear.

This is the property `docs/adr/0007` exists for, and it is asserted the same way it always
was: against a stub that runs no client, records every argument, and reports only WHETHER the
key variable arrived non-empty — never its value.

The "it did arrive" assertion is load-bearing. Without it the three absence checks would pass
on a command that simply never sent the key, which is a different thing from sending it
safely.
"""

from __future__ import annotations

from pathlib import Path

from tests.edison_cli.conftest import FIXTURE_KEY, Harness

SRC = Path(__file__).resolve().parents[2] / "src"


def _submitted(edison: Harness) -> object:
    """Run one submission that the stub answers, with the fixture key in place."""
    query = edison.write("query.txt", "what is known about the thing\n")
    return edison.run(
        "task", "submit", "--job", "literature", "-q", query, "-f", str(edison.key_file)
    )


def test_the_key_reached_the_client_through_the_environment(edison: Harness) -> None:
    """Without this the absence checks below would prove nothing at all."""
    run = _submitted(edison)
    assert run.returncode == 0, run.stderr
    constructions = run.called("construct")
    assert len(constructions) == 1
    assert constructions[0]["key_arrived"] is True


def test_the_key_is_in_no_argument_the_client_process_ever_saw(edison: Harness) -> None:
    """The stub records `sys.argv`, so this reads the real command line rather than a copy."""
    run = _submitted(edison)
    for construction in run.called("construct"):
        assert FIXTURE_KEY not in " ".join(construction["argv"])
        assert FIXTURE_KEY not in " ".join(construction["args"])
        assert FIXTURE_KEY not in " ".join(f"{k}={v}" for k, v in construction["kwargs"].items())


def test_the_key_is_in_nothing_the_command_recorded_or_printed(edison: Harness) -> None:
    """Every call the client made, and both output streams."""
    run = _submitted(edison)
    assert FIXTURE_KEY not in run.log
    assert FIXTURE_KEY not in run.stdout
    assert FIXTURE_KEY not in run.stderr


def test_the_key_is_in_no_program_text(edison: Harness) -> None:
    """The bash version passed a program on stdin; the program is now the tree under `src/`.

    A key written into the package would be the same failure wearing a different shape.
    """
    _submitted(edison)
    offenders = [
        path
        for path in SRC.rglob("*.py")
        if FIXTURE_KEY in path.read_text(encoding="utf-8", errors="replace")
    ]
    assert offenders == []


def test_the_key_is_never_the_client_constructor_argument(edison: Harness) -> None:
    """`EdisonClient(api_key=...)` is the route this package refuses to use.

    The client reads the environment when no argument is given, so an empty argument list is
    the whole proof.
    """
    run = _submitted(edison)
    construction = run.called("construct")[0]
    assert construction["args"] == []
    assert "api_key" not in construction["kwargs"]
    assert "jwt" not in construction["kwargs"]


def test_a_configured_machine_still_prints_the_identifier_first(edison: Harness) -> None:
    """The receipt for the credit leads stdout, and no verdict line can push it down."""
    run = _submitted(edison)
    assert run.first_line.startswith("TASK_ID: ")


def test_the_audit_trail_is_on_stderr_so_stdout_stays_the_receipt(edison: Harness) -> None:
    """The job and the exact text that went out belong in the transcript beside the id."""
    run = _submitted(edison)
    assert "submitting LITERATURE" in run.stderr
    assert "| what is known about the thing" in run.stderr
    assert "submitting" not in run.stdout
