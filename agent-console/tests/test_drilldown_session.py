"""Tests for the /session/<id> detail route: the tail-first transcript reader,
tool-payload elision, transcript-path globbing, and 404s — plus an end-to-end
pin that a repo page's session link resolves to a session page.

No live server: the Handler is exercised by constructing a bare instance and
capturing what it would write (mirrors test_drilldown_pages.py).
"""

import importlib.util
import json
import re
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch

_spec = importlib.util.spec_from_file_location(
    "ac", str(Path(__file__).resolve().parent.parent / "agent-console.py")
)
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)


def _headers(mapping):
    msg = Message()
    for k, v in mapping.items():
        msg[k] = v
    return msg


def _handler(path, host="127.0.0.1:8899"):
    h = ac.Handler.__new__(ac.Handler)
    h.path = path
    h.headers = _headers({"Host": host})
    captured = {}

    def _send(body, ctype="text/html; charset=utf-8", code=200):
        captured["body"] = body
        captured["ctype"] = ctype
        captured["code"] = code

    h._send = _send
    return h, captured


class _CountingFile:
    """Wraps a real file object, summing every byte handed back by read() so a
    test can assert tail_events never slurps the whole file."""

    def __init__(self, f):
        self._f = f
        self.read_total = 0

    def read(self, *a, **k):
        data = self._f.read(*a, **k)
        self.read_total += len(data) if data else 0
        return data

    def __enter__(self):
        self._f.__enter__()
        return self

    def __exit__(self, *a):
        return self._f.__exit__(*a)

    def __getattr__(self, name):
        return getattr(self._f, name)


def _write_transcript(path: Path, n: int, pad: int = 380) -> None:
    """Write n JSONL events, each carrying its own index and padded so the file
    comfortably exceeds a 64K tail window."""
    lines = []
    for i in range(n):
        ev = {
            "type": "assistant" if i % 2 else "user",
            "message": {
                "role": "assistant" if i % 2 else "user",
                "content": [{"type": "text", "text": f"event-{i} " + "x" * pad}],
            },
            "idx": i,
        }
        lines.append(json.dumps(ev))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class TailEventsTest(unittest.TestCase):
    def test_returns_last_n_of_200_via_tail_window(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.jsonl"
            _write_transcript(p, 200)
            events, total = ac.tail_events(str(p), n=50)
        self.assertEqual(len(events), 50)
        # tail-first: the returned events are the highest indices, not the first
        idxs = [e["idx"] for e in events]
        self.assertEqual(idxs[-1], 199)
        self.assertTrue(min(idxs) >= 100, f"expected tail slice, got {min(idxs)}")
        # byte-ratio estimate lands near the true 200 (never the exact 50 shown)
        self.assertGreater(total, len(events))
        self.assertTrue(150 <= total <= 260, f"estimate off: {total}")

    def test_never_reads_whole_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.jsonl"
            _write_transcript(p, 200)
            size = p.stat().st_size
            self.assertGreater(size, 65_536)
            real_open = open
            spy = {}

            def fake_open(*a, **k):
                cf = _CountingFile(real_open(*a, **k))
                spy["cf"] = cf
                return cf

            with patch("builtins.open", fake_open):
                ac.tail_events(str(p), n=50, window=65_536)
            self.assertLessEqual(spy["cf"].read_total, 65_536)
            self.assertLess(spy["cf"].read_total, size)

    def test_small_file_reports_exact_total(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.jsonl"
            _write_transcript(p, 5)
            events, total = ac.tail_events(str(p), n=50)
        self.assertEqual(len(events), 5)
        self.assertEqual(total, 5)

    def test_grows_window_when_single_line_exceeds_window(self):
        """A lone trailing JSONL line larger than the 64K window must still
        render: with zero events parsed from a non-empty file the window grows
        (capped at file size) instead of showing 'no events'."""
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.jsonl"
            ev = {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "x" * 80_000}],
                },
                "idx": 0,
            }
            p.write_text(json.dumps(ev) + "\n", encoding="utf-8")
            self.assertGreater(p.stat().st_size, 65_536)
            events, total = ac.tail_events(str(p))
        self.assertGreaterEqual(len(events), 1)
        self.assertEqual(events[0]["idx"], 0)

    def test_non_positive_window_terminates_and_returns_events(self):
        """A caller passing window <= 0 must not spin forever: the growth loop
        starts at cur == window (0 or negative), parses nothing, and without a
        floor would double 0 -> 0 (or -1 -> -2 -> ...) never reaching file size.
        The guard floors the next window at 1 so the loop still terminates and
        the events render."""
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.jsonl"
            _write_transcript(p, 8, pad=10)
            for window in (0, -1):
                events, total = ac.tail_events(str(p), n=50, window=window)
                # Terminates (no hang) and yields the tail: a non-empty,
                # contiguous suffix of the events ending at the last one.
                self.assertGreaterEqual(
                    len(events), 1, f"window={window} returned nothing"
                )
                idxs = [e["idx"] for e in events]
                self.assertEqual(
                    idxs[-1], 7, f"window={window} not tail-anchored"
                )
                self.assertEqual(
                    idxs, list(range(idxs[0], 8)),
                    f"window={window} not a contiguous suffix",
                )


