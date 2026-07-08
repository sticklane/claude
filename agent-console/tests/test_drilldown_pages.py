"""Tests for the /repo, /spec, /task detail routes and the board rows that
link into them.

No live server: the Handler is exercised by constructing a bare instance and
capturing what it would write (mirrors test_drilldown_registry.py). The repo
route reads real git state, so the fixture inits a real repo with a bare
remote, an unpushed commit, and a dirty file.
"""

import importlib.util
import os
import subprocess
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

_GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@e",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@e",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
}


def _git(*args, cwd=None):
    subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
        env=_GIT_ENV,
        cwd=cwd,
    )


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


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _make_repo(root: Path, *, upstream=True) -> dict:
    """Init a real repo under root/work: a spec dir, one committed+pushed state,
    one unpushed commit, one dirty (untracked) file, and (when upstream) a bare
    remote with the branch's upstream set. Returns the assemble()-shaped dict."""
    work = root / "work"
    spec_dir = work / "specs" / "s1"
    _write(work / "CLAUDE.md", "# repo conventions\n")
    _write(spec_dir / "SPEC.md", "# Spec One\n\nThis spec does a thing.\n")
    _write(
        spec_dir / "tasks" / "01-task.md",
        "# Task 01\n\nStatus: pending\n"
        "Unblock: finish the migration then ping ops\n\nbody text\n",
    )
    _write(spec_dir / "evidence" / "01-task.md", "# Evidence\n\nverified ok\n")

    _git("init", "-b", "main", str(work))
    _git("add", "-A", cwd=work)
    _git("commit", "-m", "init spec and tasks", cwd=work)
    if upstream:
        remote = root / "remote.git"
        _git("init", "--bare", str(remote))
        _git("remote", "add", "origin", str(remote), cwd=work)
        _git("push", "-u", "origin", "main", cwd=work)
    # one unpushed commit
    _write(work / "feature.txt", "new feature\n")
    _git("add", "-A", cwd=work)
    _git("commit", "-m", "UNPUSHED add feature X", cwd=work)
    # one dirty (untracked) file
    _write(work / "dirty-file.txt", "wip\n")

    task_abs = str(spec_dir / "tasks" / "01-task.md")
    return {
        "repos": [
            {
                "path": str(work),
                "name": "r1",
                "git": {"branch": "main", "dirty": 1, "ahead": 1, "behind": 0},
                "specs": [
                    {
                        "kind": "toolkit",
                        "slug": "s1",
                        "title": "Spec One",
                        "path": "specs/s1/SPEC.md",
                        "priority": "",
                        "tasks_done": 0,
                        "tasks_total": 1,
                        "last_touched": 5.0,
                        "tasks": [
                            {
                                "file": "specs/s1/tasks/01-task.md",
                                "abs": task_abs,
                                "title": "Task 01",
                                "status": "pending",
                                "deps": [],
                            }
                        ],
                    }
                ],
                "sessions": [
                    {
                        "id": "sess-abc",
                        "state": "active",
                        "prompt": "doing stuff",
                        "branch": "main",
                        "last_ts": 5.0,
                        "start_ts": 1.0,
                        "cwd": str(work),
                    }
                ],
                "handoffs": [],
            }
        ],
        "inbox": [],
        "orphan_sessions": [],
        "liveness_unknown": False,
    }


def _ids(assembled: dict) -> dict:
    repo = assembled["repos"][0]
    work = repo["path"]
    spec_dir = os.path.join(work, "specs", "s1")
    task_abs = repo["specs"][0]["tasks"][0]["abs"]
    return {
        "repo": ac._entity_id("repo", work),
        "spec": ac._entity_id("spec", spec_dir),
        "task": ac._entity_id("task", task_abs),
        "work": work,
    }


