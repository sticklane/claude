"""Request handlers — pure functions over the store.

Each returns an ``(http_status, body_dict)`` pair; the router serialises the
body as JSON. Errors use the service's standard error shape, produced by
``error_body`` (see API.md).
"""

import json

from validation import ValidationError, validate_note_payload


def error_body(code, message):
    """The standard error shape used for every non-2xx response."""
    return {"error": {"code": code, "message": message}}


def list_notes(store, query):
    """GET /notes — returns every note at once."""
    notes = store.all()
    return 200, {"notes": [n.to_dict() for n in notes]}


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
