"""Kosmos: start a run, watch it, find it again, and stop it.

Kosmos is a chat session that fans out into ordinary tasks, and the bill is the fan-out —
discussion #41 bought 33 tasks in 18 minutes and it was still growing when it was stopped.
Three facts from that run shape everything below.

* THE PROJECT MUST BE PERSONA-OWNED, or the chat endpoint answers 500 with no body. So
  `start` checks ownership before it sends anything.
* THERE IS NO RUN-LEVEL CANCEL. The only cancel on the platform is one task at a time, and
  the orchestrator replaces a cancelled task about a minute later. The queue endpoint is
  what actually halts it: the message is picked up by the rollout's next step. **So `stop`
  queues the halt first and sweeps second.** Do it the other way round and the orchestrator
  refills the tasks while you work.
* AN ASSISTANT MESSAGE'S `content` IS EMPTY. What the browser shows lives in
  `tool_calls[].function.arguments`, as a JSON string. Read `content` alone and a healthy
  run looks dead.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import TYPE_CHECKING, Any
from uuid import UUID

from edison_cli import datasets, personas, projects, resolve
from edison_cli.runtime import (
    Refusal,
    as_dict,
    clipped,
    clipped_lines,
    identifier,
    invocation,
    note,
    say,
    sentence,
    text_from_file,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from edison_client import EdisonClient

# What the run is told when someone stops it. Written out rather than improvised, because it
# is the one message that has to be unambiguous to a planner that is mid-flight.
HALT = (
    "Stop this run now. Do not plan any further work, do not dispatch any further subagent "
    "tasks, and do not start any new tool calls. This is a deliberate cancellation: the "
    "remaining work is no longer wanted. Acknowledge and halt."
)

# How much of the objective `start` echoes before it sends it. Enough to recognise which file
# went, and small enough that the whole command's output stays inside what an agent harness
# will render — which is what keeps the `STOP:` line at the bottom of it visible.
ECHO_LINES = 20


def _rows(client: EdisonClient, project: Any) -> list[dict[str, Any]]:
    """List every task under the run's project, which is the fan-out and the bill."""
    return client.get_tasks(project_id=project, limit=200)


