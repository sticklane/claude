"""Dispatch loop: hand pending tasks to workers, retry failures."""

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
