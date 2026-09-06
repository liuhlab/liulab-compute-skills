"""The rest of the surface: identifiers first, flags that carry, and nothing personal printed."""

from __future__ import annotations

from pathlib import Path

from tests.edison_cli.conftest import ACCOUNT, PERSONA_ID, PROJECT_ID, TASK_ID, Harness


def test_project_create_prints_the_id_first_and_confirms_ownership(edison: Harness) -> None:
    """A project no persona owns is invisible in the browser, so the answer is not optional."""
    run = edison.run(
        "project", "create", "--name", "a run", "--persona", PERSONA_ID, "-f", str(edison.key_file)
    )
    assert run.returncode == 0, run.stderr
    assert run.first_line == f"PROJECT_ID: {PROJECT_ID}"
    assert "PERSONA_OWNS_PROJECT: yes" in run.stdout
    assert run.called("create_project")[0]["persona_id"] == PERSONA_ID


def test_project_ensure_reuses_rather_than_creating_a_second_one(edison: Harness) -> None:
    """Two projects of one name under one persona cannot be told apart afterwards."""
    run = edison.run(
        "project",
        "ensure",
        "--name",
        "a project",
        "--persona",
        PERSONA_ID,
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 0, run.stderr
    assert run.first_line == f"PROJECT_ID: {PROJECT_ID}"
    assert "REUSED: yes" in run.stdout
    assert run.called("create_project") == []


def test_project_ensure_creates_when_the_name_is_new(edison: Harness) -> None:
    """The other half of reuse-or-create, so a green test cannot come from never creating."""
    run = edison.run(
        "project",
        "ensure",
        "--name",
        "a name nothing has",
        "--persona",
        PERSONA_ID,
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 0, run.stderr
    assert "REUSED: no" in run.stdout
    assert len(run.called("create_project")) == 1


def test_submit_attaches_every_repeated_data_uri(edison: Harness) -> None:
    """`--data` is repeatable, and the ANALYSIS path in references/datasets.md is built on it."""
    query = edison.write("query.txt", "analyse the counts\n")
    run = edison.run(
        "task",
        "submit",
        "-j",
        "ANALYSIS",
        "-q",
        query,
        "-d",
        "data_entry:one",
        "-d",
        "data_entry:two",
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 0, run.stderr
    assert run.called("create_task")[0]["files"] == ["data_entry:one", "data_entry:two"]


def test_submit_carries_continue_into_the_runtime_config(edison: Harness) -> None:
    """`--continue` is the cheap alternative to paying for a run's context twice."""
    query = edison.write("query.txt", "and what about the other thing\n")
    run = edison.run(
        "task",
        "submit",
        "-j",
        "LITERATURE",
        "-q",
        query,
        "-c",
        TASK_ID,
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 0, run.stderr
    assert "continued_job_id" in run.called("create_task")[0]["task"]


def test_submit_refuses_a_continue_id_the_client_could_not_use(edison: Harness) -> None:
    """`RuntimeConfig.continued_job_id` is a UUID, so a bad one fails better here than there."""
    query = edison.write("query.txt", "and what about the other thing\n")
    run = edison.run(
        "task",
        "submit",
        "-j",
        "LITERATURE",
        "-q",
        query,
        "-c",
        "an-earlier-task",
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 2
    assert "is not a task id" in run.stderr
    assert run.called("create_task") == []
    assert run.called("construct") == [], "the id was read after a client was built"


def test_fetch_with_out_writes_the_answer_it_used_only_to_print(edison: Harness) -> None:
    """`--out` used to promise more than it kept, which is the defect #39 found."""
    out = edison.workspace / "collected"
    run = edison.run("task", "fetch", TASK_ID, "-o", str(out), "-f", str(edison.key_file))
    assert run.returncode == 0, run.stderr
    assert (out / f"{TASK_ID}.answer.md").is_file()
    assert (out / f"{TASK_ID}.ipynb").is_file()
    assert f"ANSWER_FILE: {out / f'{TASK_ID}.answer.md'}" in run.stdout


def test_fetch_prints_no_account_identifier_in_its_file_records(edison: Harness) -> None:
    """The provenance record is printed whole because its shape is unknown — minus the account."""
    run = edison.run("task", "fetch", TASK_ID, "-f", str(edison.key_file))
    assert run.returncode == 0, run.stderr
    assert "FILE: " in run.stdout
    assert ACCOUNT not in run.stdout


def test_persona_show_prints_the_job_name_and_no_account(edison: Harness) -> None:
    """The job name is free here and authoritative; the account identifier is neither."""
    run = edison.run("persona", "show", "--id", PERSONA_ID, "-f", str(edison.key_file))
    assert run.returncode == 0, run.stderr
    assert run.first_line == f"PERSONA_ID: {PERSONA_ID}"
    assert "PERSONA_JOB_NAME: job-futurehouse-data-analysis-aries" in run.stdout
    assert ACCOUNT not in run.stdout


def test_persona_show_refuses_both_selectors_at_once(edison: Harness) -> None:
    """Two selectors is a question with two answers, and guessing between them is worse."""
    run = edison.run(
        "persona", "show", "--id", PERSONA_ID, "--name", "Kosmos", "-f", str(edison.key_file)
    )
    assert run.returncode == 2
    assert "exactly one" in run.stderr
    assert run.called("construct") == []


def test_data_upload_prints_the_uri_first_and_a_directory_goes_up_as_a_collection(
    edison: Harness,
) -> None:
    """The URI is what `task submit --data` consumes, and the two upload calls are not alike."""
    folder = edison.workspace / "dataset"
    folder.mkdir()
    (folder / "counts.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    run = edison.run("data", "upload", str(folder), "-f", str(edison.key_file))
    assert run.returncode == 0, run.stderr
    assert run.first_line.startswith("DATA_URI: data_entry:")
    assert "SHAPE: collection" in run.stdout
    assert len(run.called("store_file_content")) == 1
    assert run.called("upload_file") == []


def test_data_upload_sends_a_single_file_the_other_way(edison: Harness) -> None:
    """A file is not a collection, and the default has to be right without a flag."""
    path = Path(edison.write("counts.csv", "a,b\n1,2\n"))
    run = edison.run("data", "upload", str(path), "-f", str(edison.key_file))
    assert run.returncode == 0, run.stderr
    assert run.first_line.startswith("DATA_URI: data_entry:")
    assert "SHAPE: file" in run.stdout
    assert len(run.called("upload_file")) == 1


def test_data_upload_takes_the_collection_flag_either_way(edison: Harness) -> None:
    """`--collection` and `--no-collection` override the default for whoever needs the other."""
    path = Path(edison.write("counts.csv", "a,b\n1,2\n"))
    forced = edison.run("data", "upload", str(path), "--collection", "-f", str(edison.key_file))
    assert forced.returncode == 0, forced.stderr
    assert len(forced.called("store_file_content")) == 1

    folder = edison.workspace / "dataset"
    folder.mkdir()
    (folder / "counts.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    plain = edison.run("data", "upload", str(folder), "--no-collection", "-f", str(edison.key_file))
    assert plain.returncode == 0, plain.stderr
    assert "hierarchical route" in plain.stderr


def test_data_search_prints_entries_without_an_account(edison: Harness) -> None:
    """Searching first is what stops a second copy of a dataset nobody can tell apart."""
    run = edison.run("data", "search", "--text", "counts", "-f", str(edison.key_file))
    assert run.returncode == 0, run.stderr
    assert "ENTRY: data_entry:" in run.stdout
    assert ACCOUNT not in run.stdout


def test_task_list_prints_rows_without_an_account(edison: Harness) -> None:
    """The listing is the way back to an id nobody wrote down, and it is free."""
    run = edison.run("task", "list", "-n", "5", "-f", str(edison.key_file))
    assert run.returncode == 0, run.stderr
    assert run.called("get_tasks")[0]["kwargs"] == {"limit": 5}
    assert ACCOUNT not in run.stdout


def test_project_add_task_files_a_run_under_a_project(edison: Harness) -> None:
    """references/tasks.md's "make a run visible in the browser" recipe, as one call."""
    run = edison.run(
        "project",
        "add-task",
        "--project",
        PROJECT_ID,
        "--task",
        TASK_ID,
        "-f",
        str(edison.key_file),
    )
    assert run.returncode == 0, run.stderr
    assert run.called("add_task_to_project")[0]["trajectory_id"] == TASK_ID
