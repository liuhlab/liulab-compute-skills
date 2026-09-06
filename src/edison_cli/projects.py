"""Projects, which on this platform are persona-owned or they are broken.

A project created without a persona is accepted happily by the API and then makes the chat
endpoint answer 500 with no body — discussion #41 paid for that discovery. There is no
persona-less form here for that reason: `--persona` is required by the parser, so an orphan
project is not expressible through this command at all.

`get_project_by_name` is not used anywhere below. It raises when a project is absent, which
makes "does this exist yet?" an exception handler rather than a question, and it also accepts
a persona to search *within* — so it can confirm a project and never discover one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from edison_cli import resolve
from edison_cli.runtime import Refusal, note, say

if TYPE_CHECKING:  # pragma: no cover - typing only
    from edison_client import EdisonClient


def owned(client: EdisonClient, persona: UUID) -> list[dict[str, Any]]:
    """List the projects a persona owns. `resolve` owns the call, so the cache learns from it."""
    return resolve.list_projects(client, persona)


def _confirm_ownership(client: EdisonClient, persona: UUID, project: object) -> None:
    """Say whether the persona really owns the project, because an invisible run is a failed run.

    A run in an orphan project does not appear under the persona in the browser, and nobody
    can find it afterwards however good the answer.
    """
    ids = {str(row.get("id")) for row in owned(client, persona)}
    yes = str(project) in ids
    say(f"PERSONA_OWNS_PROJECT: {'yes' if yes else 'no'}")
    if not yes:
        note(
            "edison-cli: the persona does not own this project. A Kosmos run started in it "
            "will answer 500, and nothing will be visible in the browser."
        )


def create(
    client: EdisonClient, *, name: str, persona: str, description: str | None, live: bool
) -> int:
    """Create one persona-owned project and print its id before anything else can happen."""
    owner = resolve.persona(client, persona, live=live).id
    created = client.create_project(name=name, description=description, persona_id=owner)
    say(f"PROJECT_ID: {created}")
    _confirm_ownership(client, owner, created)
    return 0


def list_projects(client: EdisonClient, *, persona: str, live: bool) -> int:
    """Print the projects one persona owns, newest first."""
    owner = resolve.persona(client, persona, live=live).id
    rows = owned(client, owner)
    for row in rows:
        cells = [str(row.get("id", "")), str(row.get("name", "")), str(row.get("created_at", ""))]
        say("PROJECT: " + "\t".join(cells))
    if not rows:
        say("(this persona owns no projects)")
    return 0


def ensure(
    client: EdisonClient, *, name: str, persona: str, description: str | None, live: bool
) -> int:
    """Reuse the persona's project of this name, or create it. Either way, print the id first."""
    owner = resolve.persona(client, persona, live=live).id
    matches = [row for row in owned(client, owner) if str(row.get("name")) == name]
    if matches:
        say(f"PROJECT_ID: {matches[0].get('id')}")
        say("REUSED: yes")
        if len(matches) > 1:
            note(
                f"edison-cli: this persona has {len(matches)} projects named '{name}'; "
                "the newest was reused. `project list` shows them all."
            )
        return 0
    created = client.create_project(name=name, description=description, persona_id=owner)
    say(f"PROJECT_ID: {created}")
    say("REUSED: no")
    _confirm_ownership(client, owner, created)
    return 0


def delete(
    client: EdisonClient,
    *,
    project: str,
    persona: str | None,
    delete_tasks: bool,
    yes: bool,
) -> int:
    """Delete one project, after saying exactly what will go with it.

    The only irreversible command in this package, so it is the only one with guards. It
    resolves live and never from the name cache: a cached entry mapping a name to an id that
    was deleted and recreated is how the wrong project gets deleted.

    The summary is printed whether or not the delete proceeds, so a refusal still leaves the
    receipt behind — what was about to go, what it is called, and how much of it there was.
    """
    doomed, owner = resolve.both(client, project_value=project, persona_value=persona, live=True)
    rows = client.get_tasks(project_id=doomed.id, limit=200)
    named = doomed.name or resolve.name_of(client, doomed.id, owner.id if owner else None)
    if not named:
        # A project's name lives on its persona's listing. With no persona there is nothing to
        # read it from, and the tasks are the only fallback — which an empty project has none of.
        found = {str(row.get("project_name")) for row in rows if row.get("project_name")}
        named = found.pop() if len(found) == 1 else "(not reachable — pass --persona to name it)"

    say(f"PROJECT_ID: {doomed.id}")
    say(f"PROJECT_NAME: {named}")
    say(f"N_TASKS: {len(rows)}")
    say(f"TRAJECTORIES: {'delete' if delete_tasks else 'keep'}")

    if not yes:
        say("DELETED: no")
        raise Refusal(
            "nothing was deleted. The summary above is what --yes would remove; re-run with "
            "--yes if that is what you want."
        )

    client.delete_project(doomed.id, delete_trajectories=delete_tasks)
    say("DELETED: yes")
    return 0


def add_task(
    client: EdisonClient, *, project: str, persona: str | None, task: str, live: bool
) -> int:
    """Give an existing run a browser home by filing its trajectory under a project."""
    home, _ = resolve.both(client, project_value=project, persona_value=persona, live=live)
    client.add_task_to_project(home.id, task)
    say(f"PROJECT_ID: {home.id}")
    say(f"ADDED_TASK: {task}")
    return 0
