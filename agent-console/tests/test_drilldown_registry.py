"""Tests for the content-derived entity registry, the read-only /file/<id>
detail route, and the Host-header check shared by all GET routes.

No live server: the Handler is exercised by constructing a bare instance and
capturing what it would write, so routing/Host logic runs for real without a
socket. Import-by-path mirrors test_parsers.py (agent-console.py has a hyphen).
"""

import importlib.util
import os
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
    """A Handler wired to capture _send() instead of writing to a socket."""
    h = ac.Handler.__new__(ac.Handler)
    h.path = path
    h.headers = _headers({"Host": host} if host is not None else {})
    captured = {}

    def _send(body, ctype="text/html; charset=utf-8", code=200):
        captured["body"] = body
        captured["ctype"] = ctype
        captured["code"] = code

    h._send = _send
    return h, captured


def _make_repo(root: Path):
    """A toolkit repo with a spec, a task, an evidence file, CLAUDE.md and a
    handoff — returns the assemble()-shaped dict plus the on-disk file map."""
    (root / "CLAUDE.md").write_text("# repo conventions\n")
    (root / "HANDOFF.md").write_text("# handoff\ncarry on\n")
    spec_dir = root / "specs" / "s1"
    (spec_dir / "tasks").mkdir(parents=True)
    (spec_dir / "evidence").mkdir(parents=True)
    (spec_dir / "SPEC.md").write_text("# Spec One\n\n- do a thing\n")
    task_abs = spec_dir / "tasks" / "01-task.md"
    task_abs.write_text("# Task 01\n\n```\ncode\n```\n")
    (spec_dir / "evidence" / "01-task.md").write_text("# Evidence\nok\n")
    assembled = {
        "repos": [
            {
                "path": str(root),
                "name": "r1",
                "specs": [
                    {
                        "kind": "toolkit",
                        "slug": "s1",
                        "title": "Spec One",
                        "path": "specs/s1/SPEC.md",
                        "tasks": [
                            {
                                "file": "specs/s1/tasks/01-task.md",
                                "abs": str(task_abs),
                                "title": "Task 01",
                                "status": "pending",
                                "deps": [],
                            }
                        ],
                    }
                ],
                "handoffs": [{"title": "H", "path": "HANDOFF.md", "mtime": 5.0}],
            }
        ],
    }
    expected = {
        os.path.realpath(str(root / "CLAUDE.md")),
        os.path.realpath(str(root / "HANDOFF.md")),
        os.path.realpath(str(spec_dir / "SPEC.md")),
        os.path.realpath(str(task_abs)),
        os.path.realpath(str(spec_dir / "evidence" / "01-task.md")),
    }
    return assembled, expected


class TestEntityRegistry(unittest.TestCase):
    def test_registry_has_one_entry_per_source_file(self):
        with tempfile.TemporaryDirectory() as td:
            assembled, expected = _make_repo(Path(td))
            reg = ac.build_entity_registry(assembled)
            paths = [e["path"] for e in reg.values()]
            self.assertEqual(set(paths), expected)
            self.assertEqual(len(paths), len(set(paths)))  # one id per file
            self.assertEqual(len(reg), len(expected))

    def test_ids_are_stable_across_rebuilds(self):
        with tempfile.TemporaryDirectory() as td:
            assembled, _ = _make_repo(Path(td))
            a = ac.build_entity_registry(assembled)
            b = ac.build_entity_registry(assembled)
            self.assertEqual(set(a), set(b))
            for k in a:
                self.assertEqual(a[k]["path"], b[k]["path"])

    def test_id_key_matches_kind_and_path_contract(self):
        with tempfile.TemporaryDirectory() as td:
            assembled, _ = _make_repo(Path(td))
            reg = ac.build_entity_registry(assembled)
            for eid, entry in reg.items():
                self.assertEqual(eid, ac._entity_id(entry["kind"], entry["path"]))


