"""Input validation for note payloads.

A failed validation raises ``ValidationError``; callers turn that into an
HTTP 400 in the service's standard error shape.
"""


class ValidationError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


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
