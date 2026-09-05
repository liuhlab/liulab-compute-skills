# Datasets: upload, submit, poll, fetch

Companion to `SKILL.md`'s "Analysing a dataset". Everything here was read off the installed
`edison-client` 0.16.1 on 2026-09-05 — re-read it the same way when this is next touched. The
ephemeral `uv` invocation, the `JobNames` table and the cost note live in `jobs.md` and are not
repeated here.

## Upload

A task never takes a local path. It takes a **data-entry URI** — `data_entry:<uuid>` — which an
upload hands back, so the upload comes first.

```python
uri = client.upload_file("/path/to/counts.csv")  # -> "data_entry:<uuid>"
```

**A directory has two shapes, and only one of them is a collection.** `upload_file` on a
directory takes the hierarchical route: one entry per file and per subdirectory, each hanging off
a parent entry, `is_collection` false on all of them, and the URI you get back is the parent's. A
directory should go up as the other shape instead — one zip, one entry, one URI:

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

## Submit

```python
task = TaskRequest(name=JobNames.ANALYSIS, query="<the exact query you showed the user>")
task_id = client.create_task(task, files=[uri])  # returns the trajectory id
```

`files` takes URIs, never paths, and several of them attach several datasets. The client writes
them into `runtime_config.environment_config["data_storage_uris"]`, so set that key **or** pass
`files` — both at once raises `ValueError`.

## Poll

`create_task` returns as soon as the task exists, so the id outlives the shell that made it.
Poll it cheaply:

```python
from edison_client.models.rest import ExecutionStatus

t = client.get_task(task_id, lite=True)  # task_id, query and status only
done = ExecutionStatus(t.status).is_terminal_state()
```

The statuses are `queued`, `in progress`, `fail`, `success`, `cancelled` and `truncated`; the
last four are terminal. Sleep between polls, and tell the user it is running.

`run_tasks_until_done(task, files=[uri])` runs that loop for you, but it blocks and gives up at
`timeout` — 2400 seconds by default — returning whatever state it has reached. Analysis is the
long shape, so prefer `create_task` with your own poll, and keep the id either way.

## Fetch the results

`get_task` picks the response class from the job name, and an analysis run is **not** the
literature shape:

```python
resp = client.get_task(task_id)  # FinchTaskResponse for ANALYSIS
resp.answer  # the written answer
resp.notebook  # dict with `cells` and `metadata` — write it out as .ipynb
```

`formatted_answer` belongs to the literature and molecules jobs; reaching for it here raises
`AttributeError` on a run that succeeded.

Files the run produced are listed by provenance, then fetched one at a time:

```python
entries = client.list_files(task_id)  # provenance entries, each with data_storage
path = client.fetch_data_from_storage("<uuid>")  # STRIP the "data_entry:" prefix first
```

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
`skills/lab-hpc/references/arc-hpc.md` covers that and the transfer hosts;
`skills/lab-hpc/references/ircbc-hpc.md` covers why ircbc cannot reach the platform. Neither
fact is repeated here.

## Preparing the data

Better input beats a bigger job, and `kosmos.md`'s dataset section is the vendor's guidance for
both: processed rather than raw, every column intuitively labelled or described in a sheet of its
own, and a size the platform will take. Put what the columns mean in the `description`: it
travels with the entry, so the next person to find it does not have to guess.
