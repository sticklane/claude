"""Behavioral coverage for resume_agent() and its /api/agent/resume branches.

resume_agent() has three real branches: unknown-sid rejection, spawn-failure
propagation, and the success path that dispatches a detached `claude --resume`.
These tests mock only the two process-boundary calls it makes -- `_claude_json`
(reads the live session list) and `_claude_run_bg` (spawns the background
process) -- and drive the real handler, asserting its (ok, msg) tuple and the
observable dispatch effect (argv + cwd handed to the spawn boundary).
"""

import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch

_spec = importlib.util.spec_from_file_location(
    "ac", str(Path(__file__).resolve().parent.parent / "agent-console.py")
)
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)


class TestResumeAgentUnknownSid(unittest.TestCase):
    def test_returns_not_a_known_session_when_sid_absent(self):
        # _claude_json reports two live sessions, neither matching the request.
        agents = [
            {"sessionId": "aaa", "cwd": "/repo/a"},
            {"sessionId": "bbb", "cwd": "/repo/b"},
        ]
        with (
            patch.object(ac, "_claude_json", return_value=agents),
            patch.object(ac, "_claude_run_bg") as run_bg,
        ):
            ok, msg = ac.resume_agent("ccc", "do the thing")
        self.assertFalse(ok)
        self.assertEqual(msg, "not a known session")
        # Rejected before the spawn boundary: no process is launched.
        run_bg.assert_not_called()


class TestResumeAgentSpawnFailure(unittest.TestCase):
    def test_runtime_error_from_spawn_boundary_propagates(self):
        agents = [{"sessionId": "sid1", "cwd": "/repo/a"}]
        with (
            patch.object(ac, "_claude_json", return_value=agents),
            patch.object(
                ac,
                "_claude_run_bg",
                side_effect=RuntimeError("claude not found on PATH"),
            ),
        ):
            ok, msg = ac.resume_agent("sid1", "go")
        self.assertFalse(ok)
        self.assertEqual(msg, "claude not found on PATH")

    def test_oserror_from_spawn_boundary_propagates(self):
        agents = [{"sessionId": "sid1", "cwd": "/repo/a"}]
        with (
            patch.object(ac, "_claude_json", return_value=agents),
            patch.object(
                ac, "_claude_run_bg", side_effect=OSError("exec format error")
            ),
        ):
            ok, msg = ac.resume_agent("sid1", "go")
        self.assertFalse(ok)
        self.assertEqual(msg, "exec format error")


class TestResumeAgentSuccess(unittest.TestCase):
    def test_success_returns_resumed_and_dispatches_correct_command(self):
        repo = "/repo/target"
        agents = [{"sessionId": "sid1", "cwd": repo}]
        with (
            patch.object(ac, "_claude_json", return_value=agents),
            patch.object(ac, "_claude_run_bg") as run_bg,
        ):
            ok, msg = ac.resume_agent("sid1", "keep going")
        # Response indicates success...
        self.assertTrue(ok)
        self.assertEqual(msg, "resumed")
        # ...and the observable dispatch effect: the exact resume command and
        # the realpath-resolved cwd handed to the spawn boundary.
        run_bg.assert_called_once_with(
            ["--bg", "--resume", "sid1", "-p", "keep going"],
            os.path.realpath(repo),
        )

    def test_empty_prompt_defaults_to_continue_and_succeeds(self):
        # An empty prompt is not a failure: resume_agent defaults it to
        # "continue" and dispatches. Covered here as a passing case.
        repo = "/repo/target"
        agents = [{"sessionId": "sid1", "cwd": repo}]
        with (
            patch.object(ac, "_claude_json", return_value=agents),
            patch.object(ac, "_claude_run_bg") as run_bg,
        ):
            ok, msg = ac.resume_agent("sid1", "")
        self.assertTrue(ok)
        self.assertEqual(msg, "resumed")
        run_bg.assert_called_once_with(
            ["--bg", "--resume", "sid1", "-p", "continue"],
            os.path.realpath(repo),
        )


if __name__ == "__main__":
    unittest.main()
