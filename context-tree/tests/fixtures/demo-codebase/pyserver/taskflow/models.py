"""Core domain models."""

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
