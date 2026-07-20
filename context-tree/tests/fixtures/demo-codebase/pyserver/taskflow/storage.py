"""SQLite-backed persistence for tasks and queues."""

import json
import sqlite3

from .models import Queue, Task, TaskState

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY, queue TEXT, payload TEXT, state TEXT, attempts INT
);
"""


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
