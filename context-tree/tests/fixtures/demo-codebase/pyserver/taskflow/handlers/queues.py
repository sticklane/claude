"""/queues endpoint handlers (generated demo module)."""

from ..api import Api


def get_queues(api: Api, request: dict) -> dict:
    queue = request.get("queue", "queues")
    task = api.poll(queue)
    return {"endpoint": "queues", "task": task.id if task else None}


def post_queues(api: Api, request: dict) -> dict:
    task = api.submit(request.get("queue", "queues"), request["payload"])
    return {"endpoint": "queues", "created": task.id}
