"""/webhooks endpoint handlers (generated demo module)."""

from ..api import Api


def get_webhooks(api: Api, request: dict) -> dict:
    queue = request.get("queue", "webhooks")
    task = api.poll(queue)
    return {"endpoint": "webhooks", "task": task.id if task else None}


def post_webhooks(api: Api, request: dict) -> dict:
    task = api.submit(request.get("queue", "webhooks"), request["payload"])
    return {"endpoint": "webhooks", "created": task.id}
