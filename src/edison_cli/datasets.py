"""Datasets: put data on the platform, find it again, and bring it back down.

A task never takes a local path. It takes a data-entry URI — `data_entry:<uuid>` — so an
upload comes first and `task submit --data <uri>` comes second.

The platform has two upload calls and they are not interchangeable. `upload_file` on a
directory takes the hierarchical route: one entry per file and per subdirectory, none of them
a collection, and the URI you get back is the parent's. `store_file_content(as_collection=
True)` zips the tree into a single entry that comes back whole, which is what a dataset
wants. Choosing between them by hand is a trap, so this command chooses by default: a
directory goes up as a collection and a file goes up as itself. `--collection` and
`--no-collection` are how someone who wants the other shape says so.

`store_file_content` also returns the entry rather than the URI, so the URI used to be
something every caller built for itself. It is built here now, once, and printed first.

`get` is the way back down, and it lives here rather than in `tasks` because an entry is not a
task: a Kosmos run's deliverables are entries no task holds the answer to. `task fetch
--storage` reaches the same function, so the two commands cannot drift apart.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from edison_cli.runtime import Refusal, clipped, note, say, without_account

if TYPE_CHECKING:  # pragma: no cover - typing only
    from edison_client import EdisonClient

PREFIX = "data_entry:"


def uri(value: object) -> str:
    """Spell one data-entry id the way every command prints it, prefix and all.

    Three surfaces disagree about the prefix: `upload_file` returns it, `store_file_content`
    returns a bare id, and the chat surface stores the bare stem of whatever was sent. One
    spelling, made here, is what lets `kosmos start`'s `DATA:` and `kosmos status`'s
    `ATTACHED:` be read against each other by eye.
    """
    text = str(value)
    return text if text.startswith(PREFIX) else PREFIX + text


def upload(
    client: EdisonClient,
    *,
    path: str,
    name: str | None,
    description: str | None,
    ignore: list[str],
    collection: bool | None,
) -> int:
    """Upload one file or one directory and print the URI a task can be given.

    `--collection` is a decision, not a default: without it a directory goes up as one
    collection entry and a file goes up as itself, which is what each of them should be.
    Pass it, or `--no-collection`, only when you want the other shape and know why.
    """
    where = Path(path)
    if not where.exists():
        raise Refusal(f"no file or directory at '{path}' — nothing was uploaded")
    as_collection = where.is_dir() if collection is None else collection

    if as_collection:
        note(f"edison-cli: uploading {where} as one collection entry")
        response = client.store_file_content(
            name=name or where.name,
            file_path=where,
            description=description,
            as_collection=True,
            ignore_patterns=list(ignore) or None,
        )
        say(f"DATA_URI: {uri(response.data_storage.id)}")
        say("SHAPE: collection (one zipped entry; it comes back as a directory)")
        return 0

    if ignore:
        raise Refusal("--ignore only means something for a collection upload")
    if where.is_dir():
        note(
            "edison-cli: --no-collection on a directory takes the hierarchical route — one "
            "entry per file, none of them a collection, and the URI is the parent's."
        )
    note(f"edison-cli: uploading {where}")
    # The two calls disagree about whether the prefix is included. `uri` is what stops the
    # caller guessing, and it is the same spelling `kosmos status` reads an attachment back in.
    say(f"DATA_URI: {uri(client.upload_file(where, name=name, description=description))}")
    say("SHAPE: file")
    return 0


def search(client: EdisonClient, *, text: str, limit: int) -> int:
    """Search data entries by text. Free, and the cheapest way to avoid a second upload.

    Two entries of the same dataset under the same name cannot be told apart afterwards, so
    this is worth running before every upload.

    NEITHER HALF OF THE OBVIOUS READING HOLDS, and both used to be asserted here. It is not
    account-scoped: entries this account never created come back, so a hit may be somebody
    else's dataset. And a miss settles nothing — the results are ranked, and the ranking stops
    before the corpus is exhausted, so an entry whose description holds the term verbatim can
    still be absent from forty rows. `references/datasets.md` carries the probes behind both.
    """
    rows = client.search_data_storage(text_query=text, limit=limit)
    for row in rows:
        public = without_account(row)
        cells = [
            f"{PREFIX}{public.get('id', '')}",
            str(public.get("name", "")),
            str(public.get("created_at", "")),
            # The description is searched, not just shown, so a reader has to be able to see
            # that the phrase they matched on may be in the part that was cut.
            clipped(str(public.get("description", "")).replace("\n", " "), 60),
        ]
        say("ENTRY: " + "\t".join(cells))
    if not rows:
        # Not "nothing on this account matches", which claimed a scope the search does not
        # have and a certainty it cannot give. Someone who is told their dataset is not up
        # there uploads a second copy — the one outcome this command exists to prevent.
        say(f"(nothing came back for '{text}' — which is not proof the entry is not there)")
    return 0


def _keep(path: Path, out: str | None) -> None:
    """Copy a fetched path out of the library's temporary directory when `--out` was given."""
    import shutil

    if not out:
        say(f"FETCHED: {path} (temporary — pass --out <dir> to keep it)")
        return
    destination = Path(out) / path.name
    if path.is_dir():
        shutil.copytree(path, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(path, destination)
    say(f"FETCHED: {destination}")


def get(client: EdisonClient, *, storage: str, out: str | None) -> int:
    """Download one data entry by its URI. The only route to what a Kosmos run produced.

    Free, and the other half of `search`: a run publishes its deliverables as entries, and
    until this existed nothing in the `data` group could bring one down. The accident that
    stood in for it — `task fetch <ignored> --storage <uri>`, whose required task id is never
    read — is still there for the one-shot flow that documents it, and calls this.
    """
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
    # The bare id, so a data_entry: prefix comes off first.
    got = client.fetch_data_from_storage(storage.removeprefix(PREFIX))
    if got is None:
        say("STORAGE: the entry holds nothing")
        return 0
    if isinstance(got, list):
        for one in got:
            _keep(one, out)
        return 0
    if isinstance(got, Path):
        _keep(got, out)
        return 0
    content = getattr(got, "content", None)
    if content is None:
        say(f"STORAGE: {got}")
    elif out:
        destination = Path(out) / f"{storage.removeprefix(PREFIX)}.txt"
        destination.write_text(str(content), encoding="utf-8")
        say(f"FETCHED: {destination}")
    else:
        say("CONTENT:")
        say(str(content))
    return 0
