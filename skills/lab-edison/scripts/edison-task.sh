#!/usr/bin/env bash
# The Edison spend path, as one command: submit a task, poll it, find one whose id you lost,
# cancel one, fetch what it produced. It exists because the ordering that keeps a paid run
# reachable used to be a rule an agent re-read across two reference pages and retyped at every
# submission — and a real session lost a task id that way. Here it is structure.
# See docs/adr/0010-edison-skill-runs-through-a-script.md.
#
# The properties this file holds, none of them optional:
#
#   * SUBMISSION TAKES A FILE. `--query-file`, never an inline string, so the artefact the
#     user confirmed is the artefact that goes out. Absent or empty is refused, exit 2, and
#     nothing is spent.
#   * THE TASK ID IS THE FIRST LINE OF STDOUT. Stdout carries data, stderr carries narration,
#     so the receipt for the credit leads the output and no verdict line can push it down.
#   * IT RETURNS AT ONCE. Submission makes one call, `create_task`. The client's blocking
#     wait helper — `references/tasks.md` names it and gives its default timeout — is never
#     called from here, and neither is anything else that waits for a run to end.
#   * IT RUNS THE PREFLIGHT ITSELF before any subcommand that touches the network, and relays
#     the preflight's own remedy on failure. A skipped step 0 refuses instead of spending.
#   * THE KEY REACHES THE CLIENT THROUGH THE ENVIRONMENT AND BY NO OTHER ROUTE. It is sourced
#     from the key file into this shell and inherited by the client process. Never an
#     argument, never on a command line, never echoed, never written into the Python below.
#
# The constants describing the key file — the variable name the client reads, and where the
# file lives — are READ FROM THE PREFLIGHT (`--constants`), which owns them. Nothing here
# restates one, so moving the key file is still a one-line edit in one file.
#
# Exit: 0 fine, 1 refused (preflight, or the client failed), 2 usage.

set -u

# These two come first, above the assignments they read, and moving them below any of it
# turns the shell linter's use-before-definition rule red on every call site in the file.
# It wants a definition, then a command substitution, then the calls; the order below is the
# one arrangement of these six lines that gives it that.
die() { echo "$me: $1" >&2; exit "${2:-2}"; }
need() { [ "$1" -gt 0 ] || die "$2 needs a value"; }

here=$(cd "$(dirname "$0")" && pwd)
preflight="$here/check-edison-config.sh"
me=$(basename "$0")

# The JobNames members this command will send, and the only ones. `references/jobs.md` owns
# which question routes to which — that table is not repeated here. This list is the API
# surface, and its narrowness is the point: the client sends any string it is handed, so an
# allow-list is what turns "never guess a job-name string" into something that cannot be
# guessed past. PHOENIX is absent on purpose; new submissions to it 404.
JOBS="LITERATURE LITERATURE_HIGH PRECEDENT MOLECULES ANALYSIS DUMMY"

usage() {
  cat <<EOF
usage: $me <subcommand> [options]

  submit  --job <JOB> --query-file <path> [--data <data_entry:uri>]...
          [--continue <task-id>] [--project <project-id>]
          Create one task from the query FILE and print its id first. Returns at once.
  status  <task-id>
          One poll: the task's status, and whether that status is terminal.
  list    [--limit <n>] [--project <project-id>]
          Your own tasks, newest first. Costs nothing — the way back to an id you lost.
  cancel  <task-id>
          Stop a run that has not finished. It is still charging while anyone deliberates.
  fetch   <task-id> [--out <dir>] [--storage <id>]
          What the run produced: the answer, the notebook, and the files it wrote.

options
  -j, --job <JOB>          one of: $JOBS
  -q, --query-file <path>  the file holding the exact query the user confirmed
  -d, --data <uri>         a data_entry: URI to attach; repeat for several
  -c, --continue <id>      ride on a previous run instead of paying for its context again
  -p, --project <id>       the project a run belongs to
  -n, --limit <n>          how many tasks to list
  -o, --out <dir>          keep fetched files here instead of a temporary directory
  -s, --storage <id>       fetch one stored entry rather than the task's answer
  -f, --key-file <path>    read the key from this file instead of the configured one
  -h, --help               this text

The query is a file and never a string: what the user confirmed is what is submitted.
references/jobs.md says which question routes to which JOB; references/tasks.md covers
polling, recovery and cancelling.
EOF
}

