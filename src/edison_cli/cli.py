"""The command line: one typer app, and the ordering that keeps a refusal from costing anything.

Two orderings in `_spend` are load-bearing and neither is visible in the parser.

* THE ARGUMENT CHECKS RUN BEFORE THE PREFLIGHT. Both refuse and neither spends, but this way
  a refusal for a missing query file says so on any machine — including one where the key IS
  configured, which is every machine a maintainer runs the gate on. It is also what lets the
  gate prove the ordering: the refusal fixtures pass a key file that does not exist, and a
  refusal that named the key file instead would mean the argument check never ran. `_ids` is
  what puts every id-shaped argument among those checks rather than in a command body, where
  reading it would already have cost the round trip that builds the client.
* THE PREFLIGHT RUNS BEFORE THE CLIENT EXISTS. `runtime.client` is the only constructor in
  the package, so there is no subcommand that can reach the platform around it.

The exit codes are 0 fine, 1 refused, 2 usage, and `_guard` is what holds them: a `Refusal`
carries its own code and click's own `UsageError` already exits 2, so a malformed command
line and a refusal this package makes itself answer the same way.

`edison_cli.preflight` is deliberately not driven from here. It parses its own arguments with
nothing but the standard library, because `tests/lint.sh` runs it with a bare interpreter
inside the no-secrets sweep. This module calls its FUNCTIONS; it never lends it typer.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any

import typer

from edison_cli import datasets, kosmos, personas, preflight, projects, resolve, runtime, tasks
from edison_cli.runtime import Refusal, note, say, sentence

HELP = """\
The Edison platform, as one command: check this machine, find a persona, make it a project,
run and stop Kosmos, submit and collect one-shot tasks, and move datasets.