class ElisionTest(unittest.TestCase):
    def _events(self):
        return [
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "running a search"},
                        {
                            "type": "tool_use",
                            "id": "tu_grep",
                            "name": "Grep",
                            "input": {"pattern": "SECRET_PATTERN_XYZ"},
                        },
                        {
                            "type": "tool_use",
                            "id": "tu_bash",
                            "name": "Bash",
                            "input": {"command": "SECRET_CMD rm -rf /tmp"},
                        },
                    ],
                },
            },
            {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "tu_grep",
                            "content": "SECRET_RESULT_TEXT match line",
                        },
                        {
                            "type": "tool_result",
                            "tool_use_id": "tu_missing",
                            "content": "ORPHAN_RESULT_TEXT",
                        },
                    ],
                },
            },
        ]

    def test_tool_use_renders_name_marker_no_payload(self):
        html = ac._render_events(self._events())
        self.assertIn("[tool: Grep]", html)
        self.assertIn("[tool: Bash]", html)
        for leaked in (
            "SECRET_PATTERN_XYZ",
            "SECRET_CMD",
            "rm -rf",
            "SECRET_RESULT_TEXT",
            "ORPHAN_RESULT_TEXT",
        ):
            self.assertNotIn(leaked, html, f"payload leaked: {leaked}")

    def test_tool_result_resolves_name_else_generic(self):
        html = ac._render_events(self._events())
        self.assertIn("[tool: Grep result]", html)  # resolved from tu_grep
        self.assertIn("[tool result]", html)  # tu_missing has no match

    def test_message_text_is_preserved(self):
        html = ac._render_events(self._events())
        self.assertIn("running a search", html)


