#!/usr/bin/env python3
"""gen-demo-codebase.py <outdir> — deterministic multi-language demo codebase.

Generates the committed fixture at tests/fixtures/demo-codebase/: a toy
"taskflow" system (Python API server + TypeScript web client + Go worker +
bash ops) whose files genuinely import and call each other, so every ctx
query surface (tree/sig/map/deps/refs/at/notes anchors) has real edges to
resolve. Deterministic output: same script, same bytes — regenerate and
diff instead of hand-editing the fixture.
"""

import sys
from pathlib import Path

HANDLERS = ["tasks", "queues", "workers", "auth", "metrics", "webhooks"]
COMPONENTS = [
    "TaskList",
    "TaskDetail",
    "QueuePicker",
    "WorkerBadge",
    "MetricsPanel",
    "LoginForm",
]


def w(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.lstrip("\n"))


def python_core(root: Path) -> None:
    w(
        root,
        "pyserver/taskflow/__init__.py",
        """
\"\"\"taskflow — toy task-queue API server (demo fixture).\"\"\"

__version__ = "0.3.1"
""",
    )
    w(
        root,
        "pyserver/taskflow/models.py",
        """
\"\"\"Core domain models.\"\"\"

from dataclasses import dataclass, field
from enum import Enum


class TaskState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Task:
    id: str
    queue: str
    payload: dict
    state: TaskState = TaskState.PENDING
    attempts: int = 0

    def is_terminal(self) -> bool:
        return self.state in (TaskState.DONE, TaskState.FAILED)


@dataclass
class Queue:
    name: str
    max_attempts: int = 3
    tasks: list = field(default_factory=list)

    def depth(self) -> int:
        return len([t for t in self.tasks if not t.is_terminal()])
""",
    )
    w(
        root,
        "pyserver/taskflow/storage.py",
        """
\"\"\"SQLite-backed persistence for tasks and queues.\"\"\"

import json
import sqlite3

from .models import Queue, Task, TaskState

SCHEMA = \"\"\"
CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY, queue TEXT, payload TEXT, state TEXT, attempts INT
);
\"\"\"


class Store:
    def __init__(self, path: str = ":memory:") -> None:
        self.db = sqlite3.connect(path)
        self.db.executescript(SCHEMA)

    def save_task(self, task: Task) -> None:
        self.db.execute(
            "REPLACE INTO tasks VALUES (?, ?, ?, ?, ?)",
            (task.id, task.queue, json.dumps(task.payload),
             task.state.value, task.attempts),
        )
        self.db.commit()

    def load_task(self, task_id: str) -> Task | None:
        row = self.db.execute(
            "SELECT id, queue, payload, state, attempts FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
        if row is None:
            return None
        return Task(row[0], row[1], json.loads(row[2]),
                    TaskState(row[3]), row[4])

    def queue_snapshot(self, name: str) -> Queue:
        q = Queue(name=name)
        for row in self.db.execute(
            "SELECT id, queue, payload, state, attempts FROM tasks WHERE queue = ?",
            (name,),
        ):
            q.tasks.append(Task(row[0], row[1], json.loads(row[2]),
                                TaskState(row[3]), row[4]))
        return q
""",
    )
    w(
        root,
        "pyserver/taskflow/dispatch.py",
        """
\"\"\"Dispatch loop: hand pending tasks to workers, retry failures.\"\"\"

from .models import Task, TaskState
from .storage import Store


class Dispatcher:
    def __init__(self, store: Store, max_attempts: int = 3) -> None:
        self.store = store
        self.max_attempts = max_attempts

    def claim_next(self, queue: str) -> Task | None:
        snap = self.store.queue_snapshot(queue)
        for task in snap.tasks:
            if task.state is TaskState.PENDING:
                task.state = TaskState.RUNNING
                task.attempts += 1
                self.store.save_task(task)
                return task
        return None

    def complete(self, task: Task, ok: bool) -> Task:
        if ok:
            task.state = TaskState.DONE
        elif task.attempts >= self.max_attempts:
            task.state = TaskState.FAILED
        else:
            task.state = TaskState.PENDING
        self.store.save_task(task)
        return task
""",
    )
    w(
        root,
        "pyserver/taskflow/api.py",
        """
\"\"\"HTTP-ish API surface: thin request handlers over the dispatcher.\"\"\"

from .dispatch import Dispatcher
from .models import Task
from .storage import Store
from .utils.ids import new_task_id
from .utils.validate import require_fields


class Api:
    def __init__(self, store: Store | None = None) -> None:
        self.store = store or Store()
        self.dispatcher = Dispatcher(self.store)

    def submit(self, queue: str, payload: dict) -> Task:
        require_fields(payload, ["kind"])
        task = Task(id=new_task_id(queue), queue=queue, payload=payload)
        self.store.save_task(task)
        return task

    def poll(self, queue: str) -> Task | None:
        return self.dispatcher.claim_next(queue)

    def ack(self, task: Task, ok: bool) -> Task:
        return self.dispatcher.complete(task, ok)
""",
    )
    w(root, "pyserver/taskflow/utils/__init__.py", "")
    w(
        root,
        "pyserver/taskflow/utils/ids.py",
        """
\"\"\"Deterministic-ish id helpers.\"\"\"

import hashlib
import itertools

_counter = itertools.count(1)


def new_task_id(queue: str) -> str:
    n = next(_counter)
    digest = hashlib.sha1(f"{queue}:{n}".encode()).hexdigest()[:8]
    return f"{queue}-{digest}"
""",
    )
    w(
        root,
        "pyserver/taskflow/utils/validate.py",
        """
\"\"\"Payload validation helpers.\"\"\"


class ValidationError(ValueError):
    pass


def require_fields(payload: dict, fields: list) -> None:
    missing = [f for f in fields if f not in payload]
    if missing:
        raise ValidationError(f"missing fields: {missing}")
""",
    )
    w(
        root,
        "pyserver/tests/test_dispatch.py",
        """
from taskflow.api import Api
from taskflow.models import TaskState


def test_submit_poll_ack_roundtrip():
    api = Api()
    submitted = api.submit("default", {"kind": "email"})
    claimed = api.poll("default")
    assert claimed is not None and claimed.id == submitted.id
    finished = api.ack(claimed, ok=True)
    assert finished.state is TaskState.DONE


def test_retry_until_failed():
    api = Api()
    api.submit("default", {"kind": "flaky"})
    for _ in range(3):
        task = api.poll("default")
        task = api.ack(task, ok=False)
    assert task.state is TaskState.FAILED
""",
    )
    for name in HANDLERS:
        w(
            root,
            f"pyserver/taskflow/handlers/{name}.py",
            f"""
\"\"\"/{name} endpoint handlers (generated demo module).\"\"\"

from ..api import Api


def get_{name}(api: Api, request: dict) -> dict:
    queue = request.get("queue", "{name}")
    task = api.poll(queue)
    return {{"endpoint": "{name}", "task": task.id if task else None}}


def post_{name}(api: Api, request: dict) -> dict:
    task = api.submit(request.get("queue", "{name}"), request["payload"])
    return {{"endpoint": "{name}", "created": task.id}}
""",
        )
    w(
        root,
        "pyserver/taskflow/handlers/__init__.py",
        "".join(f"from . import {n}\n" for n in HANDLERS),
    )


