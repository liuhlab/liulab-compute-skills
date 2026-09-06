# Datasets: upload, attach, fetch what the run made

> **Provenance** — Source: `edison-client` 0.16.1 and the vendor's Kosmos best-practices guide · Checked: 2026-09-05 · Default tier: read.
> A claim at another tier is tagged `[verified]`, `[read]` or `[unverified]` where it is made.

Companion to `SKILL.md`. Read it whenever a run takes data with the question: `ANALYSIS` needs a
URI, so the upload comes first, then `task submit --data`, then `task fetch`. Re-read the package
the same way when this page is next touched. The environment underneath and the routing table are
in `jobs.md`; submitting, polling, recovering and cancelling are in `tasks.md`. Neither is
repeated here.

## Upload

A task never takes a local path. It takes a **data-entry URI** — `data_entry:<uuid>` — which an
upload hands back, so the upload comes first.

```bash
edison-cli data search --text "<name>"        # is it up already?
edison-cli data upload /path/to/counts.csv    # DATA_URI: data_entry:<uuid>, then SHAPE: file
```

Search first: re-uploading a dataset that is already there costs time and leaves two entries
nobody can tell apart. `search` prints one `ENTRY:` line per match, URI first, ten at a time
unless `-n` says otherwise. The path `upload` takes is a positional argument, not a flag.
`DATA_URI:` is the first line of output and carries the URI `task submit --data` consumes;
`SHAPE:` on the second line says which of the two upload shapes it took.

`[verified]` **`search` matches on descriptions, not only on names.** A query found an entry on
a phrase that appears nowhere but its description. The description column of an `ENTRY:` line
is cut at 60 characters and a cut one ends in `… [+N chars cut]`, so on a marked line the term
you matched on may be in the part that went.

**The shape is chosen for you.** A directory goes up as a collection and a file as a file.
Neither `--collection` nor `--no-collection` is required, and the pair exists only to override
that default:

```bash
edison-cli data upload /path/to/dataset-dir \
  --name "<dataset name>" \
  --description "<what it holds, and what the columns mean>" \
  --ignore '*.bam'
```

A collection is `store_file_content(as_collection=True)`: one zip, one entry, one URI, and it
comes back whole — `fetch_data_from_storage` extracts the zip, so what you fetch later is a
directory again. `--no-collection` on a directory forces the other route instead, `upload_file`
on the tree: one entry per file and per subdirectory, `is_collection` false on all of them, and
the URI you get back is only the parent's. The command says on stderr that it is doing that.

`--ignore PATTERN` repeats, and is **refused unless the upload is a collection** — the
hierarchical route has nothing to apply it to. It is optional even there, because the
directory's own `.gitignore` is read anyway. `upload_file` returns the URI and
`store_file_content` returns the entry, so the command builds the URI from `data_storage.id`
either way and both shapes print the same first line.

## Attach it to the task

```bash
edison-cli task submit --job ANALYSIS --query-file <file> --data data_entry:<uuid>
```

`--data` becomes `create_task(task, files=[uri])`. It takes URIs, never paths, and repeating it
attaches several datasets. The client writes them into
`runtime_config.environment_config["data_storage_uris"]`, so set that key **or** pass the URIs —
both at once raises `ValueError`.

**This section is the one-shot task surface only.** A Kosmos run is a chat session and not a
task, so it takes its data by the route below rather than this one. `kosmos.md`.

## Attach it to a Kosmos run

```bash
edison-cli kosmos start --project ID|NAME --persona ID|NAME \
  --objective-file <file> --data data_entry:<uuid>
```

`[verified]` **`send_chat_message` takes `data_storage_ids`** — a list of bare ids or
`data_entry:` URI stems, carried in the POST body as `info.data_storage_ids`. The client's own
`_normalize_data_storage_id` strips the prefix, so the URI `data upload` printed goes in
unchanged. `queue_chat_message` takes the same argument.

`--data` here is `task submit --data`: the same `-d` short form, URIs and never paths, repeated
once per entry. Nothing checks it on the way out — the platform normalises the spelling and
rejects a bad id itself, and both upload shapes wear the same URI, so a collection attaches
exactly like a file. That is the usual shape for a run: a folder of context, not one table.

`kosmos start` prints one `DATA:` line per entry in its leading block, before the send and
before anything is charged. Nothing in the response says what was attached, so that line is the
only receipt — read it, and if an entry is missing from it the run did not get it.

**`kosmos status` prints one `ATTACHED:` line per entry the platform kept**, read back off the
user turn's `info.data_storage_ids` and spelled the way `DATA:` spelled it, so the two lists
compare by eye: `DATA:` is what was sent, `ATTACHED:` is what the platform bound to the message.
An entry on one and not the other is worth reporting. `ATTACHED:` confirms that record and
nothing further — **not** that any task opened the file. Only the transcript says that.

`[verified]` **A run has been started with one**, on 2026-09-05: the send was accepted, the
`DATA:` line printed in the leading block, and the run dispatched. `[unverified]` **What the run
then does with the entry.** Whether any task opens it is still unread — `ATTACHED:` answers only
whether the platform kept the record.

## Fetch what the run produced

```bash
edison-cli task fetch <task-id> --out <dir>            # answer, notebook, records
edison-cli task fetch <task-id> --out <dir> --storage <id>   # one entry
```

With `--out` the answer is written as `<task-id>.answer.md` rather than printed, and every line
names the file it wrote (`tasks.md`).

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

**The default is the user's own machine.** A run started on a cluster needs a live credential on a
shared node, and the only machine that has to hold one is theirs. Arc is the one cluster where
running from it is possible at all, and only once the user has installed their own key file there
— explain that, never do it for them. There, `pixi` lives under the user's home, so any remote
command needs a login shell. `skills/lab-hpc/references/arc-hpc.md` covers that and the transfer
hosts, and neither fact is repeated here.

On ircbc, stage the data down and upload from the user's own machine. The basis for that is
narrower than it looks: `lab-hpc` records nothing about this platform. What it records is that
ircbc's compute nodes have no route to the internet
(`skills/lab-hpc/references/ircbc-hpc.md`), and that the two hosts there that do have one are a
doorway and a data mover, neither of them a place to run work. Earlier text here claimed the
platform cannot be reached from ircbc at all; nothing verifies that.

## Preparing the data

Better input beats a bigger job, and the guidance is the same whether the data goes to a task or
to a run. Vendor guidance, from
<https://docs.edisonscientific.com/guides/best-practices-for-optimizing-kosmos-workflows>,
fetched 2026-09-05:

- Processed data of good quality, not raw files.
- Every column name intuitively labelled. Where a name cannot carry its own meaning, add a
  sheet describing what each one means.
- It does best on complex, high-dimensional data.
- Under 5GB in total, uncompressed.

Put what the columns mean in the `description` as well: it travels with the entry, so the next
person to find it does not have to guess.
