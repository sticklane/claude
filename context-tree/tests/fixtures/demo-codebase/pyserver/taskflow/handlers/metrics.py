"""/metrics endpoint handlers (generated demo module)."""

from ..api import Api


def get_metrics(api: Api, request: dict) -> dict:
    queue = request.get("queue", "metrics")
    task = api.poll(queue)
    return {"endpoint": "metrics", "task": task.id if task else None}


def post_metrics(api: Api, request: dict) -> dict:
    task = api.submit(request.get("queue", "metrics"), request["payload"])
    return {"endpoint": "metrics", "created": task.id}