Every subcommand that can spend runs the preflight first and refuses on a machine with no
key. The key is read from the key file into this process's environment and reaches the
client by no other route.
"""

# Plain click help rather than rich panels. Everything this command prints lands in an
# agent's transcript, where box-drawing characters and reflowed columns are noise a grep has
# to survive.
app = typer.Typer(
    name="edison-cli",
    help=HELP,
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
)
persona_app = typer.Typer(help="The personas a Kosmos run lives under.", no_args_is_help=True)
project_app = typer.Typer(
    help="Projects, which are persona-owned or they are broken.", no_args_is_help=True
)
kosmos_app = typer.Typer(
    help="The chat surface: start, watch, find and stop a run.", no_args_is_help=True
)
task_app = typer.Typer(
    help="The one-shot lifecycle: submit, poll, list, fetch, cancel.", no_args_is_help=True
)
data_app = typer.Typer(help="Datasets: upload one, find one already there.", no_args_is_help=True)
app.add_typer(persona_app, name="persona")
app.add_typer(project_app, name="project")
app.add_typer(kosmos_app, name="kosmos")
app.add_typer(task_app, name="task")
app.add_typer(data_app, name="data")

KeyFile = Annotated[
    str | None,
    typer.Option("-f", "--key-file", help="read the key from this file, not the configured one"),
]
Project = Annotated[
    str, typer.Option("--project", metavar="ID|NAME", help="the project's id, or its name")
]
Persona = Annotated[
    str, typer.Option("--persona", metavar="ID|NAME", help="the persona's id, or its name")
]
# Optional wherever `--project` is, because a project name is unique only inside a persona.
# A project name given without one is refused rather than guessed at.
OwnerOf = Annotated[
    str | None,
    typer.Option("--persona", metavar="ID|NAME", help="needed only to resolve a project NAME"),
]
NoCache = Annotated[
    bool,
    typer.Option("--no-cache", help="look names up on the platform and refresh what is remembered"),
]
Session = Annotated[str, typer.Option("--session", metavar="ID", help="the chat session's id")]
TaskId = Annotated[str, typer.Argument(metavar="TASK_ID", help="the task's id")]


def _guard(work: Callable[[], int], *, not_found: str = runtime.LOST_ID) -> None:
    """Run one command body, turning any failure into an exit code and never a traceback.

    A spend path answers in sentences. A traceback out of here would bury the one line that
    says whether anything was charged.

    `not_found` is what a 404 means for THIS command. This is the only place a client failure
    is turned into a sentence, and it cannot see which call raised — so the command says in
    advance. The default fits the many commands that hand the platform an id; `task submit`
    hands it none, and told the reader to go and find one with `task list`.
    """
    try:
        code = work()
    except Refusal as refusal:
        note(f"edison-cli: {refusal}")
        raise typer.Exit(refusal.code) from None
    except Exception as exc:
        note(f"edison-cli: {sentence(exc, not_found=not_found)}")
        raise typer.Exit(1) from None
    if code:
        raise typer.Exit(code)


def _spend(
    key_file: str | None,
    work: Callable[[Any], int],
    precheck: Callable[[], None] | None = None,
    *,
    not_found: str = runtime.LOST_ID,
) -> None:
    """Check the arguments, then the machine, then build the one client and do the work."""

    def run() -> int:
        if precheck is not None:
            precheck()
        return work(runtime.client(key_file))

    _guard(run, not_found=not_found)


def _ids(
    *,
    project: str | None = None,
    persona: str | None = None,
    session: str | None = None,
    task: str | None = None,
) -> None:
    """Refuse an argument that is not the id it has to be, before anything is built.

    This belongs in the precheck and nowhere later. `runtime.client` authenticates and
    fetches the account's organisations while it is being constructed, so an id read for the
    first time inside a command body has already cost a network round trip on its way to
    exit 2.

    ONLY THE SHAPE OF A VALUE MOVES HERE, and the next reader should not try to move the
    rest: turning a NAME into an id is a lookup, and a lookup needs the client this runs in
    front of. So `--project` and `--persona` names still resolve in the command body where
    they always did, and what comes forward is the one thing about a name that needs no
    platform — `resolve.check_shapes`, on a project name with no persona to be unique inside.

    Every refusal keeps the message and the exit code it had when it ran later, so nothing
    that reads this command's output can tell the difference except by what it did not spend.
    """
    resolve.check_shapes(project, persona)
    if session is not None:
        runtime.identifier(session, "session")
    if task is not None:
        runtime.identifier(task, "task")


# ---------------------------------------------------------------- preflight


@app.command("preflight")
def preflight_command(
    key_file: KeyFile = None,
    constants: Annotated[
        bool,
        typer.Option(
            "--constants",
            help="print the key-file constants as KEY=value lines and exit, reading no key file",
        ),
    ] = False,
) -> None:
    """Report whether this machine holds an Edison platform API key."""
    if constants:
        for line in preflight.constants(key_file):
            say(line)
        return
    report = preflight.check(key_file)
    say(report.text())
    if not report.ok:
        raise typer.Exit(1)


# ---------------------------------------------------------------- persona


@persona_app.command("list")
def persona_list(key_file: KeyFile = None) -> None:
    """List every persona, with the job name a run under it would use."""
    _spend(key_file, personas.list_personas)


@persona_app.command("show")
def persona_show(
    name: Annotated[str | None, typer.Option("--name", help="the persona's name")] = None,
    persona_id: Annotated[str | None, typer.Option("--id", help="the persona's id")] = None,
    key_file: KeyFile = None,
) -> None:
    """Show one persona, by name or by id, job name first."""

    def work(client: Any) -> int:
        return personas.show(client, name=name, persona_id=persona_id)

    def precheck() -> None:
        if bool(name) == bool(persona_id):
            raise Refusal("persona show needs exactly one of --name or --id")

    _spend(key_file, work, precheck)


# ---------------------------------------------------------------- project


@project_app.command("create")
def project_create(
    name: Annotated[str, typer.Option("--name", help="what the project is called")],
    persona: Persona,
    description: Annotated[str | None, typer.Option("--description")] = None,
    no_cache: NoCache = False,
    key_file: KeyFile = None,
) -> None:
    """Create one persona-owned project.

    --persona is required. A project no persona owns makes the chat endpoint answer 500, so
    it is not expressible here.
    """
    _spend(
        key_file,
        lambda client: projects.create(
            client, name=name, persona=persona, description=description, live=no_cache
        ),
    )


@project_app.command("list")
def project_list(persona: Persona, no_cache: NoCache = False, key_file: KeyFile = None) -> None:
    """List the projects one persona owns."""
    _spend(key_file, lambda client: projects.list_projects(client, persona=persona, live=no_cache))


@project_app.command("ensure")
def project_ensure(
    name: Annotated[str, typer.Option("--name")],
    persona: Persona,
    description: Annotated[
        str | None, typer.Option("--description", help="used only if it has to be created")
    ] = None,
    no_cache: NoCache = False,
    key_file: KeyFile = None,
) -> None:
    """Reuse the persona's project of this name, or create it."""
    _spend(
        key_file,
        lambda client: projects.ensure(
            client, name=name, persona=persona, description=description, live=no_cache
        ),
    )


