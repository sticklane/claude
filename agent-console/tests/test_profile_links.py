"""Unit tests for R4/R5 of specs/skill-profiling-workboard: the workboard's
profile links and the /api/profile/refresh handler.

Run by scripts/check.sh (unittest discover). No network, no server, no real
subprocess execution — the refresh handler's subprocess calls are stubbed.
"""

import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_spec = importlib.util.spec_from_file_location(
    "ac", str(Path(__file__).resolve().parent.parent / "agent-console.py")
)
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)


class TestWorkboardProfileLinks(unittest.TestCase):
    """SYNTHETIC board fixture only — never assert per-row anchors against
    live data (a live scan may have zero active sessions)."""

    def _board(self, sid):
        return {
            "n_repos": 1,
            "n_open_specs": 0,
            "n_open_tasks": 0,
            "n_active": 1,
            "inbox": [],
            "open_specs": [],
            "task_repos": [],
            "actives": [],
            "repos": [
                {
                    "name": "r1",
                    "git": {},
                    "gh": {},
                    "specs": [],
                    "tasks": None,
                    "handoffs": [],
                    "sessions": [
                        {
                            "state": "active",
                            "prompt": "do x",
                            "branch": "main",
                            "last": 10.0,
                            "start_ts": 1.0,
                            "sid": sid,
                        }
                    ],
                }
            ],
            "orphans": [],
            "health": [],
            "agents": [],
            "resumable": [],
            "repo_names": [],
        }

    def test_session_row_anchor_targets_flamegraph_for_its_sid(self):
        html_out = ac.render_workboard(self._board("sess-abc123"))
        self.assertIn("?tf=session=sess-abc123", html_out)

    def test_page_carries_header_profile_link(self):
        # Distinct from the per-row flamegraph href (which also embeds
        # AGENTPROF_URL but with a longer path) — match the header anchor's
        # exact href attribute so this doesn't pass on the row link alone.
        # Reads AGENTPROF_URL (env-configurable, default 127.0.0.1:8901) rather
        # than pinning the literal, so an install that overrides it still passes.
        html_out = ac.render_workboard(self._board("sess-abc123"))
        self.assertIn(f'href="{ac.AGENTPROF_URL}/"', html_out)


class TestRefreshProfileHandler(unittest.TestCase):
    """R5: refresh_profile() is the function registered under
    /api/profile/refresh in the POST handlers dict. subprocess is stubbed —
    this never executes the real refresh-profile.sh or launchctl. The pprof
    launchd label is install-specific, so every kickstart-path test supplies
    its own AGENT_CONSOLE_PPROF_SERVICE rather than relying on the ambient env.
    """

    SERVICE = "com.example.agent-console-test-pprof"

    def _with_service(self, value):
        return patch.dict(os.environ, {"AGENT_CONSOLE_PPROF_SERVICE": value})

    def _without_service(self):
        env = {
            k: v for k, v in os.environ.items() if k != "AGENT_CONSOLE_PPROF_SERVICE"
        }
        return patch.dict(os.environ, env, clear=True)

    def test_ok_wrapper_shape_on_success(self):
        regen = MagicMock(returncode=0, stdout="regenerated\n", stderr="")
        kick = MagicMock(returncode=0, stdout="", stderr="")
        with self._with_service(self.SERVICE):
            with patch.object(ac.subprocess, "run", side_effect=[regen, kick]):
                ok, msg = ac.refresh_profile()
        self.assertTrue(ok)
        self.assertIsInstance(msg, str)

    def test_ok_true_when_regen_succeeds_but_kickstart_fails(self):
        regen = MagicMock(returncode=0, stdout="regenerated\n", stderr="")
        kick = MagicMock(returncode=1, stdout="", stderr="No such service")
        with self._with_service(self.SERVICE):
            with patch.object(ac.subprocess, "run", side_effect=[regen, kick]):
                ok, msg = ac.refresh_profile()
        self.assertTrue(ok, "kickstart failure alone must not fail the call")
        self.assertIn("kickstart", msg.lower())

    def test_ok_false_wrapper_shape_when_regen_script_fails(self):
        regen = MagicMock(returncode=1, stdout="", stderr="boom")
        with patch.object(ac.subprocess, "run", return_value=regen):
            ok, msg = ac.refresh_profile()
        self.assertFalse(ok)
        self.assertIn("boom", msg)

    def test_kickstart_targets_the_configured_service_label(self):
        regen = MagicMock(returncode=0, stdout="regenerated\n", stderr="")
        kick = MagicMock(returncode=0, stdout="", stderr="")
        with self._with_service(self.SERVICE):
            with patch.object(ac.subprocess, "run", side_effect=[regen, kick]) as run:
                ok, _ = ac.refresh_profile()
        self.assertTrue(ok)
        argv = run.call_args_list[1].args[0]
        self.assertIn("launchctl", argv)
        self.assertTrue(
            any(a.endswith("/" + self.SERVICE) for a in argv),
            f"kickstart target must name the configured label, got {argv}",
        )

    def test_kickstart_skipped_when_service_unconfigured(self):
        regen = MagicMock(returncode=0, stdout="regenerated\n", stderr="")
        with self._without_service():
            with patch.object(ac.subprocess, "run", return_value=regen) as run:
                ok, msg = ac.refresh_profile()
        self.assertTrue(ok, "regeneration alone still succeeds")
        self.assertEqual(
            run.call_count, 1, "no launchctl call without a configured service label"
        )
        self.assertIn("AGENT_CONSOLE_PPROF_SERVICE", msg)


if __name__ == "__main__":
    unittest.main()
