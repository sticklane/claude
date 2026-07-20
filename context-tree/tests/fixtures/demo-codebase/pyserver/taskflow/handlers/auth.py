"""/auth endpoint handlers (generated demo module)."""

from ..api import Api


def get_auth(api: Api, request: dict) -> dict:
    queue = request.get("queue", "auth")
    task = api.poll(queue)
    return {"endpoint": "auth", "task": task.id if task else None}


def post_auth(api: Api, request: dict) -> dict:
    task = api.submit(request.get("queue", "auth"), request["payload"])
    return {"endpoint": "auth", "created": task.id}
