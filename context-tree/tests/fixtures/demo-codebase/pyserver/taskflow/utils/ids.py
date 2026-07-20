"""Deterministic-ish id helpers."""

import hashlib
import itertools

_counter = itertools.count(1)


def new_task_id(queue: str) -> str:
    n = next(_counter)
    digest = hashlib.sha1(f"{queue}:{n}".encode()).hexdigest()[:8]
    return f"{queue}-{digest}"
