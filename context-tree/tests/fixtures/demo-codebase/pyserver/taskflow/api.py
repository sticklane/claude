"""HTTP-ish API surface: thin request handlers over the dispatcher."""

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
