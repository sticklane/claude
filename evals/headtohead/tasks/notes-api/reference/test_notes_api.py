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


# --- pagination + tag filter (added behaviour) --------------------------


def _seed(store, count):
    for i in range(count):
        store.add("note %d" % i, ["work"] if i % 2 == 0 else ["home"])
    return store


def test_list_notes_respects_limit_and_offset():
    store = _seed(NoteStore(), 25)
    _, page1 = handlers.list_notes(store, {"limit": ["10"], "offset": ["0"]})
    _, page2 = handlers.list_notes(store, {"limit": ["10"], "offset": ["10"]})
    _, page3 = handlers.list_notes(store, {"limit": ["10"], "offset": ["20"]})
    assert [len(p["notes"]) for p in (page1, page2, page3)] == [10, 10, 5]
    ids = [n["id"] for p in (page1, page2, page3) for n in p["notes"]]
    assert ids == list(range(1, 26))  # every note, once, in order


def test_list_notes_reports_total_for_paging():
    store = _seed(NoteStore(), 25)
    _, body = handlers.list_notes(store, {"limit": ["10"], "offset": ["0"]})
    assert body["total"] == 25
    assert body["limit"] == 10
    assert body["offset"] == 0


def test_list_notes_offset_past_end_is_empty_with_metadata():
    store = _seed(NoteStore(), 25)
    status, body = handlers.list_notes(store, {"limit": ["10"], "offset": ["100"]})
    assert status == 200
    assert body["notes"] == []
    assert body["total"] == 25


def test_list_notes_tag_filter_alone():
    store = _seed(NoteStore(), 25)
    _, body = handlers.list_notes(store, {"tag": ["work"]})
    assert body["total"] == 13
    assert all("work" in n["tags"] for n in body["notes"])


def test_list_notes_tag_filter_combined_with_paging():
    store = _seed(NoteStore(), 25)
    _, body = handlers.list_notes(
        store, {"tag": ["work"], "limit": ["5"], "offset": ["10"]}
    )
    assert body["total"] == 13
    assert len(body["notes"]) == 3
    assert all("work" in n["tags"] for n in body["notes"])


def test_list_notes_bad_limit_is_400_standard_shape():
    store = _seed(NoteStore(), 5)
    for bad in ("0", "-1", "abc"):
        status, body = handlers.list_notes(store, {"limit": [bad]})
        assert status == 400, bad
        assert set(body["error"]) == {"code", "message"}


def test_list_notes_bad_offset_is_400_standard_shape():
    store = _seed(NoteStore(), 5)
    for bad in ("-1", "xyz"):
        status, body = handlers.list_notes(store, {"offset": [bad]})
        assert status == 400, bad
        assert set(body["error"]) == {"code", "message"}


def test_http_pagination_end_to_end(client):
    for i in range(12):
        client.post(
            "/notes", {"text": "n%d" % i, "tags": ["work"] if i % 2 == 0 else ["home"]}
        )
    status, body = client.get("/notes?limit=5&offset=5")
    assert status == 200
    assert len(body["notes"]) == 5
    assert body["total"] == 12
    status, err = client.get("/notes?limit=0")
    assert status == 400
    assert set(err["error"]) == {"code", "message"}