@project_app.command("delete")
def project_delete(
    project: Project,
    persona: OwnerOf = None,
    delete_tasks: Annotated[
        bool | None,
        typer.Option(
            "--delete-tasks/--keep-tasks",
            help="whether the project's paid run history goes with it; there is no default",
        ),
    ] = None,
    yes: Annotated[
        bool, typer.Option("--yes", help="actually delete it; without this nothing is removed")
    ] = False,
    key_file: KeyFile = None,
) -> None:
    """Delete one project, after printing what will go with it.

    The only irreversible command here. It prints the project, its name and how many tasks it
    holds first, and removes nothing without --yes. The trajectory disposition has no default
    because the client's own default deletes paid run history. A name resolves live, never
    from the cache, and --persona is what makes a name resolvable at all.
    """

    def precheck() -> None:
        if delete_tasks is None:
            raise Refusal(
                "project delete needs --delete-tasks or --keep-tasks. The client's own default "
                "deletes the project's paid run history, so this command will not guess."
            )
        _ids(project=project, persona=persona)

    _spend(
        key_file,
        lambda client: projects.delete(
            client, project=project, persona=persona, delete_tasks=bool(delete_tasks), yes=yes
        ),
        precheck,
    )


@project_app.command("add-task")
def project_add_task(
    project: Project,
    task: Annotated[str, typer.Option("--task", metavar="ID", help="the trajectory to file")],
    persona: OwnerOf = None,
    no_cache: NoCache = False,
    key_file: KeyFile = None,
) -> None:
    """Give an existing run a browser home by filing it under a project."""
    _spend(
        key_file,
        lambda client: projects.add_task(
            client, project=project, persona=persona, task=task, live=no_cache
        ),
        lambda: _ids(project=project, persona=persona),
    )


# ---------------------------------------------------------------- kosmos


@kosmos_app.command("start")
def kosmos_start(
    project: Project,
    persona: Persona,
    objective_file: Annotated[
        str,
        typer.Option("--objective-file", metavar="FILE", help="the objective the user confirmed"),
    ],
    # `task submit --data`, down to the short form and the help text, because the bug this
    # fixes was a reader expecting the two surfaces to behave alike. Like that one it takes a
    # bare list and is deliberately absent from `_ids`: the platform normalises a `data_entry:`
    # prefix and rejects a bad id itself, and both upload shapes wear the same URI, so a check
    # here could only reject spellings the platform accepts.
    data: Annotated[
        list[str] | None,
        typer.Option("-d", "--data", metavar="URI", help="a data_entry: URI; repeat for several"),
    ] = None,
    key_file: KeyFile = None,
) -> None:
    """Start one run from an objective file.

    The objective comes from a file, never a string. The project must be owned by the persona
    or the platform answers 500. The project id, the job name, the ownership check and a DATA
    line for every entry --data attached are all printed BEFORE the send, so a missing DATA
    line means stop and nothing has been charged. The session id and the stop command come
    after it: the session does not exist until the send returns.
    """

    def precheck() -> None:
        runtime.text_from_file(objective_file, "objective file", "nothing was started")
        _ids(project=project, persona=persona)

    _spend(
        key_file,
        lambda client: kosmos.start(
            client,
            project=project,
            persona=persona,
            objective_file=objective_file,
            data=list(data or []),
        ),
        precheck,
    )


