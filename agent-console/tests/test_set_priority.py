"""Wrapper-level tests for `set_priority()` — the real file-edit + git-commit
wrapper around the pure `apply_priority` transform.

The pure transform is covered in test_parsers.py (TestPriority:
test_apply_replaces_existing / test_apply_inserts_under_status /
test_apply_unset_removes_line) and path/value rejection is covered there too;
those never touch a real repo. This file adds the missing NEW coverage: a real
temp git repo fixture (real `git`, not a mock) proving the spec file is actually
rewritten on disk and a commit actually records it.
"""

import importlib.util
import os
import subprocess
import tempfile
import unittest
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


def _git(*args, cwd):
    return subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
        env=_GIT_ENV,
        cwd=cwd,
    ).stdout


def _make_spec_repo(root: Path, body: str) -> Path:
    """Init a real git repo under root/work with a committed spec file, and
    return the SPEC.md path. Caller decides the file body (with/without a
    Priority: header)."""
    work = root / "work"
    spec = work / "specs" / "s1" / "SPEC.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(body, encoding="utf-8")
    _git("init", "-b", "main", ".", cwd=work)
    _git("add", "-A", cwd=work)
    _git("commit", "-m", "init spec", cwd=work)
    return spec


class TestSetPriorityWrapper(unittest.TestCase):
    def test_rewrites_priority_header_in_the_real_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            spec = _make_spec_repo(
                root, "# Spec One\n\nStatus: pending\nPriority: P2\n"
            )
            real_repo = os.path.realpath(str(root / "work"))
            with patch.object(ac, "_tracked_repo_reals", return_value={real_repo}):
                ok, msg = ac.set_priority(str(spec), "P0")
            self.assertTrue(ok, msg)
            text = spec.read_text(encoding="utf-8")
            self.assertIn("Priority: P0", text)
            self.assertNotIn("Priority: P2", text)

    def test_records_a_git_commit_for_the_change(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            spec = _make_spec_repo(
                root, "# Spec One\n\nStatus: pending\nPriority: P2\n"
            )
            work = root / "work"
            real_repo = os.path.realpath(str(work))
            before = _git("rev-list", "--count", "HEAD", cwd=work).strip()
            with patch.object(ac, "_tracked_repo_reals", return_value={real_repo}):
                ok, msg = ac.set_priority(str(spec), "P0")
            self.assertTrue(ok, msg)
            after = _git("rev-list", "--count", "HEAD", cwd=work).strip()
            self.assertEqual(int(after), int(before) + 1)
            subject = _git("log", "-1", "--pretty=%s", cwd=work).strip()
            self.assertIn("priority", subject.lower())
            # the edit was actually committed: nothing left dirty in the tree
            status = _git("status", "--porcelain", cwd=work).strip()
            self.assertEqual(status, "")
            # and the committed blob carries the new value
            committed = _git("show", "HEAD:specs/s1/SPEC.md", cwd=work)
            self.assertIn("Priority: P0", committed)

    def test_inserts_priority_and_commits_when_header_absent(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            spec = _make_spec_repo(root, "# Spec One\n\nStatus: pending\n\nbody\n")
            work = root / "work"
            real_repo = os.path.realpath(str(work))
            with patch.object(ac, "_tracked_repo_reals", return_value={real_repo}):
                ok, msg = ac.set_priority(str(spec), "P1")
            self.assertTrue(ok, msg)
            self.assertIn("Priority: P1", spec.read_text(encoding="utf-8"))
            committed = _git("show", "HEAD:specs/s1/SPEC.md", cwd=work)
            self.assertIn("Priority: P1", committed)


if __name__ == "__main__":
    unittest.main()
