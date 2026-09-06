"""Turning what a person types into the id the platform wants.

A UUID is what every client method takes and nothing a person can hold in their head, so
`--project` and `--persona` accept a name as well. The rule is one line: **if it parses as a
UUID it is an id, otherwise it is a name.**

Resolving a name is where this gets dangerous, so the resolver refuses on both edges rather
than choosing. Nothing found is a refusal that says what was looked for. More than one is a
refusal that prints every candidate with its id. It never picks. `get_project_by_name` in the
client picks — it answers with a bare `UUID` for one match and a `list[UUID]` for several,
which is the trap this module exists instead of.

A project name is unique only inside a persona, so resolving one needs a persona. Resolving a
persona name needs nothing.

## The cache

Names are cached so that typing one twice does not list twice. It is a convenience and never
a source of truth:

* it lives on the machine, outside the repo and outside the plugin directory — a plugin
  update wipes that directory, and `tests/lint.sh` sweeps the repo;
* it holds names and UUIDs, and nothing else ever. Not the key, not one byte of the key file;
* `--no-cache` bypasses it and refreshes what it holds;
* **every command that spends or destroys resolves live and ignores it entirely.** A stale
  entry mapping a name to an id that was deleted and recreated is exactly how the wrong
  project gets deleted, so `project delete`, `kosmos start`, `kosmos stop` and `task submit`
  never read it.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

from edison_cli.runtime import Refusal

if TYPE_CHECKING:  # pragma: no cover - typing only
    from edison_client import EdisonClient

PERSONAS_PATH = "/v0.1/personas"
# Overridable so the tests, and anyone with an unusual home directory, can put it elsewhere.
# A path, never a secret.
CACHE_ENV = "EDISON_CLI_CACHE"


@dataclass(frozen=True)
class Resolved:
    """One id, and the name it came from when a name is what was typed."""

    id: UUID
    name: str = ""
    row: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------- the two listings


def list_personas(client: EdisonClient, limit: int = 50) -> list[dict[str, Any]]:
    """List the account's personas through the client's own authenticated HTTP client.

    There is no persona method on the client at all — every one it has wants the persona id
    you are trying to find — so this goes one level under it.
    """
    response = client.client.get(PERSONAS_PATH, params={"limit": limit})
    if response.status_code != 200:
        body = " ".join((response.text or "").split())
        raise Refusal(
            f"the platform answered {response.status_code} listing personas: {body[:300]}", 1
        )
    payload = response.json()
    rows = payload if isinstance(payload, list) else payload.get("items", [])
    found = [row for row in rows if isinstance(row, dict)]  # pyright: ignore[reportUnknownVariableType]
    remember("personas", "", found)
    return found


def list_projects(client: EdisonClient, persona: UUID) -> list[dict[str, Any]]:
    """List the projects one persona owns. Untyped rows, so the id is read by key."""
    rows = client.list_persona_owned_projects(persona, limit=50)
    remember("projects", str(persona), rows)
    return rows


# ---------------------------------------------------------------- the cache


def cache_path() -> Path:
    """Say where the name cache lives on this machine."""
    override = os.environ.get(CACHE_ENV)
    if override:
        return Path(override)
    return Path.home() / ".claude" / "compute" / "edison-cli-names.json"


def _read() -> dict[str, Any]:
    """Read the cache, treating anything unreadable as an empty one."""
    try:
        loaded = json.loads(cache_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def remember(kind: str, scope: str, rows: list[dict[str, Any]]) -> None:
    """Record the names in one listing. Names and ids only, and a failure is not an error."""
    known = _read()
    bucket = known.setdefault(kind, {})
    if not isinstance(bucket, dict):
        bucket = known[kind] = {}
    inner = bucket.setdefault(scope, {})
    if not isinstance(inner, dict):
        inner = bucket[scope] = {}
    for row in rows:
        name, found = str(row.get("name") or ""), str(row.get("id") or "")
        if name and found:
            inner[name] = found
    try:
        path = cache_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(known, indent=1, sort_keys=True), encoding="utf-8")
        path.chmod(0o600)
    except OSError:
        # A cache that cannot be written is a cache that is not used. Never a failure: the
        # command it is helping has real work to do.
        return


def _recall(kind: str, scope: str, name: str) -> UUID | None:
    """Look one name up in the cache, ignoring anything that is not a UUID any more."""
    bucket = _read().get(kind)
    inner = bucket.get(scope) if isinstance(bucket, dict) else None
    found = inner.get(name) if isinstance(inner, dict) else None
    try:
        return UUID(str(found)) if found else None
    except ValueError:
        return None


# ---------------------------------------------------------------- resolution


def as_id(value: str) -> UUID | None:
    """Read a value as an id, or answer `None` when it is a name."""
    try:
        return UUID(value)
    except ValueError:
        return None


def _needs_a_persona(value: str) -> Refusal:
    """Build the refusal for a project name with no persona to look it up inside."""
    return Refusal(
        f"'{value}' is not a project id, and a project name is unique only inside a "
        "persona. Pass --persona as well, or give the project's id."
    )


def check_shapes(project_value: str | None, persona_value: str | None) -> None:
    """Say whether `--project` could resolve at all, from the arguments and nothing else.

    This is the half of resolution that needs no client, so it is the half a caller can run
    before one exists — building the client authenticates and lists the account's
    organisations, and an argument refused after that has already paid for a round trip.

    Only the SHAPE moves this early. A value that parses as a UUID is an id and needs no
    lookup; a value that does not is a name, and looking a name up is what the client is
    for, so `persona` and `project` below stay where they are. What is knowable here is the
    pair that has no lookup at all: a project name with no persona has no listing to be
    found in, whatever the platform would have said.
    """
    if project_value is not None and as_id(project_value) is None and not persona_value:
        raise _needs_a_persona(project_value)


def _pick(matches: list[dict[str, Any]], kind: str, wanted: str, listing: str) -> Resolved:
    """Choose the one match, or refuse — never choose between several."""
    if not matches:
        raise Refusal(f"no {kind} called '{wanted}'. `{listing}` shows what there is.", 1)
    if len(matches) > 1:
        lines = "\n".join(f"    {row.get('id')}  {row.get('name')}" for row in matches)
        raise Refusal(
            f"{len(matches)} {kind}s are called '{wanted}'. Re-run with the id:\n{lines}", 1
        )
    row = matches[0]
    return Resolved(UUID(str(row.get("id"))), str(row.get("name") or ""), row)


def persona(client: EdisonClient, value: str, *, live: bool = False) -> Resolved:
    """Resolve `--persona`, which may be an id or a name."""
    found = as_id(value)
    if found is not None:
        return Resolved(found)
    if not live:
        cached = _recall("personas", "", value)
        if cached is not None:
            return Resolved(cached, value)
    return _pick(
        [row for row in list_personas(client) if str(row.get("name")) == value],
        "persona",
        value,
        "edison-cli persona list",
    )


def project(
    client: EdisonClient, value: str, *, owner: UUID | None, live: bool = False
) -> Resolved:
    """Resolve `--project`, which may be an id or, given a persona, a name."""
    found = as_id(value)
    if found is not None:
        return Resolved(found)
    if owner is None:
        raise _needs_a_persona(value)
    if not live:
        cached = _recall("projects", str(owner), value)
        if cached is not None:
            return Resolved(cached, value)
    return _pick(
        [row for row in list_projects(client, owner) if str(row.get("name")) == value],
        "project",
        value,
        "edison-cli project list --persona <id>",
    )


def both(
    client: EdisonClient, *, project_value: str, persona_value: str | None, live: bool = False
) -> tuple[Resolved, Resolved | None]:
    """Resolve a project and its optional persona together, in the order they depend on."""
    owner = persona(client, persona_value, live=live) if persona_value else None
    return project(client, project_value, owner=owner.id if owner else None, live=live), owner


def name_of(client: EdisonClient, target: UUID, owner: UUID | None) -> str:
    """Find what a project is called, which only its persona's listing can answer.

    The tasks under a project carry `project_name`, but a project with no tasks has no tasks
    to carry it — and an empty project is exactly the one somebody is about to delete.
    """
    if owner is None:
        return ""
    for row in list_projects(client, owner):
        if str(row.get("id")) == str(target):
            return str(row.get("name") or "")
    return ""
