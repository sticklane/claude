"""Input validation for note payloads and list query parameters.

A failed validation raises ``ValidationError``; callers turn that into an
HTTP 400 in the service's standard error shape.
"""

import re


class ValidationError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


_NON_NEG_INT = re.compile(r"\d+$")


def _single(query, key):
    """parse_qs stores each value as a list; take the last, or None."""
    values = query.get(key)
    if not values:
        return None
    return values[-1]


def parse_list_params(query):
    """Parse ``limit``/``offset``/``tag`` from a ``GET /notes`` query dict.

    Returns ``(limit, offset, tag)`` where ``limit`` is a positive int or
    ``None`` (unbounded), ``offset`` is a non-negative int (default 0), and
    ``tag`` is a string or ``None``. Raises ``ValidationError`` on any bad
    value so the caller can return HTTP 400.
    """
    limit_raw = _single(query, "limit")
    offset_raw = _single(query, "offset")
    tag = _single(query, "tag")

    limit = None
    if limit_raw is not None:
        if not _NON_NEG_INT.fullmatch(limit_raw) or int(limit_raw) < 1:
            raise ValidationError("'limit' must be a positive integer")
        limit = int(limit_raw)

    offset = 0
    if offset_raw is not None:
        if not _NON_NEG_INT.fullmatch(offset_raw):
            raise ValidationError("'offset' must be a non-negative integer")
        offset = int(offset_raw)

    return limit, offset, tag


def validate_note_payload(payload):
    """Validate a ``POST /notes`` body. Returns a clean dict or raises."""
    if not isinstance(payload, dict):
        raise ValidationError("request body must be a JSON object")
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValidationError("'text' is required and must be a non-empty string")
    tags = payload.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        raise ValidationError("'tags' must be a list of strings")
    return {"text": text, "tags": tags}