class TranscriptPathTest(unittest.TestCase):
    def test_globs_projects_for_session_jsonl(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            proj = root / "-Users-someone-repo"
            proj.mkdir()
            sid = "abc-123-session"
            (proj / f"{sid}.jsonl").write_text("{}\n", encoding="utf-8")
            found = ac._transcript_path(sid, root=root)
            self.assertIsNotNone(found)
            self.assertEqual(Path(found).name, f"{sid}.jsonl")

    def test_missing_transcript_returns_none(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(ac._transcript_path("no-such-sid", root=Path(d)))


def _session_entry(sid, prompt="hello world", state="idle", cwd="/tmp/repo"):
    seid = ac._entity_id("session", sid)
    return seid, {
        "id": seid,
        "kind": "session",
        "title": prompt[:90],
        "root": cwd,
        "session": {
            "id": sid,
            "cwd": cwd,
            "prompt": prompt,
            "state": state,
            "start_ts": 1_783_000_000.0,
            "last_ts": 1_783_100_000.0,
            "end_ts": 1_783_100_000.0,
            "branch": "main",
        },
    }


class SessionPageRouteTest(unittest.TestCase):
    def test_page_renders_metadata_and_transcript_tail(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            proj = root / "-Users-x-repo"
            proj.mkdir()
            sid = "sid-with-transcript"
            _write_transcript(proj / f"{sid}.jsonl", 200)
            seid, entry = _session_entry(sid, prompt="fix the bug")
            with (
                patch.object(ac, "get_pages", create=True, return_value={seid: entry}),
                patch.object(ac, "_projects_root", return_value=root),
            ):
                h, cap = _handler(f"/session/{seid}")
                h.do_GET()
        self.assertEqual(cap["code"], 200)
        body = cap["body"].decode("utf-8")
        self.assertIn(sid, body)  # sessionId in metadata
        self.assertIn("idle", body)  # state
        self.assertIn("event-199", body)  # transcript tail present
        self.assertNotIn("event-0 ", body)  # head not shown
        self.assertRegex(body, r"last\s+50\s+of\s+~\s*\d+")  # banner

    def test_no_transcript_renders_metadata_not_error(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            seid, entry = _session_entry("sid-no-file", prompt="orphan session")
            with (
                patch.object(ac, "get_pages", create=True, return_value={seid: entry}),
                patch.object(ac, "_projects_root", return_value=root),
            ):
                h, cap = _handler(f"/session/{seid}")
                h.do_GET()
        self.assertEqual(cap["code"], 200)
        body = cap["body"].decode("utf-8")
        self.assertIn("sid-no-file", body)
        self.assertIn("no transcript found", body)

    def test_resume_button_present(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            seid, entry = _session_entry("sid-btn")
            with (
                patch.object(ac, "get_pages", create=True, return_value={seid: entry}),
                patch.object(ac, "_projects_root", return_value=root),
            ):
                h, cap = _handler(f"/session/{seid}")
                h.do_GET()
        body = cap["body"].decode("utf-8")
        self.assertIn('data-act="resume"', body)
        self.assertIn('data-sid="sid-btn"', body)

    def test_unknown_id_is_404(self):
        with patch.object(ac, "get_pages", create=True, return_value={}):
            h, cap = _handler("/session/deadbeefdeadbeef")
            h.do_GET()
        self.assertEqual(cap["code"], 404)

    def test_traversal_id_is_404(self):
        with patch.object(ac, "get_pages", create=True, return_value={}):
            h, cap = _handler("/session/../../etc/passwd")
            h.do_GET()
        self.assertEqual(cap["code"], 404)
        self.assertNotIn(b"root:", cap["body"])

    def test_wrong_kind_id_is_404(self):
        # an id that maps to a repo entry, not a session, must not render here
        entry = {"id": "x", "kind": "repo", "path": "/tmp"}
        with patch.object(ac, "get_pages", create=True, return_value={"x": entry}):
            h, cap = _handler("/session/x")
            h.do_GET()
        self.assertEqual(cap["code"], 404)


class RepoLinkResolvesEndToEndTest(unittest.TestCase):
    """Binding constraint from task 02: render_repo_page emits session links as
    /session/<_entity_id("session", sid)>; that id must resolve to a session
    page. Follow a repo page's session link end to end."""

    def _assembled(self, sid):
        return {
            "repos": [
                {
                    "path": "/tmp/fixture-repo",
                    "name": "fixture-repo",
                    "git": {"branch": "main", "dirty": 0, "ahead": 0, "behind": 0},
                    "specs": [],
                    "handoffs": [],
                    "sessions": [
                        {
                            "id": sid,
                            "cwd": "/tmp/fixture-repo",
                            "prompt": "do the thing",
                            "state": "idle",
                            "start_ts": 1_783_000_000.0,
                            "last_ts": 1_783_100_000.0,
                            "end_ts": 1_783_100_000.0,
                            "branch": "main",
                        }
                    ],
                }
            ]
        }

    def test_repo_page_link_resolves_to_session_page(self):
        sid = "end-to-end-sid-42"
        assembled = self._assembled(sid)
        pages = ac.build_page_registry(assembled)

        # the session is registered under the same id the repo page links to
        expected = ac._entity_id("session", sid)
        self.assertIn(expected, pages)
        self.assertEqual(pages[expected]["kind"], "session")

        repo_id = ac._entity_id("repo", "/tmp/fixture-repo")
        repo_html = ac.render_repo_page(pages[repo_id])
        m = re.search(r'/session/([0-9a-f]+)"', repo_html)
        self.assertIsNotNone(m, "repo page emitted no /session/<id> link")
        linked_id = m.group(1)
        self.assertEqual(linked_id, expected)

        # drive the route with that exact id → it resolves (no 404)
        with (
            patch.object(ac, "get_pages", create=True, return_value=pages),
            patch.object(ac, "_projects_root", return_value=Path("/nonexistent")),
        ):
            h, cap = _handler(f"/session/{linked_id}")
            h.do_GET()
        self.assertEqual(cap["code"], 200)
        self.assertIn(sid, cap["body"].decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