def typescript_client(root: Path) -> None:
    w(
        root,
        "webclient/src/api.ts",
        """
/** Typed client for the taskflow pyserver API. */

export interface TaskDto {
  id: string;
  queue: string;
  state: "pending" | "running" | "done" | "failed";
  attempts: number;
}

export class ApiClient {
  constructor(private baseUrl: string) {}

  async submit(queue: string, payload: object): Promise<TaskDto> {
    const res = await fetch(`${this.baseUrl}/${queue}`, {
      method: "POST",
      body: JSON.stringify({ payload }),
    });
    return res.json();
  }

  async poll(queue: string): Promise<TaskDto | null> {
    const res = await fetch(`${this.baseUrl}/${queue}`);
    return res.status === 204 ? null : res.json();
  }
}
""",
    )
    w(
        root,
        "webclient/src/format.ts",
        """
import type { TaskDto } from "./api";

export function stateBadge(task: TaskDto): string {
  const glyphs: Record<TaskDto["state"], string> = {
    pending: "…", running: "▶", done: "✓", failed: "✗",
  };
  return `${glyphs[task.state]} ${task.id}`;
}

export function attemptsLabel(task: TaskDto): string {
  return task.attempts === 0 ? "fresh" : `retry ${task.attempts}`;
}
""",
    )
    for name in COMPONENTS:
        w(
            root,
            f"webclient/src/components/{name}.ts",
            f"""
import {{ ApiClient }} from "../api";
import {{ stateBadge }} from "../format";

/** {name} component (generated demo module). */
export class {name} {{
  constructor(private client: ApiClient) {{}}

  async render(queue: string): Promise<string> {{
    const task = await this.client.poll(queue);
    return task ? stateBadge(task) : "<empty>";
  }}
}}
""",
        )


