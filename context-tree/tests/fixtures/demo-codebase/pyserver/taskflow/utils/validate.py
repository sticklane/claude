"""Payload validation helpers."""


class ValidationError(ValueError):
    pass


def require_fields(payload: dict, fields: list) -> None:
    missing = [f for f in fields if f not in payload]
    if missing:
        raise ValidationError(f"missing fields: {missing}")
