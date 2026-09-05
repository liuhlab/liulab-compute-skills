"""A fake Edison platform, and a harness that drives `edison-cli` against it.

**No test in this suite may be able to reach the real client.** A Kosmos run is billed as
the fan-out of tasks it dispatches — the first one ever made bought 33 tasks in 18 minutes
and was still growing when it was stopped — so a test that could touch the platform on the
day the spend path is broken is not a test, it is an invoice.

The seam is a package called `edison_client` written into the test's own temporary directory
and put first on `PYTHONPATH`, where it shadows the installed one. It records what the CLI
did — every argument, whether the key variable arrived non-empty, every call in order — and
answers with canned ids. `_harness` proves the shadowing worked before any test runs, so a
`PYTHONPATH` that failed to take effect is a red test rather than a live call.

It records **whether** the key arrived, never the key. That distinction is the whole point
of the leak assertions in `test_key_discipline.py`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src"
sys.path.insert(0, str(SRC))

from edison_cli import preflight  # noqa: E402 - after sys.path, so the tree is read, not a copy

# 22 characters of nothing, at a shape no real key has. It stands in for a key in every test
# below and must appear in no argument, no output and no file under `src/`.
FIXTURE_KEY = "fixture-stands-in-for-a-key-and-must-never-leak"

PERSONA_ID = "11111111-1111-4111-8111-111111111111"
PROJECT_ID = "22222222-2222-4222-8222-222222222222"
SESSION_ID = "33333333-3333-4333-8333-333333333333"
TASK_ID = "44444444-4444-4444-8444-444444444444"
LIVE_TASK_IDS = ("55555555-5555-4555-8555-555555555551", "55555555-5555-4555-8555-555555555552")
JOB_NAME = "job-futurehouse-data-analysis-aries"
ACCOUNT = "an-account-identifier-no-command-may-print"
# A second row wearing the same name, for the duplicate-name refusals.
OTHER_ID = "77777777-7777-4777-8777-777777777777"

_STUB_ROOT = '''
"""A fake edison_client. Records what the caller did; never opens a socket."""

import json
import os
import sys
from pathlib import Path

LOG = Path(os.environ["EDISON_STUB_LOG"])
KEY_VAR = os.environ["EDISON_STUB_KEY_VAR"]

PERSONA_ID = "{persona}"
PROJECT_ID = "{project}"
SESSION_ID = "{session}"
TASK_ID = "{task}"
LIVE_TASK_IDS = {live!r}
JOB_NAME = "{job}"
ACCOUNT = "{account}"
OTHER_ID = "{other}"


def record(event, **fields):
    """Append one line describing a call. Order is the whole point of the file."""
    with LOG.open("a", encoding="utf-8") as handle:
        print(json.dumps(dict(event=event, **fields), default=str), file=handle)


class _Response:
    def __init__(self, payload, status_code=200):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class _Raw:
    def get(self, path, params=None):
        record("http_get", path=path, params=params)
        if path == "/v0.1/personas":
            rows = [
                {{
                    "id": PERSONA_ID,
                    "name": "Kosmos",
                    "enabled": True,
                    "persona_scope": "personal",
                    "user_id": ACCOUNT,
                    "metadata": {{"persona_job_name": JOB_NAME}},
                }}
            ]
            if os.environ.get("EDISON_STUB_DUPLICATES") == "personas":
                rows.append(dict(rows[0], id=OTHER_ID))
            return _Response(rows)
        return _Response([])


class _Dumpable:
    def __init__(self, payload):
        self._payload = payload

    def model_dump(self):
        return dict(self._payload)


class _Conversations:
    def __init__(self, rows):
        self.conversations = [_Dumpable(row) for row in rows]


class _Task:
    status = "success"
    formatted_answer = "the answer, as the platform formatted it"
    notebook = {{"cells": []}}

    def has_successful_answer(self):
        return True


class _Entry:
    id = "66666666-6666-4666-8666-666666666666"


class _Stored:
    data_storage = _Entry()


class EdisonClient:
    def __init__(self, *args, **kwargs):
        record(
            "construct",
            argv=sys.argv,
            key_arrived=bool(os.environ.get(KEY_VAR)),
            args=[str(item) for item in args],
            kwargs={{key: str(value) for key, value in kwargs.items()}},
        )

    @property
    def client(self):
        return _Raw()

    # ---- one-shot tasks
    def create_task(self, task_data, files=None):
        record("create_task", task=str(task_data), files=files)
        return TASK_ID

    def get_task(self, task_id=None, history=False, verbose=False, lite=False):
        record("get_task", task_id=task_id, lite=lite)
        return _Task()

    def get_tasks(self, query_params=None, **kwargs):
        record("get_tasks", kwargs=kwargs)
        return [
            {{"id": LIVE_TASK_IDS[0], "crow": JOB_NAME, "status": "in progress",
              "created_at": "2026-09-05T21:42:00Z", "task": "one", "user_id": ACCOUNT,
              "project_name": "a project"}},
            {{"id": LIVE_TASK_IDS[1], "crow": JOB_NAME, "status": "queued",
              "created_at": "2026-09-05T21:43:00Z", "task": "two", "user_id": ACCOUNT}},
            {{"id": TASK_ID, "crow": JOB_NAME, "status": "success",
              "created_at": "2026-09-05T21:43:00Z", "task": "three", "user_id": ACCOUNT}},
        ]

    def cancel_task(self, task_id=None):
        record("cancel_task", task_id=task_id)
        return True

    def list_files(self, trajectory_id):
        record("list_files", trajectory_id=trajectory_id)
        return {{"data": [{{"id": "a-storage-id", "name": "counts.csv", "user_id": ACCOUNT}}]}}

    def fetch_data_from_storage(self, data_storage_id=None):
        record("fetch_data_from_storage", data_storage_id=data_storage_id)
        return None

    # ---- projects
    def create_project(self, name, description=None, persona_id=None, **kwargs):
        record("create_project", name=name, persona_id=persona_id, description=description)
        return PROJECT_ID

    def list_persona_owned_projects(self, persona_id, **kwargs):
        record("list_persona_owned_projects", persona_id=persona_id)
        rows = [{{"id": PROJECT_ID, "name": "a project", "created_at": "2026-09-05T21:40:00Z"}}]
        if os.environ.get("EDISON_STUB_DUPLICATES") == "projects":
            rows.append(dict(rows[0], id=OTHER_ID))
        return rows

    def delete_project(self, project_id, delete_trajectories=True):
        record("delete_project", project_id=project_id, delete_trajectories=delete_trajectories)

    def add_task_to_project(self, project_id, trajectory_id):
        record("add_task_to_project", project_id=project_id, trajectory_id=trajectory_id)

    # ---- chat
    def send_chat_message(self, project_id, message, **kwargs):
        record("send_chat_message", project_id=project_id, kwargs=kwargs, chars=len(message))
        return _Dumpable({{"session_id": SESSION_ID, "status": "dispatched"}})

    def queue_chat_message(self, session_id, project_id, message):
        record("queue_chat_message", session_id=session_id, project_id=project_id)
        return _Dumpable({{"id": "a-queued-message-id", "target_id": SESSION_ID}})

    def get_conversation(self, session_id, limit=50, offset=0):
        record("get_conversation", session_id=session_id)
        call = {{"function": {{"name": "send_message",
                             "arguments": json.dumps({{"display_text": "what the run said"}})}}}}
        return _Dumpable({{"messages": [{{"role": "assistant", "content": "", "tool_calls": [call]}}]}})

    def get_session(self, session_id):
        record("get_session", session_id=session_id)
        return [_Dumpable({{"id": SESSION_ID, "type": "project", "type_id": PROJECT_ID,
                           "job_name": JOB_NAME}})]

    def get_conversations(self, session_id=None, limit=25, offset=0):
        record("get_conversations", limit=limit)
        return _Conversations([{{"session_id": SESSION_ID, "created_at": "2026-09-05T21:40:35Z"}}])

    # ---- data storage
    def upload_file(self, file_path, name=None, description=None, **kwargs):
        record("upload_file", file_path=str(file_path), name=name)
        return "data_entry:66666666-6666-4666-8666-666666666666"

    def store_file_content(self, name, file_path, **kwargs):
        record("store_file_content", name=name, file_path=str(file_path), kwargs=kwargs)
        return _Stored()

    def search_data_storage(self, text_query=None, limit=10, **kwargs):
        record("search_data_storage", text_query=text_query, limit=limit)
        return [{{"id": "66666666-6666-4666-8666-666666666666", "name": "counts.csv",
                 "created_at": "2026-09-05", "description": "counts", "user_id": ACCOUNT}}]
'''

_STUB_APP = '''
"""The models the one-shot path builds a request out of."""

from enum import Enum


class JobNames(Enum):
    LITERATURE = "job-futurehouse-paperqa3"
    LITERATURE_HIGH = "job-futurehouse-paperqa3-high"
    ANALYSIS = "job-futurehouse-data-analysis-crow-high"
    MOLECULES = "job-futurehouse-data-analysis-molecules"
    PRECEDENT = "job-futurehouse-paperqa3-precedent"
    DUMMY = "job-futurehouse-dummy-env"
    PHOENIX = "job-futurehouse-phoenix"


class RuntimeConfig:
    def __init__(self, **fields):
        self.fields = fields

    def __repr__(self):
        return f"RuntimeConfig({self.fields})"


class TaskRequest:
    def __init__(self, **fields):
        self.fields = fields

    def __repr__(self):
        return f"TaskRequest({self.fields})"
'''

_STUB_REST = '''
"""The execution states, and which of them mean the task can no longer spend."""

from enum import Enum

TERMINAL = {"fail", "success", "cancelled", "truncated"}


class ExecutionStatus(Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in progress"
    FAIL = "fail"
    SUCCESS = "success"
    CANCELLED = "cancelled"
    TRUNCATED = "truncated"

    def is_terminal_state(self):
        return self.value in TERMINAL
'''


@dataclass
class Run:
    """One `edison-cli` invocation: what it printed, what it returned, and what it called."""

    returncode: int
    stdout: str
    stderr: str
    events: list[dict[str, Any]]
    log: str

    @property
    def first_line(self) -> str:
        """The first line of stdout, which on anything that spends is the receipt."""
        return self.stdout.splitlines()[0] if self.stdout.splitlines() else ""

    def called(self, event: str) -> list[dict[str, Any]]:
        """Every recorded call of one name, in the order the CLI made them."""
        return [item for item in self.events if item.get("event") == event]

    def order_of(self, event: str) -> int:
        """Where a call first appears in the recording, or -1 if it never happened."""
        for index, item in enumerate(self.events):
            if item.get("event") == event:
                return index
        return -1


class Harness:
    """A temporary machine: a key file, a fake platform, and a way to run the command."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.log = workspace / "calls.jsonl"
        self.stub = workspace / "stub"
        package = self.stub / "edison_client"
        (package / "models").mkdir(parents=True)
        (package / "__init__.py").write_text(
            _STUB_ROOT.format(
                persona=PERSONA_ID,
                project=PROJECT_ID,
                session=SESSION_ID,
                task=TASK_ID,
                live=LIVE_TASK_IDS,
                job=JOB_NAME,
                account=ACCOUNT,
                other=OTHER_ID,
            ),
            encoding="utf-8",
        )
        (package / "models" / "__init__.py").write_text("", encoding="utf-8")
        (package / "models" / "app.py").write_text(_STUB_APP, encoding="utf-8")
        (package / "models" / "rest.py").write_text(_STUB_REST, encoding="utf-8")

        self.key_file = workspace / "key.env"
        self.key_file.write_text(f"export {preflight.VAR}={FIXTURE_KEY}\n", encoding="utf-8")
        self.key_file.chmod(0o600)
        self.absent_key = workspace / "absent.env"
        # The name cache belongs to the test, never to the machine running it.
        self.cache = workspace / "names.json"

        self.env = dict(os.environ)
        self.env["PYTHONPATH"] = os.pathsep.join(
            [str(self.stub), str(SRC), self.env.get("PYTHONPATH", "")]
        ).rstrip(os.pathsep)
        self.env["PYTHONDONTWRITEBYTECODE"] = "1"
        self.env["EDISON_STUB_LOG"] = str(self.log)
        self.env["EDISON_STUB_KEY_VAR"] = preflight.VAR
        self.env["EDISON_CLI_CACHE"] = str(self.cache)
        # A maintainer's own exported key must not reach the child, or `key_arrived` would be
        # true for a reason that has nothing to do with the code under test.
        self.env.pop(preflight.VAR, None)

    def shadowing_works(self) -> str:
        """Report which `edison_client` a subprocess would import. It must be the fake one."""
        probe = subprocess.run(
            [sys.executable, "-c", "import edison_client; print(edison_client.__file__)"],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        return probe.stdout.strip()

    def write(self, name: str, text: str) -> str:
        """Put a file in the workspace and hand back its path, ready to be an argument."""
        path = self.workspace / name
        path.write_text(text, encoding="utf-8")
        return str(path)

    def run(self, *argv: str) -> Run:
        """Run `edison-cli` with the fake platform in place and collect everything it did.

        `events` holds only what THIS invocation recorded — the log file is appended to, and a
        test that runs the command twice has to be able to tell the two apart.
        """
        before = len(self.log.read_text(encoding="utf-8").splitlines()) if self.log.exists() else 0
        done = subprocess.run(
            [sys.executable, "-m", "edison_cli", *argv],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
            cwd=self.workspace,
        )
        log = self.log.read_text(encoding="utf-8") if self.log.exists() else ""
        mine = log.splitlines()[before:]
        events = [json.loads(line) for line in mine if line.strip()]
        return Run(done.returncode, done.stdout, done.stderr, events, log)


@pytest.fixture
def edison(tmp_path: Path) -> Harness:
    """Build a harness whose fake platform is proven to shadow the real client before any test."""
    harness = Harness(tmp_path)
    resolved = harness.shadowing_works()
    assert resolved.startswith(str(harness.stub)), (
        "the fake edison_client is not shadowing the installed one, so a test could reach "
        f"the real platform. A subprocess resolved the import to: {resolved!r}"
    )
    return harness
