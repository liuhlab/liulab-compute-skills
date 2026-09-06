"""The one-shot task lifecycle: submit, poll, list, fetch, cancel.

The properties here are the ones `docs/adr/0010` fixed and this package inherits.

* SUBMISSION TAKES A FILE, never an inline string, so the artefact the user confirmed is the
  artefact that goes out. Absent or empty is refused, exit 2, and nothing is spent.
* THE TASK ID IS THE FIRST LINE OF STDOUT. Stdout carries data and stderr carries narration,
  so the receipt for the credit leads the output and no verdict line can push it down.
* IT RETURNS AT ONCE. Submission makes one call. The client's blocking wait helper is never
  reached from here, and neither is anything else that waits for a run to end.

`JOBS` is the whole API surface this command will send, and its narrowness is the point: the
client sends any string it is handed, so an allow-list is what turns "never guess a job-name
string" into something that cannot be guessed past. `references/jobs.md` owns which question
routes to which member and that table is not repeated here. `NOT_SENT` is the other half: two
enum members that are absent on purpose, each with the reason a caller meets instead of them.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from edison_cli import datasets, resolve
from edison_cli.runtime import (
    Refusal,
    identifier,
    note,
    say,
    text_from_file,
    without_account,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from edison_client import EdisonClient

JOBS = ("LITERATURE", "LITERATURE_HIGH", "PRECEDENT", "MOLECULES", "ANALYSIS")

# Real `JobNames` members this command will not send, and why. Both answered 404 to a new
# submission, so sending one buys a round trip and no task. They are named rather than merely
# missing, because "unknown job" is untrue of a member that is right there in the enum, and a
# reader told the wrong thing goes looking for a spelling mistake instead of reading the page.
NOT_SENT = {
    "PHOENIX": (
        "the package's own comment retires it — new submissions 404. Chemistry goes to MOLECULES"
    ),
    "DUMMY": (
        "a new submission 404'd on 2026-09-06 and created nothing. Nothing routes to it: it does "
        "no science, so there is no question it is the answer to"
    ),
}

# What a 404 means on the submit path, where no id has been handed out yet. `runtime.LOST_ID`
# would send the reader after a lost-id problem they do not have.
SUBMIT_404 = (
    "the platform would not take that submission and nothing was created — check the job name "
    "against references/jobs.md, and any id passed to --project or --continue"
)


def check_job(name: str) -> str:
    """Fold a job name to its member spelling, refusing anything off the routing table."""
    job = name.upper()
    if job in NOT_SENT:
        raise Refusal(
            f"'{job}' is a real JobNames member that this command will not send: {NOT_SENT[job]}. "
            f"references/jobs.md. One of: {' '.join(JOBS)}"
        )
    if job not in JOBS:
        raise Refusal(
            f"unknown job '{job}'. Route from references/jobs.md; never invent a name. "
            f"One of: {' '.join(JOBS)}"
        )
    return job


def submit(
    client: EdisonClient,
    *,
    job: str,
    query_file: str,
    data: list[str],
    cont: str | None,
    project: str | None,
    persona: str | None,
) -> int:
    """Create one task from the query file and print its id first. Returns at once.

    Names resolve live and never from the cache: this is the command that spends.
    """
    from edison_client.models.app import JobNames, RuntimeConfig, TaskRequest

    member = check_job(job)
    query = text_from_file(query_file, "query file", "nothing was submitted")

    fields: dict[str, Any] = {"name": JobNames[member], "query": query}
    if cont:
        # The field is `continued_job_id`; the vendor's README calls it something else and
        # TaskRequest rejects unknown fields outright. references/jobs.md.
        fields["runtime_config"] = RuntimeConfig(continued_job_id=identifier(cont, "task"))
    if project:
        fields["project_id"] = resolve.both(
            client, project_value=project, persona_value=persona, live=True
        )[0].id

    # On stderr, so stdout still opens with the task id. This is the audit trail: the job and
    # the exact text that went out, in the transcript, beside the id it produced.
    note(f"edison-cli: submitting {member} with the query in {query_file}:")
    for line in query.splitlines():
        note(f"  | {line}")
    if data:
        note("edison-cli: attaching:")
        for uri in data:
            note(f"  | {uri}")

    created = client.create_task(TaskRequest(**fields), files=list(data) or None)
    say(f"TASK_ID: {created}")
    return 0


def status(client: EdisonClient, *, task_id: str) -> int:
    """One poll: the task's status, and whether that status is terminal."""
    from edison_client.models.rest import ExecutionStatus

    task = client.get_task(task_id, lite=True)
    say(f"STATUS: {task.status}")
    say(f"TERMINAL: {'yes' if ExecutionStatus(task.status).is_terminal_state() else 'no'}")
    return 0