# ---------------------------------------------------------------- arguments

[ $# -gt 0 ] || { usage >&2; exit 2; }
case "$1" in
  -h|--help) usage; exit 0 ;;
  submit|status|list|cancel|fetch) sub="$1"; shift ;;
  *) usage >&2; die "unknown subcommand: $1" ;;
esac

job=""; query_file=""; task_id=""; limit=""; project=""; cont=""
out=""; storage=""; key_file=""; data=""
nl=$'\n'

while [ $# -gt 0 ]; do
  case "$1" in
    -j|--job)        shift; need $# --job;        job="$1" ;;
    -q|--query-file) shift; need $# --query-file; query_file="$1" ;;
    -d|--data)       shift; need $# --data;       data="${data:+$data$nl}$1" ;;
    -c|--continue)   shift; need $# --continue;   cont="$1" ;;
    -p|--project)    shift; need $# --project;    project="$1" ;;
    -n|--limit)      shift; need $# --limit;      limit="$1" ;;
    -o|--out)        shift; need $# --out;        out="$1" ;;
    -s|--storage)    shift; need $# --storage;    storage="$1" ;;
    -f|--key-file)   shift; need $# --key-file;   key_file="$1" ;;
    -h|--help)       usage; exit 0 ;;
    -*)              usage >&2; die "unknown option: $1" ;;
    *)  [ -z "$task_id" ] || die "only one task id, got '$task_id' and '$1'"
        task_id="$1" ;;
  esac
  shift
done

# Folded to the member spelling here rather than inside the branch that uses it: shellcheck
# loses track of a function definition across a command substitution nested in a `case`, and
# then reports every `die` in the block as undefined.
[ -z "$job" ] || job=$(printf '%s' "$job" | tr '[:lower:]' '[:upper:]')

# Argument checks come BEFORE the preflight on purpose. Both refuse and neither spends, but
# this way a refusal for a missing query file says so on any machine — including one where
# the key IS configured, which is every machine a maintainer runs the gate on.
case "$sub" in
  submit)
    [ -n "$job" ] || die "submit needs --job (one of: $JOBS)"
    case " $JOBS " in
      *" $job "*) ;;
      *) die "unknown job '$job'. Route from references/jobs.md; never invent a name. One of: $JOBS" ;;
    esac
    [ -n "$query_file" ] || die "submit needs --query-file: write the query the user confirmed to a file and pass it"
    [ -f "$query_file" ] || die "no query file at '$query_file' — nothing was submitted"
    [ -s "$query_file" ] || die "the query file '$query_file' is empty — nothing was submitted"
    [ -z "$task_id" ] || die "submit takes no task id (got '$task_id')"
    ;;
  status|cancel|fetch)
    [ -n "$task_id" ] || die "$sub needs a task id"
    ;;
  list)
    [ -z "$task_id" ] || die "list takes no task id (got '$task_id'); use --project to narrow it"
    ;;
esac
[ -z "$out" ] || mkdir -p "$out" || die "cannot make the output directory '$out'" 1

# ---------------------------------------------------------------- the preflight, then the key

# `--constants` reads no key file and touches no environment variable. With `-f` it reports
# the file THAT invocation would check, so the same flag moves both the check and the source.
# The `-f` branch is inside this function rather than around the two calls below because the
# shell linter loses track of a function definition across a command substitution nested in
# a conditional, and then reports every `die` above as undefined.
run_preflight() { # <extra preflight args...>
  if [ -n "$key_file" ]; then bash "$preflight" -f "$key_file" "$@"; else bash "$preflight" "$@"; fi
}

consts=$(run_preflight --constants) || die "the preflight could not print its constants" 1
pf_out=$(run_preflight 2>&1)
pf_rc=$?

