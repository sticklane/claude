"""Tests for the notes service (snapshot behaviour)."""

import handlers
from store import NoteStore
from validation import ValidationError, validate_note_payload


def test_store_assigns_sequential_ids():
    store = NoteStore()
    first = store.add("a", [])
    second = store.add("b", ["x"])
    assert first.id == 1
    assert second.id == 2
    assert store.get(2).text == "b"


def test_store_get_missing_returns_none():
    assert NoteStore().get(99) is None


def test_validate_note_payload_rejects_empty_text():
    try:
        validate_note_payload({"text": "  "})
        raise AssertionError("expected ValidationError")
    except ValidationError as exc:
        assert "text" in exc.message


def test_validate_note_payload_rejects_non_string_tags():
    try:
        validate_note_payload({"text": "hi", "tags": [1, 2]})
        raise AssertionError("expected ValidationError")
    except ValidationError as exc:
        assert "tags" in exc.message


def test_list_notes_returns_all():
    store = NoteStore()
    for i in range(3):
        store.add("note %d" % i, [])
    status, body = handlers.list_notes(store, {})
    assert status == 200
    assert len(body["notes"]) == 3


def test_create_note_valid_returns_201():
    store = NoteStore()
    status, body = handlers.create_note(store, '{"text": "hello", "tags": ["home"]}')
    assert status == 201
    assert body["id"] == 1
    assert body["tags"] == ["home"]


def test_create_note_bad_json_is_400_standard_shape():
    status, body = handlers.create_note(NoteStore(), "not json")
    assert status == 400
    assert set(body["error"]) == {"code", "message"}


def test_get_note_missing_is_404_standard_shape():
    status, body = handlers.get_note(NoteStore(), 7)
    assert status == 404
    assert set(body["error"]) == {"code", "message"}


def test_http_get_notes_lists_created(client):
    client.post("/notes", {"text": "first", "tags": ["work"]})
    status, body = client.get("/notes")
    assert status == 200
    assert [n["text"] for n in body["notes"]] == ["first"]
