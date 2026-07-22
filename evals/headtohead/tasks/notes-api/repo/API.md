# Notes API

A tiny JSON notes service built on the Python standard library. All request
and response bodies are JSON.

## Standard error shape

Every non-2xx response has this shape:

```json
{ "error": { "code": "<machine_code>", "message": "<human message>" } }
```

## Endpoints

### `GET /notes`

Returns every note.

```json
{ "notes": [ { "id": 1, "text": "buy milk", "tags": ["home"] } ] }
```

### `POST /notes`

Create a note. Body: `{ "text": "<non-empty string>", "tags": ["<string>", ...] }`
(`tags` optional, defaults to `[]`). Returns `201` with the created note.
A malformed body returns `400` in the standard error shape.

### `GET /notes/{id}`

Returns the note with that id, or `404` in the standard error shape.
