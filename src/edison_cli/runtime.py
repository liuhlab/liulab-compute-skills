"""What every subcommand shares: the key's route in, and a failure that reads as a sentence.

Three of the four properties `docs/adr/0007` and `docs/adr/0010` fix live here.

* THE PREFLIGHT RUNS BEFORE A CLIENT EXISTS. `client` is the only constructor in the
  package, and it refuses before it builds one, so a skipped step zero refuses instead of
  spending — including in agent tools that ignore `disable-model-invocation`.
* THE KEY REACHES THE CLIENT THROUGH THE ENVIRONMENT AND BY NO OTHER ROUTE. The preflight
  reads it out of the key file and `Report.export` puts it in this process's environment,
  where `edison-client` looks for it. It is never an argument, never on a command line,
  never printed, and never written into this package.
* A CLIENT FAILURE READS AS A SENTENCE. `sentence` handles the raw `httpx.HTTPStatusError`
  the client re-raises for 429/500/502/503/504 as well as its own exception classes, of
  which there are two unrelated trees called `RestClientError`. It does that by reading the
  response off the exception rather than by catching a class, so neither tree can slip past.

The fourth — an identifier first, before anything can block — belongs to each command and is
written where the identifier is produced.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

from edison_cli import preflight

if TYPE_CHECKING:  # pragma: no cover - the client is imported lazily, see `client` below
    from edison_client import EdisonClient


class Refusal(Exception):  # noqa: N818 - see the docstring
    """A refusal that carries its exit code. Nothing was spent.

    Exit 2 is the default and means the request was malformed — a missing file, an id that
    is not an id, a job name off the routing table. Exit 1 means the request was fine and
    the machine or the platform was not.

    Named `Refusal` rather than `RefusalError`, against the naming rule, because refusing is
    this skill's own word: every page that documents the command says the agent *refuses*,
    and the rule exists to stop exception names that do not read as failures. This one does.
    """

    def __init__(self, message: str, code: int = 2) -> None:
        super().__init__(message)
        self.code = code


def say(line: str) -> None:
    """Print one line of data, flushed.

    Flushed because the first line of a spending command is the receipt for a credit, and it
    has to outlive whatever happens next.
    """
    print(line, flush=True)


def clipped(text: str, limit: int) -> str:
    """Cut one piece of platform text to `limit` characters, and say on the line that it was cut.

    The caps are real: a run says thousands of characters at a time and one command must not
    flood a transcript with them. Cutting in silence is the bug. Everything printed here ends
    up in an agent's transcript, where a sentence that stops mid-word reads as the whole
    answer and nothing distinguishes a clipped line from a finished one — so the cut becomes
    a wrong answer further downstream. The marker says how much is missing, which is the
    reader's cue to go to the transcript or the entry itself for the rest.

    It carries no tab and no newline: two of the three callers print tab-separated rows that
    are read by eye and split by column.
    """
    missing = len(text) - limit
    if missing <= 0:
        return text
    return f"{text[:limit]}… [+{missing} chars cut]"


def note(line: str) -> None:
    """Print one line of narration on stderr, so stdout stays the receipt."""
    print(line, file=sys.stderr, flush=True)


def client(key_file: str | None) -> EdisonClient:
    """Run the preflight, put the key in the environment, and build the one client.

    The import is inside the function on purpose. Importing `edison_client` costs seconds,
    and a refusal — a missing query file, an unconfigured machine — should not pay for it.
    """
    report = preflight.check(key_file)
    if not report.ok:
        note(report.text())
        note("")
        raise Refusal(
            "this machine is not configured for the Edison platform. The fix is above; the "
            "user pastes the key into the file themselves.",
            1,
        )
    report.export()
    from edison_client import EdisonClient

    # Constructing the client is already a network call: it authenticates and fetches your
    # organisations, so a bad key fails here rather than at submission.
    return EdisonClient()


# What a 404 means for a call that carried an id, which is most of them. It is a default and
# not a law: a command where no id is involved passes its own, because a sentence that sends
# the reader after a lost id they never had is worse than no sentence at all.
LOST_ID = "the platform has no record of that id — `task list` finds ids again"


def sentence(exc: BaseException, *, not_found: str = LOST_ID) -> str:
    """Say what went wrong in one line, without a traceback and without an id nobody has."""
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    if isinstance(status, int):
        body = " ".join((getattr(response, "text", "") or "").split())
        if status == 404:
            return f"{not_found} (404)"
        if status in {401, 403}:
            return f"the platform refused the key ({status}) — re-run `edison-cli preflight`"
        if body:
            return f"the platform answered {status}: {body[:400]}"
        return f"the platform answered {status} and said nothing more"
    text = str(exc).strip()
    return f"{type(exc).__name__}: {text}" if text else type(exc).__name__


def identifier(text: str, what: str) -> UUID:
    """Read one id the client insists on as a UUID, refusing anything that is not one."""
    try:
        return UUID(text)
    except ValueError as exc:
        raise Refusal(f"'{text}' is not a {what} id") from exc


def text_from_file(path: str, what: str, undone: str) -> str:
    """Read the text a run will be charged for out of a file, refusing before anything spends.

    A file and never an inline string, so the artefact the user confirmed is the artefact
    that goes out.
    """
    where = Path(path)
    if not where.is_file():
        raise Refusal(f"no {what} at '{path}' — {undone}")
    body = where.read_text(encoding="utf-8")
    if not body.strip():
        raise Refusal(f"the {what} '{path}' is empty — {undone}")
    return body


def invocation() -> str:
    """Spell this command the way the skill types it, so a printed command is runnable.

    The skill reaches the package through pixi with an explicit manifest, because it runs
    from the installed plugin while the working directory is the user's own project. The
    path is spelled with a tilde, which the shell expands, rather than with a home directory
    that carries a username.
    """
    root = Path(__file__).resolve().parents[2]
    manifest = root / "pyproject.toml"
    if not manifest.is_file():
        return "edison-cli"
    return f"pixi run --manifest-path {preflight.display(manifest)} edison-cli"


def as_dict(row: Any) -> dict[str, Any]:
    """Read a client response as a plain dict, whether it arrived as a model or as one already.

    The client is inconsistent about this on purpose: task listings come back as raw dicts
    and conversations as pydantic models, and callers here want one shape.
    """
    dumper = getattr(row, "model_dump", None)
    payload: Any = dumper() if callable(dumper) else row
    if not isinstance(payload, dict):
        return {}
    return {str(key): value for key, value in payload.items()}


# Whatever a platform record calls the account it belongs to. Printing one puts a person's
# identity in a transcript for no gain: the caller already knows whose account it is.
ACCOUNT_KEYS = frozenset(
    {"user", "user_id", "userid", "owner", "owner_id", "email", "created_by", "username"}
)


def without_account(record: dict[str, Any]) -> dict[str, Any]:
    """Drop whatever identifies the account from a record before it is printed."""
    return {k: v for k, v in record.items() if k.lower() not in ACCOUNT_KEYS}
