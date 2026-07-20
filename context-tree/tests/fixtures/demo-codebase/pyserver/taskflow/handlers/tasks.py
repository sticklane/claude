"""/tasks endpoint handlers (generated demo module)."""

from ..api import Api


def get_tasks(api: Api, request: dict) -> dict:
    queue = request.get("queue", "tasks")
    task = api.poll(queue)
    return {"endpoint": "tasks", "task": task.id if task else None}


def post_tasks(api: Api, request: dict) -> dict:
    task = api.submit(request.get("queue", "tasks"), request["payload"])
    return {"endpoint": "tasks", "created": task.id}