class TestFileRoute(unittest.TestCase):
    def _registry_for(self, fpath, kind="file", title="t"):
        eid = ac._entity_id(kind, fpath)
        return eid, {eid: {"id": eid, "kind": kind, "path": fpath, "title": title}}

    def test_serves_file_contents_html_escaped(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Title\n\n<script>alert(1)</script>\n")
            fpath = f.name
        self.addCleanup(os.unlink, fpath)
        eid, reg = self._registry_for(fpath)
        with patch.object(ac, "get_registry", return_value=reg):
            h, cap = _handler(f"/file/{eid}")
            h.do_GET()
        self.assertEqual(cap["code"], 200)
        body = cap["body"].decode("utf-8")
        self.assertIn("&lt;script&gt;", body)
        self.assertNotIn("<script>alert", body)

    def test_unknown_id_is_404(self):
        with patch.object(ac, "get_registry", return_value={}):
            h, cap = _handler("/file/deadbeefdeadbeef")
            h.do_GET()
        self.assertEqual(cap["code"], 404)

    def test_query_path_is_ignored_and_404(self):
        # path comes from the registry, never the client query string
        with patch.object(ac, "get_registry", return_value={}):
            h, cap = _handler("/file?path=/etc/passwd")
            h.do_GET()
        self.assertEqual(cap["code"], 404)

    def test_dot_dot_traversal_id_is_404(self):
        with patch.object(ac, "get_registry", return_value={}) as gr:
            h, cap = _handler("/file/../../etc/passwd")
            h.do_GET()
        self.assertEqual(cap["code"], 404)
        # id is only ever a dict key — the traversal string never opens a file
        self.assertNotIn(b"root:", cap["body"])
        gr.assert_called()


class TestHostCheck(unittest.TestCase):
    def test_evil_host_is_400_before_routing(self):
        # /healthz would be 200 with a good host — a bad host must 400 first
        h, cap = _handler("/healthz", host="evil.example:8899")
        h.do_GET()
        self.assertEqual(cap["code"], 400)

    def test_localhost_forms_pass(self):
        for host in ("127.0.0.1:8899", "localhost:8899", "[::1]:8899", "127.0.0.1"):
            h, cap = _handler("/healthz", host=host)
            h.do_GET()
            self.assertEqual(cap["code"], 200, host)
            self.assertEqual(cap["body"], b"ok")


class TestLazyScanAndCaching(unittest.TestCase):
    def _wire(self, td):
        assembled, _ = _make_repo(Path(td))
        reg = ac.build_entity_registry(assembled)
        spec_id = next(eid for eid, e in reg.items() if e["path"].endswith("SPEC.md"))
        calls = {"n": 0}

        def fake_assemble(*a, **k):
            calls["n"] += 1
            return assembled

        return assembled, spec_id, calls, fake_assemble

    def test_deep_link_before_any_scan_triggers_lazy_scan_not_404(self):
        with tempfile.TemporaryDirectory() as td:
            _, spec_id, calls, fake_assemble = self._wire(td)
            with (
                patch.object(ac.workboard, "assemble", side_effect=fake_assemble),
                patch.object(ac, "agents_view", return_value=([], [])),
                patch.object(ac, "_adapt_board", return_value={"stub": True}),
            ):
                ac._board_cache.update(ts=0.0, data=None, registry=None)
                h, cap = _handler(f"/file/{spec_id}")
                h.do_GET()
            self.assertEqual(cap["code"], 200)
            self.assertEqual(calls["n"], 1)

    def test_detail_requests_within_ttl_do_zero_additional_scans(self):
        with tempfile.TemporaryDirectory() as td:
            _, spec_id, calls, fake_assemble = self._wire(td)
            with (
                patch.object(ac.workboard, "assemble", side_effect=fake_assemble),
                patch.object(ac, "agents_view", return_value=([], [])),
                patch.object(ac, "_adapt_board", return_value={"stub": True}),
            ):
                ac._board_cache.update(ts=0.0, data=None, registry=None)
                for _ in range(3):
                    h, cap = _handler(f"/file/{spec_id}")
                    h.do_GET()
                    self.assertEqual(cap["code"], 200)
            self.assertEqual(calls["n"], 1)


if __name__ == "__main__":
    unittest.main()