def go_worker(root: Path) -> None:
    w(
        root,
        "goworker/go.mod",
        """
module example.com/taskflow/goworker

go 1.22
""",
    )
    w(
        root,
        "goworker/main.go",
        """
package main

import (
	"fmt"

	"example.com/taskflow/goworker/worker"
)

func main() {
	cfg := worker.DefaultConfig()
	pool := worker.NewPool(cfg)
	fmt.Println(pool.Run("default"))
}
""",
    )
    w(
        root,
        "goworker/worker/config.go",
        """
package worker

// Config controls pool sizing and retry behavior.
type Config struct {
	Concurrency int
	MaxAttempts int
}

// DefaultConfig mirrors pyserver's dispatcher defaults.
func DefaultConfig() Config {
	return Config{Concurrency: 4, MaxAttempts: 3}
}
""",
    )
    w(
        root,
        "goworker/worker/pool.go",
        """
package worker

import "fmt"

// Pool consumes tasks from a named queue.
type Pool struct {
	cfg Config
}

func NewPool(cfg Config) *Pool {
	return &Pool{cfg: cfg}
}

func (p *Pool) Run(queue string) string {
	return fmt.Sprintf("pool(%d) draining %s", p.cfg.Concurrency, queue)
}
""",
    )


def ops(root: Path) -> None:
    w(
        root,
        "ops/deploy.sh",
        """
#!/usr/bin/env bash
# Deploy the taskflow stack (demo fixture).
set -euo pipefail

build_server() {
  (cd pyserver && python -m compileall taskflow)
}

build_worker() {
  (cd goworker && go build ./...)
}

build_server
build_worker
echo "deployed"
""",
    )
    w(
        root,
        "ops/smoke.sh",
        """
#!/usr/bin/env bash
# Post one task and poll it back through the API (demo fixture).
set -euo pipefail

submit_task() {
  python - <<'PY'
from taskflow.api import Api
api = Api()
print(api.submit("smoke", {"kind": "ping"}).id)
PY
}

submit_task
""",
    )
    w(
        root,
        "README.md",
        """
# taskflow (demo fixture)

A deliberately small multi-language codebase for exercising `ctx`:
a Python API server (`pyserver/`), a TypeScript web client
(`webclient/`), a Go worker pool (`goworker/`), and bash ops scripts
(`ops/`). Generated by `context-tree/scripts/gen-demo-codebase.py` —
regenerate rather than hand-edit.
""",
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: gen-demo-codebase.py <outdir>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    python_core(root)
    typescript_client(root)
    go_worker(root)
    ops(root)
    count = sum(1 for p in root.rglob("*") if p.is_file())
    print(f"generated {count} files under {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