if [ "$pf_rc" -ne 0 ]; then
  printf '%s\n' "$pf_out" >&2
  echo >&2
  echo "$me: refusing '$sub' — this machine is not configured for the Edison platform. The fix is above; the user pastes the key into the file themselves." >&2
  exit 1
fi

const() { printf '%s\n' "$consts" | sed -n "s/^$1=//p"; }
key_var=$(const VAR)
key_path=$(const KEYFILE)
[ -n "$key_var" ] && [ -n "$key_path" ] || die "the preflight named no key variable or file" 1
# The preflight collapses $HOME to a tilde, because an absolute home directory carries a
# username. Put it back to reach the file. Matched against a variable rather than a quoted
# "~/", which shellcheck reads as a tilde that failed to expand — here it is a literal to
# match, which is the whole point.
tilde='~'
case "$key_path" in "$tilde"/*) key_path="$HOME/${key_path#"$tilde"/}" ;; esac

# Sourced, never read and re-emitted: the value goes from the file into this shell's
# environment and is inherited by the client. It is never assigned to anything this script
# prints, and no branch below echoes it.
if [ -f "$key_path" ]; then
  # shellcheck disable=SC1090  # the path comes from the preflight at run time, not from here
  . "$key_path"
fi
[ -n "${!key_var:-}" ] || die "the preflight passed but \$$key_var is empty in this shell — re-run $preflight" 1
# shellcheck disable=SC2163  # exporting BY NAME is the point: the name comes from the preflight
export "$key_var"

command -v uv >/dev/null 2>&1 || die "uv is not on PATH, and the client runs ephemerally under it (references/jobs.md)" 1

# ---------------------------------------------------------------- run

# Everything the Python needs travels in the environment, so no query text and no id lands on
# a command line, and the heredoc stays quoted — nothing in it is expanded by this shell.
export EDT_SUB="$sub" EDT_JOB="$job" EDT_QUERY_FILE="$query_file" EDT_DATA="$data"
export EDT_CONTINUE="$cont" EDT_PROJECT="$project" EDT_TASK_ID="$task_id"
export EDT_LIMIT="$limit" EDT_OUT="$out" EDT_STORAGE="$storage"

if [ "$sub" = submit ]; then
  # On stderr, so stdout still opens with the task id. This is the audit trail: the job and
  # the exact text that went out, in the transcript, beside the id it produced.
  echo "$me: submitting $job with the query in $query_file:" >&2
  sed 's/^/  | /' "$query_file" >&2
  if [ -n "$data" ]; then
    echo "$me: attaching:" >&2
    printf '%s\n' "$data" | sed 's/^/  | /' >&2
  fi
fi

# `--no-project` and `--python 3.12` are both load-bearing; references/jobs.md says why.
uv run --no-project --python 3.12 --with edison-client python - <<'PY'
"""Drive edison-client for one subcommand. The key is already in the environment."""

import json
import os
import shutil
from pathlib import Path

from edison_client import EdisonClient
from edison_client.models.app import JobNames, RuntimeConfig, TaskRequest
from edison_client.models.rest import ExecutionStatus


def opt(name):
    return os.environ.get(name, "")


sub = opt("EDT_SUB")
out = opt("EDT_OUT")

# Constructing the client is already a network call: it authenticates and fetches your
# organisations, so a bad key fails here rather than at submission.
client = EdisonClient()


def keep(path):
    """Copy a fetched path out of the library's temporary directory when --out was given."""
    path = Path(path)
    if not out:
        print("FETCHED:", path, "(temporary — pass --out <dir> to keep it)")
        return
    dest = Path(out) / path.name
    if path.is_dir():
        shutil.copytree(path, dest, dirs_exist_ok=True)
    else:
        shutil.copy2(path, dest)
    print("FETCHED:", dest)


if sub == "submit":
    fields = {
        "name": JobNames[opt("EDT_JOB")],
        "query": Path(opt("EDT_QUERY_FILE")).read_text(),
    }
    if opt("EDT_CONTINUE"):
        # The field is `continued_job_id`; the vendor's README calls it something else and
        # TaskRequest rejects unknown fields outright. references/jobs.md.
        fields["runtime_config"] = RuntimeConfig(continued_job_id=opt("EDT_CONTINUE"))
    if opt("EDT_PROJECT"):
        fields["project_id"] = opt("EDT_PROJECT")
    uris = [u for u in opt("EDT_DATA").split("\n") if u]
    extra = {"files": uris} if uris else {}
    task_id = client.create_task(TaskRequest(**fields), **extra)
    # First, flushed, before anything else in this process can block. This line is the
    # receipt for the credit and it outlives every shell.
    print("TASK_ID:", task_id, flush=True)

elif sub == "status":
    task = client.get_task(opt("EDT_TASK_ID"), lite=True)
    print("STATUS:", task.status)
    terminal = ExecutionStatus(task.status).is_terminal_state()
    print("TERMINAL:", "yes" if terminal else "no")

elif sub == "list":
    kwargs = {}
    if opt("EDT_LIMIT"):
        kwargs["limit"] = int(opt("EDT_LIMIT"))
    if opt("EDT_PROJECT"):
        kwargs["project_id"] = opt("EDT_PROJECT")
    # Raw dicts, not models: the job name is under `crow` and the query under `task`.
    for row in client.get_tasks(**kwargs):
        cells = [str(row.get(k, "")) for k in ("created_at", "crow", "status", "id")]
        cells.append(str(row.get("task", ""))[:80].replace("\n", " "))
        print("TASK:", "\t".join(cells))

elif sub == "cancel":
    # False when the task is already terminal, True once a re-fetch shows cancelled.
    print("CANCELLED:", "yes" if client.cancel_task(opt("EDT_TASK_ID")) else "no")

elif sub == "fetch":
    if opt("EDT_STORAGE"):
        # The bare id, so a data_entry: prefix comes off first.
        got = client.fetch_data_from_storage(opt("EDT_STORAGE").removeprefix("data_entry:"))
        if got is None:
            print("STORAGE: the entry holds nothing")
        elif isinstance(got, list):
            for one in got:
                keep(one)
        elif isinstance(got, (str, Path)):
            keep(got)
        else:
            content = getattr(got, "content", None)
            if content is None:
                print("STORAGE:", got)
            elif out:
                dest = Path(out) / f"{opt('EDT_STORAGE')}.txt"
                dest.write_text(str(content))
                print("FETCHED:", dest)
            else:
                print("CONTENT:")
                print(content)
    else:
        task_id = opt("EDT_TASK_ID")
        task = client.get_task(task_id)
        # A task can reach success carrying no answer, so this is the honest check. Whether
        # it is a property or a method is not recorded, and a bound method is truthy — which
        # would report every run as answered — so call it when it is callable.
        answered = getattr(task, "has_successful_answer", None)
        if callable(answered):
            answered = answered()
        print("HAS_ANSWER:", "yes" if answered else "no")
        # formatted_answer exists on a literature-shaped response and not on an analysis one,
        # where reaching for it raises on a run that succeeded.
        answer = getattr(task, "formatted_answer", None) or getattr(task, "answer", None)
        if answer:
            print("ANSWER:")
            print(answer)
        notebook = getattr(task, "notebook", None)
        if notebook and out:
            dest = Path(out) / f"{task_id}.ipynb"
            dest.write_text(json.dumps(notebook))
            print("NOTEBOOK:", dest)
        elif notebook:
            print("NOTEBOOK: present — pass --out <dir> to write it as .ipynb")
        # list_files returns a dict with one key, `data`, holding provenance records. Which
        # field of a record carries the storage id is NOT recorded in references/datasets.md,
        # so the record is printed whole rather than guessed at: read the id out of it and
        # pass it back as --storage.
        for record in client.list_files(task_id)["data"]:
            print("FILE:", json.dumps(record, default=str))
        print("(no FILE lines means the run wrote nothing worth keeping)")

else:
    raise SystemExit(f"unreachable subcommand: {sub}")
PY
