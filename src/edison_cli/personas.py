"""Personas: the objects a Kosmos run has to live under, and the only ones with no client method.

`edison-client` has no persona listing anywhere. Every persona method it does have —
`create_project(persona_id=...)`, `list_persona_owned_projects(persona_id)` — wants the id
you are trying to find, and `get_project_by_name` searches *within* a persona, so it can
never discover one. The route is the authenticated HTTP client the package already exposes,
which is what discussion #41 used, and `edison_cli.resolve` owns the call so that every
listing teaches the name cache.

The job name matters as much as the id. `metadata.persona_job_name` is stamped on the
persona and readable for free, before anything is spent, which makes it the authoritative
source — better than reading a job name back off a session someone already paid for.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from edison_cli import resolve
from edison_cli.runtime import Refusal, say, without_account

if TYPE_CHECKING:  # pragma: no cover - typing only
    from edison_client import EdisonClient


def fetch(client: EdisonClient, limit: int = 50) -> list[dict[str, Any]]:
    """List the account's personas. `resolve` owns the call, so the name cache learns from it."""
    return resolve.list_personas(client, limit)


def job_name(persona: dict[str, Any]) -> str:
    """Read the job name the platform stamped on a persona, or an empty string if it has none."""
    metadata = persona.get("metadata") or {}
    if not isinstance(metadata, dict):
        return ""
    return str(metadata.get("persona_job_name") or "")


def find(client: EdisonClient, *, name: str | None, persona_id: str | None) -> dict[str, Any]:
    """Find one persona by name or by id, refusing rather than guessing between several."""
    rows = fetch(client)
    if persona_id:
        matches = [row for row in rows if str(row.get("id")) == persona_id]
        wanted = f"id {persona_id}"
    else:
        matches = [row for row in rows if str(row.get("name")) == name]
        wanted = f"name '{name}'"
    if not matches:
        known = ", ".join(sorted(str(row.get("name")) for row in rows)) or "none"
        raise Refusal(f"no persona with {wanted}. This account has: {known}", 1)
    if len(matches) > 1:
        ids = ", ".join(str(row.get("id")) for row in matches)
        raise Refusal(f"several personas share {wanted}: {ids} — ask for one by id", 1)
    return matches[0]


def list_personas(client: EdisonClient) -> int:
    """Print every persona, with the job name a Kosmos run under it would use."""
    rows = fetch(client)
    for row in rows:
        cells = [str(row.get("id", "")), str(row.get("name", "")), job_name(row) or "(no job name)"]
        say("PERSONA: " + "\t".join(cells))
    if not rows:
        say("(this account has no personas)")
    return 0


def show(client: EdisonClient, *, name: str | None, persona_id: str | None) -> int:
    """Print one persona in full, job name first, so a run can be started from it."""
    persona = find(client, name=name, persona_id=persona_id)
    say(f"PERSONA_ID: {persona.get('id')}")
    say(f"PERSONA_NAME: {persona.get('name')}")
    job = job_name(persona)
    say(
        f"PERSONA_JOB_NAME: {job}" if job else "PERSONA_JOB_NAME: (none in this persona's metadata)"
    )
    for key, value in sorted(without_account(persona).items()):
        if key not in {"id", "name", "metadata"}:
            say(f"{key.upper()}: {value}")
    return 0
