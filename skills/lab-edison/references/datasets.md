# Datasets: upload, attach, fetch what the run made

> **Provenance** — Source: `edison-client` 0.16.1 · Checked: 2026-09-05 · Default tier: read.
> A claim at another tier is tagged `[verified]`, `[read]` or `[unverified]` where it is made.

Companion to `SKILL.md`'s "Analysing a dataset". Re-read the package the same way when this page
is next touched. The `uv` invocation and the routing table are in `jobs.md`; submitting, polling,
recovering and cancelling are in `tasks.md`. Neither is repeated here.

## Upload

A task never takes a local path. It takes a **data-entry URI** — `data_entry:<uuid>` — which an
upload hands back, so the upload comes first.

```python
uri = client.upload_file("/path/to/counts.csv")  # -> "data_entry:<uuid>"
```

Check `search_data_storage(text_query="<name>")` first (`tasks.md`): re-uploading a dataset
that is already there costs time and leaves two entries nobody can tell apart.

**A directory has two shapes, and only one of them is a collection.** `upload_file` on a
directory takes the hierarchical route: one entry per file and per subdirectory, each hanging
off a parent entry, `is_collection` false on all of them, and the URI you get back is the
parent's. A directory should go up as the other shape instead — one zip, one entry, one URI:

```python
resp = client.store_file_content(
    name="<dataset name>",
    file_path="/path/to/dataset-dir",
    description="<what it holds, and what the columns mean>",
    as_collection=True,  # zips the tree into a single collection entry
    ignore_patterns=["*.bam"],  # optional; the directory's own .gitignore is read anyway
)
uri = f"data_entry:{resp.data_storage.id}"
```

`store_file_content` returns the entry, not the URI, so you build the URI yourself — that is the
whole difference between the two return values. A collection also comes back whole:
`fetch_data_from_storage` extracts the zip, so what you fetch later is a directory again.

## Attach it to the task

```bash
bash scripts/edison-task.sh submit --job ANALYSIS --query-file <file> --data data_entry:<uuid>
```

`--data` becomes `create_task(task, files=[uri])`. It takes URIs, never paths, and repeating it
attaches several datasets. The client writes them into
`runtime_config.environment_config["data_storage_uris"]`, so set that key **or** pass the URIs —
both at once raises `ValueError`.

## Fetch what the run produced

```bash
bash scripts/edison-task.sh fetch <task-id> --out <dir>            # answer, notebook, records
bash scripts/edison-task.sh fetch <task-id> --out <dir> --storage <id>   # one entry
```

The answer and the notebook come off the response (`tasks.md`). Files the run *made* are listed
by provenance, then fetched one at a time — `client.list_files(task_id)["data"]`, then
`client.fetch_data_from_storage("<uuid>")`, which takes the bare id, so the command strips a
`data_entry:` prefix for you.

`list_files` returns a dict with one key, `data`, holding the list — reaching for it as a list
is the mistake to avoid, and an empty list means the run wrote nothing worth keeping.

`fetch_data_from_storage` takes the bare id and returns whichever fits: a `Path` to a downloaded
file — a zip arrives already extracted, so a collection lands as a directory — a
`RawFetchResponse` whose `.content` holds text or table content, a `list[Path]` when the entry
has several storage locations, or `None` when it has nothing. **Downloads land in a temporary
directory the library manages**, so copy anything the user wants to keep somewhere real before
reporting it.

## Where the run happens

The client and the key belong to the user's own machine by default, and `SKILL.md` says why. On
arc — the only cluster where this is possible at all, and only with the user's own key file
already there — `uv` lives under the user's home, so any remote command needs a login shell.
`skills/lab-hpc/references/arc-hpc.md` covers that and the transfer hosts, and neither fact is
repeated here.

On ircbc, stage the data down and upload from the user's own machine. The basis for that is
narrower than it looks: `lab-hpc` records nothing about this platform. What it records is that
ircbc's compute nodes have no route to the internet
(`skills/lab-hpc/references/ircbc-hpc.md`), and that the two hosts there that do have one are a
doorway and a data mover, neither of them a place to run work. Earlier text here claimed the
platform cannot be reached from ircbc at all; nothing verifies that.

## Preparing the data

Better input beats a bigger job, and `kosmos.md`'s dataset section is the vendor's guidance for
both: processed rather than raw, every column intuitively labelled or described in a sheet of
its own, and a size the platform will take. Put what the columns mean in the `description`: it
travels with the entry, so the next person to find it does not have to guess.