@kosmos_app.command("status")
def kosmos_status(
    project: Project,
    session: Session,
    tail: Annotated[int, typer.Option("--tail", help="how many recent utterances to print")] = 6,
    persona: OwnerOf = None,
    no_cache: NoCache = False,
    key_file: KeyFile = None,
) -> None:
    """Poll one run: the fan-out, what the platform kept of --data, and the last few utterances."""
    _spend(
        key_file,
        lambda client: kosmos.status(
            client, project=project, persona=persona, session=session, tail=tail, live=no_cache
        ),
        lambda: _ids(project=project, persona=persona, session=session),
    )


@kosmos_app.command("tasks")
def kosmos_tasks(
    project: Project,
    session: Session,
    persona: OwnerOf = None,
    no_cache: NoCache = False,
    key_file: KeyFile = None,
) -> None:
    """List every task the run dispatched, both levels of the fan-out."""
    _spend(
        key_file,
        lambda client: kosmos.tasks(
            client, project=project, persona=persona, session=session, live=no_cache
        ),
        lambda: _ids(project=project, persona=persona, session=session),
    )


@kosmos_app.command("sessions")
def kosmos_sessions(
    limit: Annotated[int, typer.Option("-n", "--limit", help="how many to list")] = 25,
    key_file: KeyFile = None,
) -> None:
    """List recent sessions with their projects — the way back to a lost session id."""
    _spend(key_file, lambda client: kosmos.sessions(client, limit=limit))


@kosmos_app.command("stop")
def kosmos_stop(
    project: Project, session: Session, persona: OwnerOf = None, key_file: KeyFile = None
) -> None:
    """Queue the halt, then cancel the stragglers.

    The halt is queued FIRST and the running tasks are cancelled second. Cancelling first
    makes the orchestrator dispatch replacements while the sweep runs, and the sweep loses a
    race it is paying for.
    """
    _spend(
        key_file,
        lambda client: kosmos.stop(client, project=project, persona=persona, session=session),
        lambda: _ids(project=project, persona=persona, session=session),
    )


# ---------------------------------------------------------------- task


@task_app.command("submit")
def task_submit(
    job: Annotated[str, typer.Option("-j", "--job", help=f"one of: {' '.join(tasks.JOBS)}")],
    query_file: Annotated[
        str,
        typer.Option(
            "-q", "--query-file", metavar="FILE", help="the file holding the confirmed query"
        ),
    ],
    data: Annotated[
        list[str] | None,
        typer.Option("-d", "--data", metavar="URI", help="a data_entry: URI; repeat for several"),
    ] = None,
    cont: Annotated[
        str | None,
        typer.Option(
            "-c",
            "--continue",
            metavar="TASK_ID",
            help="ride on a previous run instead of paying for its context again",
        ),
    ] = None,
    project: Annotated[
        str | None,
        typer.Option("-p", "--project", metavar="ID|NAME", help="the project it belongs to"),
    ] = None,
    persona: OwnerOf = None,
    key_file: KeyFile = None,
) -> None:
    """Create one task from a query file and print its id first. Returns at once.

    The query is a file and never a string: what the user confirmed is what is submitted.
    references/jobs.md says which question routes to which job.
    """

    def precheck() -> None:
        tasks.check_job(job)
        runtime.text_from_file(query_file, "query file", "nothing was submitted")
        _ids(project=project, persona=persona, task=cont)

    _spend(
        key_file,
        lambda client: tasks.submit(
            client,
            job=job,
            query_file=query_file,
            data=list(data or []),
            cont=cont,
            project=project,
            persona=persona,
        ),
        precheck,
        not_found=tasks.SUBMIT_404,
    )