class TestRepoPage(unittest.TestCase):
    def test_shows_unpushed_commit_and_dirty_file_and_spec_link(self):
        with tempfile.TemporaryDirectory() as td:
            assembled = _make_repo(Path(td), upstream=True)
            reg = ac.build_page_registry(assembled)
            ids = _ids(assembled)
            with patch.object(ac, "get_pages", create=True, return_value=reg):
                h, cap = _handler(f"/repo/{ids['repo']}")
                h.do_GET()
            self.assertEqual(cap["code"], 200)
            body = cap["body"].decode("utf-8")
            self.assertIn(ids["work"], body)
            self.assertIn("UNPUSHED add feature X", body)  # unpushed subject
            self.assertIn("dirty-file.txt", body)  # dirty porcelain entry
            self.assertIn(f'href="/spec/{ids["spec"]}"', body)  # spec link

    def test_no_upstream_renders_fallback_not_error(self):
        with tempfile.TemporaryDirectory() as td:
            assembled = _make_repo(Path(td), upstream=False)
            reg = ac.build_page_registry(assembled)
            ids = _ids(assembled)
            with patch.object(ac, "get_pages", create=True, return_value=reg):
                h, cap = _handler(f"/repo/{ids['repo']}")
                h.do_GET()
            self.assertEqual(cap["code"], 200)  # git exits 128 must not 500
            self.assertIn("no upstream", cap["body"].decode("utf-8").lower())

    def test_unknown_id_is_404(self):
        with patch.object(ac, "get_pages", create=True, return_value={}):
            h, cap = _handler("/repo/deadbeefdeadbeef")
            h.do_GET()
        self.assertEqual(cap["code"], 404)

    def test_traversal_id_is_404(self):
        with patch.object(ac, "get_pages", create=True, return_value={}):
            h, cap = _handler("/repo/../../etc/passwd")
            h.do_GET()
        self.assertEqual(cap["code"], 404)
        self.assertNotIn(b"root:", cap["body"])


class TestSpecPage(unittest.TestCase):
    def test_renders_spec_body_task_table_evidence_and_commits(self):
        with tempfile.TemporaryDirectory() as td:
            assembled = _make_repo(Path(td), upstream=True)
            reg = ac.build_page_registry(assembled)
            ids = _ids(assembled)
            with patch.object(ac, "get_pages", create=True, return_value=reg):
                h, cap = _handler(f"/spec/{ids['spec']}")
                h.do_GET()
            self.assertEqual(cap["code"], 200)
            body = cap["body"].decode("utf-8")
            self.assertIn("Spec One", body)  # rendered SPEC.md
            self.assertIn("Task 01", body)  # task table row
            self.assertIn("pending", body)  # task status
            self.assertIn("finish the migration then ping ops", body)  # Unblock:
            self.assertIn(f'href="/task/{ids["task"]}"', body)  # task link
            self.assertIn('href="/file/', body)  # evidence link
            self.assertIn("init spec and tasks", body)  # commit touching spec dir

    def test_unknown_id_is_404(self):
        with patch.object(ac, "get_pages", create=True, return_value={}):
            h, cap = _handler("/spec/deadbeefdeadbeef")
            h.do_GET()
        self.assertEqual(cap["code"], 404)

    def test_traversal_id_is_404(self):
        with patch.object(ac, "get_pages", create=True, return_value={}):
            h, cap = _handler("/spec/../../../etc/passwd")
            h.do_GET()
        self.assertEqual(cap["code"], 404)


class TestTaskPage(unittest.TestCase):
    def test_renders_task_file(self):
        with tempfile.TemporaryDirectory() as td:
            assembled = _make_repo(Path(td), upstream=True)
            reg = ac.build_page_registry(assembled)
            ids = _ids(assembled)
            with patch.object(ac, "get_pages", create=True, return_value=reg):
                h, cap = _handler(f"/task/{ids['task']}")
                h.do_GET()
            self.assertEqual(cap["code"], 200)
            body = cap["body"].decode("utf-8")
            self.assertIn("Task 01", body)
            self.assertIn("body text", body)

    def test_unknown_id_is_404(self):
        with patch.object(ac, "get_pages", create=True, return_value={}):
            h, cap = _handler("/task/deadbeefdeadbeef")
            h.do_GET()
        self.assertEqual(cap["code"], 404)

    def test_traversal_id_is_404(self):
        with patch.object(ac, "get_pages", create=True, return_value={}):
            h, cap = _handler("/task/..%2f..%2fetc/passwd")
            h.do_GET()
        self.assertEqual(cap["code"], 404)


class TestBoardLinks(unittest.TestCase):
    def test_workboard_rows_link_to_repo_and_spec_pages(self):
        with tempfile.TemporaryDirectory() as td:
            assembled = _make_repo(Path(td), upstream=True)
            board = ac._adapt_board(assembled, [], [])
            html = ac.render_workboard(board)
        self.assertIn('href="/repo/', html)
        self.assertIn('href="/spec/', html)

    def test_page_ids_match_registry_keys(self):
        with tempfile.TemporaryDirectory() as td:
            assembled = _make_repo(Path(td), upstream=True)
            reg = ac.build_page_registry(assembled)
            ids = _ids(assembled)
            for kind in ("repo", "spec", "task"):
                self.assertIn(ids[kind], reg)
                self.assertEqual(reg[ids[kind]]["kind"], kind)


if __name__ == "__main__":
    unittest.main()
