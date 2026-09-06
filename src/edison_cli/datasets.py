"""Datasets: put data on the platform and find it again.

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
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from edison_cli.runtime import Refusal, note, say, without_account

if TYPE_CHECKING:  # pragma: no cover - typing only
    from edison_client import EdisonClient

PREFIX = "data_entry:"


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
        say(f"DATA_URI: {PREFIX}{response.data_storage.id}")
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
    uri = str(client.upload_file(where, name=name, description=description))
    # The two calls disagree about whether the prefix is included. Normalising it here is
    # what stops the caller guessing.
    say(f"DATA_URI: {uri if uri.startswith(PREFIX) else PREFIX + uri}")
    say("SHAPE: file")
    return 0


def search(client: EdisonClient, *, text: str, limit: int) -> int:
    """Search the account's data entries by text. Free, and the way to avoid a second upload.

    Two entries of the same dataset under the same name cannot be told apart afterwards, so
    this is worth running before every upload.
    """
    rows = client.search_data_storage(text_query=text, limit=limit)
    for row in rows:
        public = without_account(row)
        cells = [
            f"{PREFIX}{public.get('id', '')}",
            str(public.get("name", "")),
            str(public.get("created_at", "")),
            str(public.get("description", ""))[:60].replace("\n", " "),
        ]
        say("ENTRY: " + "\t".join(cells))
    if not rows:
        say(f"(nothing on this account matches '{text}')")
    return 0