@task_app.command("status")
def task_status(task_id: TaskId, key_file: KeyFile = None) -> None:
    """One poll: the task's status, and whether that status is terminal."""
    _spend(key_file, lambda client: tasks.status(client, task_id=task_id))


@task_app.command("list")
def task_list(
    limit: Annotated[int | None, typer.Option("-n", "--limit", metavar="N")] = None,
    project: Annotated[str | None, typer.Option("-p", "--project", metavar="ID|NAME")] = None,
    persona: OwnerOf = None,
    no_cache: NoCache = False,
    key_file: KeyFile = None,
) -> None:
    """List your own tasks, newest first. Costs nothing — the way back to a lost id."""
    _spend(
        key_file,
        lambda client: tasks.list_tasks(
            client, limit=limit, project=project, persona=persona, live=no_cache
        ),
        lambda: _ids(project=project, persona=persona),
    )


@task_app.command("fetch")
def task_fetch(
    task_id: TaskId,
    out: Annotated[
        str | None,
        typer.Option("-o", "--out", metavar="DIR", help="write everything here, do not print it"),
    ] = None,
    storage: Annotated[
        str | None,
        typer.Option("-s", "--storage", metavar="ID", help="fetch one stored entry instead"),
    ] = None,
    key_file: KeyFile = None,
) -> None:
    """Fetch the answer, the notebook, and the files the run wrote."""
    _spend(key_file, lambda client: tasks.fetch(client, task_id=task_id, out=out, storage=storage))


@task_app.command("cancel")
def task_cancel(task_id: TaskId, key_file: KeyFile = None) -> None:
    """Stop a run that has not finished. It is still charging while anyone deliberates."""
    _spend(key_file, lambda client: tasks.cancel(client, task_id=task_id))


# ---------------------------------------------------------------- data


@data_app.command("upload")
def data_upload(
    path: Annotated[str, typer.Argument(metavar="PATH", help="the file or directory to upload")],
    name: Annotated[
        str | None, typer.Option("--name", help="what to call it; a directory defaults to its own")
    ] = None,
    description: Annotated[
        str | None, typer.Option("--description", help="what it holds, and what the columns mean")
    ] = None,
    ignore: Annotated[
        list[str] | None,
        typer.Option("--ignore", metavar="PATTERN", help="skip these; repeat for several"),
    ] = None,
    collection: Annotated[
        bool | None,
        typer.Option(
            "--collection/--no-collection",
            help="force the collection shape; the default is one for a directory and not for a file",
        ),
    ] = None,
    key_file: KeyFile = None,
) -> None:
    """Upload a file or a directory and print its data_entry: URI.

    The URI it prints is what `task submit --data` takes; a task never takes a local path.
    """

    def precheck() -> None:
        if not Path(path).exists():
            raise Refusal(f"no file or directory at '{path}' — nothing was uploaded")

    _spend(
        key_file,
        lambda client: datasets.upload(
            client,
            path=path,
            name=name,
            description=description,
            ignore=list(ignore or []),
            collection=collection,
        ),
        precheck,
    )


@data_app.command("search")
def data_search(
    text: Annotated[str, typer.Option("--text", metavar="QUERY", help="what to look for")],
    limit: Annotated[int, typer.Option("-n", "--limit")] = 10,
    key_file: KeyFile = None,
) -> None:
    """Find an entry before uploading a second copy of it."""
    _spend(key_file, lambda client: datasets.search(client, text=text, limit=limit))


def main() -> None:
    """Run the command line. This is the entry point `[project.scripts]` names.

    `prog_name` is pinned because there are three ways in — the console script, `bin/edison-cli`
    on PATH, and `python -m edison_cli`, which is what that wrapper execs — and click would
    otherwise print the third one's spelling into every usage line and every `--help`. The name
    a reader is told to type must not depend on which door the process came through.
    """
    app(prog_name="edison-cli")
