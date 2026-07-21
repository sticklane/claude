"""/workers endpoint handlers (generated demo module)."""

from ..api import Api


def get_workers(api: Api, request: dict) -> dict:
    queue = request.get("queue", "workers")
    task = api.poll(queue)
    return {"endpoint": "workers", "task": task.id if task else None}


def post_workers(api: Api, request: dict) -> dict:
    task = api.submit(request.get("queue", "workers"), request["payload"])
    return {"endpoint": "workers", "created": task.id}
