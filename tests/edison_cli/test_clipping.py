"""The printing caps, and the marker that keeps a cut honest.

Three commands cut a long piece of platform text so that one invocation cannot flood a
transcript: an utterance at 700 characters, a task query at 80, a data-entry description at
60. The caps are wanted. Cutting in silence is not — everything these commands print is what
an agent then answers from, and a sentence that stops mid-word with nothing to say so is read
as the whole answer. The description column is the sharpest case: `data search` matches on
descriptions, so a reader can be looking at a clipped one and not know their term was in the
part that went.

These tests pin the marker at all three call sites, and pin that it stays inside its column.

A fourth cut is measured in lines rather than characters and falls on text of the user's own:
the objective `kosmos start` echoes before it sends it. That one is not about flooding a
transcript but about what a flooded one costs — a harness that finds the output too big to
show renders a preview taken from the top, and the `STOP:` line is at the bottom.
"""

from __future__ import annotations

from edison_cli.runtime import clipped, clipped_lines
from tests.edison_cli.conftest import PROJECT_ID, SESSION_ID, Harness

MARK = "chars cut]"
LINE_MARK = "lines cut]"


def test_text_that_fits_is_printed_exactly_as_the_platform_said_it() -> None:
    """A marker on a line nothing was taken off would be a wrong answer of its own."""
    assert clipped("what the run said", 700) == "what the run said"
    assert clipped("x" * 80, 80) == "x" * 80


def test_text_over_the_cap_says_it_was_cut_and_by_how_much() -> None:
    """How much is missing is what tells the reader whether to go and get the rest."""
    assert clipped("x" * 900, 700) == "x" * 700 + "… [+200 chars cut]"


def test_the_marker_stays_inside_its_column() -> None:
    """Two of the three callers print tab-separated rows that are split by eye."""
    marked = clipped("a description that runs on\tand on\nand on", 10)
    assert "\t" not in marked[10:]
    assert "\n" not in marked[10:]


def test_a_block_that_fits_comes_back_line_for_line() -> None:
    """The fourth cap is measured in lines, and a marker it did not earn is the same wrong answer."""
    assert clipped_lines("one\ntwo\nthree", 3) == ["one", "two", "three"]
    assert clipped_lines("", 3) == []


def test_a_block_over_the_cap_ends_in_a_marker_counting_the_lines() -> None:
    """How many lines went is what tells the reader whether they are missing anything."""
    block = "".join(f"line {n}\n" for n in range(10))
    cut = clipped_lines(block, 4)
    assert cut[:4] == ["line 0", "line 1", "line 2", "line 3"]
    assert cut[-1] == "… [+6 lines cut]"
    assert LINE_MARK in cut[-1]


def test_kosmos_status_marks_the_utterance_it_cut(edison: Harness) -> None:
    """The 700-character cut, on the line a reader takes the run's answer from."""
    edison.env["EDISON_STUB_LONG"] = "1"
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
    said = next(line for line in run.stdout.splitlines() if line.startswith("[SAY] "))
    assert MARK in said, f"the utterance was cut with nothing on the line to say so: {said}"


def test_kosmos_tasks_marks_the_query_it_cut(edison: Harness) -> None:
    """The 80-character cut, in a tab-separated row the marker must not break."""
    edison.env["EDISON_STUB_LONG"] = "1"
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
    rows = [line for line in run.stdout.splitlines() if line.startswith("TASK: ")]
    marked = [row for row in rows if MARK in row]
    assert marked, "a clipped query admitted nothing"
    assert len(marked[0].split("\t")) == len(rows[0].split("\t")), "the marker added a column"


def test_data_search_marks_the_description_it_cut(edison: Harness) -> None:
    """`data search` matches on descriptions, so a clipped one has to admit it is clipped."""
    edison.env["EDISON_STUB_LONG"] = "1"
    run = edison.run("data", "search", "--text", "counts", "-f", str(edison.key_file))
    assert run.returncode == 0, run.stderr
    entry = next(line for line in run.stdout.splitlines() if line.startswith("ENTRY: "))
    assert MARK in entry, f"the description was cut with nothing to say so: {entry}"
    assert len(entry.split("\t")) == 4, "the marker added a column"
