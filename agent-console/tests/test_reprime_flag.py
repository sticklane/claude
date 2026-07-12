"""Tests for the workboard needs-attention re-prime/context budget flag
(spec session-refresh-automation, task 05; requirement R4).

A live (active) session is flagged when it crosses either budget arm —
`sessions.<id>.reprime_count` >= 3 OR `sessions.<id>.p90_ctx` >= 250k — where
the join is the live-session ids against the summary's `sessions` keys, exactly.
A live session absent from the summary is never flagged. The flag names the
session, which arm tripped, the re-prime count + cost, and the summary file's
mtime (the freshness bound).
"""

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

_spec = importlib.util.spec_from_file_location(
    "ac", str(Path(__file__).resolve().parent.parent / "agent-console.py")
)
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)

MTIME = 1_700_000_000.0  # a fixed summary mtime the flag line must surface


def _board_with_session(sid, state="active"):
    """A board carrying one repo session with the given id + liveness state,
    built through the real adapter so the session flows exactly as production."""
    assembled = {
        "repos": [
            {
                "path": "/tmp/nonexistent-repo-xyz",
                "name": "r1",
                "git": {"branch": "main", "dirty": 0, "ahead": 0, "behind": 0},
                "specs": [],
                "handoffs": [],
                "sessions": [
                    {
                        "id": sid,
                        "cwd": "/tmp/nonexistent-repo-xyz",
                        "branch": "main",
                        "prompt": "do x",
                        "last_ts": 10.0,
                        "start_ts": 1.0,
                        "end_ts": 10.0,
                        "bytes": 1,
                        "state": state,
                    }
                ],
            }
        ],
        "orphan_sessions": [],
        "inbox": [],
        "liveness_unknown": False,
    }
    with (
        patch.object(ac, "gh_visibility", return_value={}),
        patch.object(ac, "_git", return_value=None),
    ):
        return ac._adapt_board(assembled, [], [])


def _summary(sessions):
    return {"totals": {"cost_microusd": 0}, "sessions": sessions}


class ReprimeFlag(unittest.TestCase):
    def test_over_reprime_budget_live_session_is_flagged_with_arm_and_mtime(self):
        board = _board_with_session("S1")
        summary = _summary(
            {
                "S1": {
                    "reprime_count": 5,
                    "p90_ctx": 1000,
                    "reprime_cost_microusd": 2_540_000,
                }
            }
        )
        html = ac.render_workboard(board, summary, summary_mtime=MTIME)
        # names the session, which arm, the count, the cost
        self.assertIn("S1", html)
        self.assertIn("re-prime", html.lower())
        self.assertIn("$2.54", html)  # 2_540_000 microusd
        # the summary file's mtime is visible in the flag line (staleness)
        self.assertIn(ac._dt(MTIME), html)
        # it registers as needs-attention, not "Nothing needs you"
        self.assertNotIn("Nothing needs you", html)

    def test_over_ctx_budget_arm_named_context(self):
        board = _board_with_session("S1")
        summary = _summary({"S1": {"reprime_count": 0, "p90_ctx": 300_000}})
        html = ac.render_workboard(board, summary, summary_mtime=MTIME)
        self.assertIn("S1", html)
        self.assertIn("context", html.lower())

    def test_under_budget_live_session_is_not_flagged(self):
        board = _board_with_session("S1")
        summary = _summary({"S1": {"reprime_count": 2, "p90_ctx": 100_000}})
        html = ac.render_workboard(board, summary, summary_mtime=MTIME)
        self.assertIn("Nothing needs you", html)
        self.assertNotIn("budget", html.lower())

    def test_live_session_absent_from_summary_is_not_flagged(self):
        board = _board_with_session("S1")
        # the over-budget entry belongs to a different, non-live session id
        summary = _summary({"OTHER": {"reprime_count": 9, "p90_ctx": 400_000}})
        html = ac.render_workboard(board, summary, summary_mtime=MTIME)
        self.assertIn("Nothing needs you", html)

    def test_non_live_session_over_budget_is_not_flagged(self):
        board = _board_with_session("S1", state="recent")
        summary = _summary({"S1": {"reprime_count": 9, "p90_ctx": 400_000}})
        html = ac.render_workboard(board, summary, summary_mtime=MTIME)
        self.assertIn("Nothing needs you", html)

    def test_older_summary_without_reprime_count_still_evaluates_ctx_arm(self):
        # older cache: session entry omits reprime_count -> treated as 0 on that
        # arm, but the p90_ctx arm still trips (Step 3).
        board = _board_with_session("S1")
        summary = _summary({"S1": {"p90_ctx": 300_000}})
        html = ac.render_workboard(board, summary, summary_mtime=MTIME)
        self.assertIn("S1", html)
        self.assertIn("context", html.lower())
        self.assertIn("$0.00", html)  # no reprime cost -> zero, no crash

    def test_no_summary_yields_no_flag(self):
        board = _board_with_session("S1")
        html = ac.render_workboard(board, None, summary_mtime=None)  # no exception
        self.assertIn("Nothing needs you", html)


if __name__ == "__main__":
    unittest.main()