def list_tasks(
    client: EdisonClient,
    *,
    limit: int | None,
    project: str | None,
    persona: str | None,
    live: bool,
) -> int:
    """Print your own tasks, newest first. Costs nothing — the way back to an id you lost."""
    kwargs: dict[str, Any] = {}
    if limit:
        kwargs["limit"] = limit
    if project:
        kwargs["project_id"] = resolve.both(
            client, project_value=project, persona_value=persona, live=live
        )[0].id
    # Raw dicts, not models: the job name is under `crow` and the query under `task`.
    for row in client.get_tasks(**kwargs):
        cells = [str(row.get(key, "")) for key in ("created_at", "crow", "status", "id")]
        cells.append(str(row.get("task", ""))[:80].replace("\n", " "))
        say("TASK: " + "\t".join(cells))
    return 0


def cancel(client: EdisonClient, *, task_id: str) -> int:
    """Stop a run that has not finished. It is still charging while anyone deliberates.

    `False` means the task had already reached a terminal state, not that the cancel failed.
    A missing id raises out of the client's own leading lookup, and `runtime.sentence` turns
    that 404 into a sentence about the id rather than a traceback about the cancel.
    """
    say(f"CANCELLED: {'yes' if client.cancel_task(task_id) else 'no'}")
    return 0


def fetch(client: EdisonClient, *, task_id: str, out: str | None, storage: str | None) -> int:
    """Print what the run produced, and with `--out` write all of it to disk.

    `--out` used to promise more than it kept: it wrote the notebook and copied storage
    downloads, and left the answer — the thing anyone actually wanted — in the transcript
    only. It writes the answer now, and every line below names the file it wrote.

    `--storage` never reads `task_id`, so the honest spelling of a download is `data get`.
    This path stays for the one-shot flow that documents it, and calls the same function.
    """
    if storage:
        return datasets.get(client, storage=storage, out=out)
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)

    task = client.get_task(task_id)
    # A task can reach success carrying no answer, so this is the honest check. Whether it is
    # a property or a method is not recorded, and a bound method is truthy — which would
    # report every run as answered — so call it when it is callable.
    answered = getattr(task, "has_successful_answer", None)
    if callable(answered):
        answered = answered()
    say(f"HAS_ANSWER: {'yes' if answered else 'no'}")

    # formatted_answer exists on a literature-shaped response and not on an analysis one,
    # where reaching for it raises on a run that succeeded.
    answer = getattr(task, "formatted_answer", None) or getattr(task, "answer", None)
    if answer and out:
        destination = Path(out) / f"{task_id}.answer.md"
        destination.write_text(str(answer), encoding="utf-8")
        say(f"ANSWER_FILE: {destination}")
    elif answer:
        say("ANSWER:")
        say(str(answer))

    notebook = getattr(task, "notebook", None)
    if notebook and out:
        destination = Path(out) / f"{task_id}.ipynb"
        destination.write_text(json.dumps(notebook), encoding="utf-8")
        say(f"NOTEBOOK: {destination}")
    elif notebook:
        say("NOTEBOOK: present — pass --out <dir> to write it as .ipynb")

    # list_files returns a dict with one key, `data`, holding provenance records. Which field
    # of a record carries the storage id is NOT recorded in references/datasets.md, so the
    # record is printed whole rather than guessed at — minus whatever names the account it
    # belongs to. Read the id out of it and pass it back as --storage.
    for record in client.list_files(task_id)["data"]:
        say("FILE: " + json.dumps(without_account(record), default=str))
    say("(no FILE lines means the run wrote nothing worth keeping)")
    return 0
