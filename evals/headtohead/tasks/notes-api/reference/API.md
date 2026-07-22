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

Returns notes, with optional pagination and tag filtering via query
parameters:

- `limit` — maximum notes to return; a positive integer. Omit for no limit.
- `offset` — number of matching notes to skip; a non-negative integer
  (default `0`).
- `tag` — return only notes carrying this tag.

A bad `limit` (`0`, negative, or non-numeric) or `offset` (negative or
non-numeric) returns `400` in the standard error shape. An `offset` past the
end returns an empty `notes` list with the metadata intact.

The response includes `total` (the count of matching notes before paging),
plus the effective `limit` and `offset`, so a client can page through all
notes:

```json
{
  "notes": [ { "id": 1, "text": "buy milk", "tags": ["home"] } ],
  "total": 42,
  "limit": 10,
  "offset": 0
}
```

### `POST /notes`

Create a note. Body: `{ "text": "<non-empty string>", "tags": ["<string>", ...] }`
(`tags` optional, defaults to `[]`). Returns `201` with the created note.
A malformed body returns `400` in the standard error shape.

### `GET /notes/{id}`

Returns the note with that id, or `404` in the standard error shape.