def _live(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pick the tasks that can still spend.

    A status the client's own enum does not know is treated as live. Not cancelling a
    running task costs money; cancelling a finished one costs nothing and answers `False`.
    """
    from edison_client.models.rest import ExecutionStatus

    live: list[dict[str, Any]] = []
    for row in rows:
        try:
            terminal = ExecutionStatus(str(row.get("status", ""))).is_terminal_state()
        except ValueError:
            terminal = False
        if not terminal:
            live.append(row)
    return live


def _summarise(rows: list[dict[str, Any]]) -> None:
    """Print the fan-out as counts and as dispatch rounds, which is how it is read."""
    say(f"N_TASKS: {len(rows)}")
    say(f"JOB_NAMES: {dict(Counter(str(row.get('crow')) for row in rows))}")
    say(f"STATUSES: {dict(Counter(str(row.get('status')) for row in rows))}")
    # Tasks dispatched together land within the same minute, so the minute is the round.
    rounds: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        rounds.setdefault(str(row.get("created_at"))[11:16], []).append(row)
    for minute in sorted(rounds):
        batch = rounds[minute]
        jobs = Counter(str(row.get("crow")).replace("job-futurehouse-", "") for row in batch)
        say(f"ROUND: {minute}\tn={len(batch)}\t{dict(jobs)}")


def _conversation(client: EdisonClient, session: Any) -> list[dict[str, Any]]:
    """Read the run's turns once. `status` wants two different things out of the same call."""
    detail = as_dict(client.get_conversation(session, limit=1000))
    return [as_dict(message) for message in detail.get("messages") or []]


def _attached(messages: list[dict[str, Any]]) -> list[str]:
    """Read what the PLATFORM stored as the run's attachments, in the spelling `DATA:` prints.

    `send_chat_message` writes the ids into the outgoing message's `info`, and the
    conversation hands that dict straight back. So this is the platform's own record of what
    it bound to the run — the only thing that separates an attachment the field dropped from
    one the agent simply never opened, and it costs nothing to read.

    It normalises through `datasets.uri` because the two ends spell an entry differently: we
    send `data_entry:<uuid>` and the platform stores the bare stem. Unnormalised, `DATA:` and
    `ATTACHED:` cannot be compared by eye, which is the whole point of printing them.

    Guarded like `_project_of`, and for the same reason: `info` is the platform's dict, typed
    `dict | None`, and one malformed one must not cost the reader the rest of `status`.
    """
    stored: list[str] = []
    for message in messages:
        info = message.get("info")
        if not isinstance(info, dict):
            continue
        ids = info.get("data_storage_ids")
        if not isinstance(ids, list | tuple):
            continue
        stored.extend(datasets.uri(entry) for entry in ids)
    return stored


def _utterances(messages: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """Read what the run actually said, out of the tool-call arguments rather than `content`."""
    said: list[tuple[str, str]] = []
    for message in messages:
        for call in message.get("tool_calls") or []:
            function = as_dict(call).get("function") or {}
            try:
                arguments = json.loads(function.get("arguments") or "{}")
            except (TypeError, ValueError):
                arguments = {}
            text = arguments.get("display_text") or ""
            if not text:
                continue
            said.append(("SAY" if function.get("name") == "send_message" else "STEP", text))
    return said


def start(
    client: EdisonClient,
    *,
    project: str,
    persona: str,
    objective_file: str,
    data: list[str],
) -> int:
    """Start one Kosmos run from an objective file, printing every way back to it first.

    Names resolve live here and never from the cache: this is the command that spends.

    `data` is passed to the platform exactly as it was typed. The client normalises a
    `data_entry:` prefix itself, and both upload shapes — a file and a collection — wear the
    same URI, so a check here would only be able to reject spellings the platform accepts.
    """
    objective = text_from_file(objective_file, "objective file", "nothing was started")
    resolved, owner = resolve.both(client, project_value=project, persona_value=persona, live=True)
    run_project = resolved.id
    run_persona = owner.id if owner else identifier(persona, "persona")
    say(f"PROJECT_ID: {run_project}")

    job = personas.job_name(personas.find(client, name=None, persona_id=str(run_persona)))
    if not job:
        raise Refusal(
            "this persona carries no metadata.persona_job_name, so there is no job to start. "
            "`edison-cli persona list` shows which personas do.",
            1,
        )
    say(f"JOB_NAME: {job}")

    ids = {str(row.get("id")) for row in projects.owned(client, run_persona)}
    if str(run_project) not in ids:
        raise Refusal(
            "this persona does not own that project, and the chat endpoint answers 500 on a "
            "project no persona owns. Make one with `edison-cli project ensure`.",
            1,
        )
    say("PERSONA_OWNS_PROJECT: yes")

    # On stdout with the other ids, and BEFORE the send rather than after it. The response
    # says nothing about what was attached, so this is the only place an attachment that did
    # not happen is visible — and it is printed while nothing has been charged yet.
    for uri in data:
        say(f"DATA: {uri}")

    # Narration, and capped at a glance's worth. The objective is a file the user wrote and
    # confirmed, so echoing all of it says nothing new and costs the receipt below: past the
    # harness's inline limit the whole output is replaced by a preview taken from the top, and
    # `STOP:` is at the bottom. Showing the objective before the command runs is the agent's
    # job, not this echo's — `SKILL.md`, "show before you spend".
    note(f"edison-cli: starting Kosmos with the objective in {objective_file}:")
    for line in clipped_lines(objective, ECHO_LINES):
        note(f"  | {line}")

    response = as_dict(
        client.send_chat_message(
            run_project, objective, job_name=job, data_storage_ids=list(data) or None
        )
    )
    session = response.get("session_id")
    # First, flushed, before anything else can block: a run nobody can find again is the
    # failure this ordering guards against, and it has already been paid for.
    say(f"SESSION_ID: {session}")
    say(f"STOP: {invocation()} kosmos stop --project {run_project} --session {session}")
    say(f"STATUS: {invocation()} kosmos status --project {run_project} --session {session}")
    for key in ("status", "claim_name", "pod_name", "logs_url"):
        if response.get(key):
            say(f"CHAT_{key.upper()}: {response[key]}")
    return 0


def status(
    client: EdisonClient, *, project: str, persona: str | None, session: str, tail: int, live: bool
) -> int:
    """Poll one run: the fan-out, what the platform kept of the data, and the last few utterances.

    `ATTACHED:` is the other half of `start`'s `DATA:`. One says what was sent, the other what
    the platform stored against the message, so a dropped attachment stops being invisible.
    """
    run_project = resolve.both(client, project_value=project, persona_value=persona, live=live)[
        0
    ].id
    run_session = identifier(session, "session")
    say(f"PROJECT_ID: {run_project}")
    say(f"SESSION_ID: {run_session}")
    _summarise(_rows(client, run_project))
    messages = _conversation(client, run_session)
    # Beside the fan-out rather than among the utterances: it is a fact about the run, and it
    # is what `DATA:` from the start is read against. A run started without data has none, and
    # a placeholder line here would be indistinguishable from an attachment that was dropped.
    for entry in _attached(messages):
        say(f"ATTACHED: {entry}")
    said = _utterances(messages)
    say(f"N_UTTERANCES: {len(said)}")
    for kind, text in said[-tail:]:
        say(f"[{kind}] {clipped(text, 700)}")
    return 0


def tasks(
    client: EdisonClient, *, project: str, persona: str | None, session: str, live: bool
) -> int:
    """Print the whole fan-out row by row, both levels of it.

    The second level is real: the orchestrator dispatches tasks that dispatch their own
    children, so a job name here can belong to a task no human asked for.
    """
    run_project = resolve.both(client, project_value=project, persona_value=persona, live=live)[
        0
    ].id
    run_session = identifier(session, "session")
    say(f"PROJECT_ID: {run_project}")
    say(f"SESSION_ID: {run_session}")
    rows = _rows(client, run_project)
    for row in sorted(rows, key=lambda item: str(item.get("created_at"))):
        cells = [str(row.get(key, "")) for key in ("created_at", "crow", "status", "id")]
        cells.append(clipped(str(row.get("task", "")).replace("\n", " "), 80))
        say("TASK: " + "\t".join(cells))
    _summarise(rows)
    return 0


def _project_of(client: EdisonClient, session: Any) -> str:
    """Recover the project a session belongs to, which every other subcommand here needs.

    `get_session` answers with a list — one session id can name several rows — and the
    project id travels as `type_id`. Guarded, because one unreadable session must not cost
    the reader the rest of the listing.
    """
    try:
        rows = [as_dict(row) for row in client.get_session(UUID(str(session)))]
    except Exception:
        return ""
    for row in rows:
        if row.get("type_id"):
            return str(row["type_id"])
    return ""


def sessions(client: EdisonClient, *, limit: int) -> int:
    """List recent chat sessions with their projects — the way back to a lost session id.

    The project id is printed beside the session id rather than left to be looked up, because
    `status`, `tasks` and `stop` all need both, and a session id on its own is a dead end.
    Kosmos is the most expensive surface here, so it is the one that most needs a run to be
    found rather than bought a second time.
    """
    listing = client.get_conversations(limit=limit)
    rows = [as_dict(row) for row in listing.conversations]
    for row in rows:
        session = str(row.get("session_id", ""))
        cells = [session, _project_of(client, session) or "(project not recoverable)"]
        cells.append(str(row.get("created_at", "")))
        say("SESSION: " + "\t".join(cells))
    if not rows:
        say("(no chat sessions on this account)")
    return 0


def stop(client: EdisonClient, *, project: str, persona: str | None, session: str) -> int:
    """Halt one run: queue the stop FIRST, then cancel whatever is still in flight.

    The order is the whole point and it is not obvious. Cancelling first makes the
    orchestrator dispatch replacements while the sweep is still running, so the sweep loses
    a race it is paying for. The queued message is what actually stops the planner; the
    cancels only clean up what is already in the air.

    Names resolve live and never from the cache: stopping the wrong run is as expensive as
    starting one.
    """
    run_project = resolve.both(client, project_value=project, persona_value=persona, live=True)[
        0
    ].id
    run_session = identifier(session, "session")
    say(f"PROJECT_ID: {run_project}")
    say(f"SESSION_ID: {run_session}")

    try:
        queued = as_dict(client.queue_chat_message(run_session, run_project, HALT))
        say(f"QUEUED_STOP: {queued.get('id', 'sent')}")
    except Exception as exc:
        say("QUEUED_STOP: no")
        note(f"edison-cli: the halt could not be queued ({sentence(exc)}) — sweeping anyway")

    live = _live(_rows(client, run_project))
    say(f"TO_CANCEL: {len(live)}")
    results: Counter[str] = Counter()
    for row in live:
        task_id = str(row.get("id"))
        try:
            results["cancelled" if client.cancel_task(task_id) else "already_terminal"] += 1
        except Exception as exc:
            results["errors"] += 1
            note(f"edison-cli: {task_id} would not cancel ({sentence(exc)})")
    for key in ("cancelled", "already_terminal", "errors"):
        say(f"{key.upper()}: {results[key]}")

    after = _rows(client, run_project)
    say(f"N_TASKS_AFTER: {len(after)}")
    say(f"STATUSES_AFTER: {dict(Counter(str(row.get('status')) for row in after))}")
    say(f"STILL_LIVE: {len(_live(after))}")
    return 0
