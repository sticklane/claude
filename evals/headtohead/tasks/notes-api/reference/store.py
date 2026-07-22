"""In-memory note storage for the notes service."""

from itertools import count


class Note:
    """A single note: an integer id, text, and a list of string tags."""

    def __init__(self, note_id, text, tags):
        self.id = note_id
        self.text = text
        self.tags = list(tags)

    def to_dict(self):
        return {"id": self.id, "text": self.text, "tags": list(self.tags)}


class NoteStore:
    """A tiny in-memory store. Ids are assigned sequentially from 1."""

    def __init__(self):
        self._notes = []
        self._ids = count(1)

    def add(self, text, tags):
        note = Note(next(self._ids), text, tags)
        self._notes.append(note)
        return note

    def all(self):
        return list(self._notes)

    def get(self, note_id):
        for note in self._notes:
            if note.id == note_id:
                return note
        return None
