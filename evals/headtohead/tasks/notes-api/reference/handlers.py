"""Request handlers — pure functions over the store.

Each returns an ``(http_status, body_dict)`` pair; the router serialises the
body as JSON. Errors use the service's standard error shape, produced by
``error_body`` (see API.md).
"""

import json

from validation import (
    ValidationError,
    parse_list_params,
    validate_note_payload,
)


def error_body(code, message):
    """The standard error shape used for every non-2xx response."""
    return {"error": {"code": code, "message": message}}


def list_notes(store, query):
    """GET /notes — paginated, optionally tag-filtered.

    Query parameters (all optional): ``limit`` (positive int; unbounded when
    omitted), ``offset`` (non-negative int, default 0), ``tag`` (return only
    notes carrying that tag). Bad values return 400 in the standard shape.
    The response carries ``total`` (matching-note count, before paging),
    ``limit``, and ``offset`` so a client can page through everything.
    """
    try:
        limit, offset, tag = parse_list_params(query)
    except ValidationError as exc:
        return 400, error_body("bad_request", exc.message)

    notes = store.all()
    if tag is not None:
        notes = [n for n in notes if tag in n.tags]
    total = len(notes)

    page = notes[offset:]
    if limit is not None:
        page = page[:limit]

    return 200, {
        "notes": [n.to_dict() for n in page],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def create_note(store, raw_body):
    """POST /notes — create a note from a JSON body."""
    try:
        payload = json.loads(raw_body or "")
    except (ValueError, TypeError):
        return 400, error_body("bad_request", "request body must be valid JSON")
    try:
        clean = validate_note_payload(payload)
    except ValidationError as exc:
        return 400, error_body("bad_request", exc.message)
    note = store.add(clean["text"], clean["tags"])
    return 201, note.to_dict()


def get_note(store, note_id):
    """GET /notes/{id} — a single note or a 404."""
    note = store.get(note_id)
    if note is None:
        return 404, error_body("not_found", "no note with id %d" % note_id)
    return 200, note.to_dict()
