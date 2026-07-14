"""Tests for ``execute_push()``'s three real branches — the complete surface,
since it has no dirty-check or ahead/behind logic:

- **rc 0** (push succeeds): ``ok:true`` / ``exit:0`` AND the board cache is
  actually invalidated (observed via a stale-then-fresh read of
  ``_board_cache["ts"]``, not a mock-called check on ``_invalidate_board``).
- **rc non-zero** (push to a broken remote): ``ok:false`` and the message
  carries the exit code.
- **``subprocess.TimeoutExpired``**: ``exit:None`` and a timeout message.

The push mechanics are exercised for real against a bare git "remote" — no
mocking of the push itself. Only the timeout branch mocks ``subprocess.run``,
because a real 60s timeout isn't practical to trigger deterministically.

Import-by-path mirrors the sibling tests (``agent-console.py`` has a hyphen).
"""

import importlib.util
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


def _git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo_with_remote(root: Path):
    """Bare 'remote' plus a work repo whose ``main`` tracks it, so a bare
    ``git push`` (no refspec) has an upstream to resolve. Returns the work dir."""
    bare = root / "remote.git"
    work = root / "work"
    bare.mkdir()
    work.mkdir()
    _git("init", "--bare", str(bare), cwd=str(root))
    _git("init", "-b", "main", ".", cwd=str(work))
    _git("config", "user.email", "t@example.com", cwd=str(work))
    _git("config", "user.name", "Test", cwd=str(work))
    (work / "f.txt").write_text("one\n", encoding="utf-8")
    _git("add", "-A", cwd=str(work))
    _git("commit", "-m", "init", cwd=str(work))
    _git("remote", "add", "origin", str(bare), cwd=str(work))
    _git("push", "-u", "origin", "main", cwd=str(work))
    return work


def _commit_change(work: Path, text: str):
    (work / "f.txt").write_text(text, encoding="utf-8")
    _git("add", "-A", cwd=str(work))
    _git("commit", "-m", "change", cwd=str(work))


class ExecutePushSuccessTest(unittest.TestCase):
    """rc-0 branch: push succeeds and the board cache is invalidated."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.work = _init_repo_with_remote(Path(self._tmp.name))
        _commit_change(self.work, "two\n")  # a real commit for the push to send
        self._saved_ts = ac._board_cache["ts"]

    def tearDown(self):
        ac._board_cache["ts"] = self._saved_ts
        self._tmp.cleanup()

    def test_rc0_push_succeeds_and_invalidates_board_cache(self):
        # Seed a non-zero timestamp so invalidation (which sets ts to 0.0) is
        # observable as a real change, not a no-op on the default 0.0.
        ac._board_cache["ts"] = 1234.5
        before = ac._board_cache["ts"]

        result = ac.execute_push({"argv": ["git", "-C", str(self.work), "push"]})

        body = result["body"]
        self.assertTrue(body["ok"])
        self.assertEqual(body["exit"], 0)
        after = ac._board_cache["ts"]
        self.assertNotEqual(before, after)  # stale-then-fresh: cache invalidated
        self.assertEqual(after, 0.0)


class ExecutePushFailureTest(unittest.TestCase):
    """rc-nonzero branch: push to a broken remote reports the exit code."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.work = _init_repo_with_remote(root)
        # Repoint origin at a path with no repo, then make a commit to push —
        # the next `git push` fails hard (non-zero exit).
        _git("remote", "set-url", "origin", str(root / "gone.git"), cwd=str(self.work))
        _commit_change(self.work, "changed\n")

    def tearDown(self):
        self._tmp.cleanup()

    def test_rc_nonzero_push_reports_exit_code_in_message(self):
        result = ac.execute_push({"argv": ["git", "-C", str(self.work), "push"]})

        body = result["body"]
        self.assertFalse(body["ok"])
        self.assertIsNotNone(body["exit"])
        self.assertNotEqual(body["exit"], 0)
        self.assertIn(str(body["exit"]), body["message"])


class ExecutePushTimeoutTest(unittest.TestCase):
    """TimeoutExpired branch: exit is None and the message states the timeout."""

    def test_timeout_reports_none_exit_and_timeout_message(self):
        with patch.object(
            ac.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(
                cmd=["git", "push"], timeout=ac.ACTION_TIMEOUT
            ),
        ):
            result = ac.execute_push({"argv": ["git", "push"]})

        body = result["body"]
        self.assertFalse(body["ok"])
        self.assertIsNone(body["exit"])
        self.assertIn("timed out", body["message"].lower())


if __name__ == "__main__":
    unittest.main()
