"""Dependency-graph blocker badges + auto-expand for human-blocked specs.

_dag_tasks forwards a `blocker` kind ("human" | "agent") for blocked/failed
tasks — human when the task records no unblock step or an ask-typed one,
agent when it records a run/agent recheck — so viz.dag() can badge the node.
render_workboard auto-expands (`<details open>`) a spec card whose graph
contains a human-blocked node: the human's blockers are visible per repo
without hunting, agent-bounded ones stay collapsed and proceed.
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


def _task(name, status, unblock=None):
    t = {
        "file": f"tasks/{name}",
        "abs": f"/r/tasks/{name}",
        "title": name,
        "status": status,
        "deps": [],
    }
    if unblock:
        t["unblock"] = unblock
    return t


class TestDagTaskBlockerKind(unittest.TestCase):
    def _one(self, status, unblock=None):
        out = ac._dag_tasks([_task("01-a.md", status, unblock)])
        return out[0]

    def test_blocked_without_unblock_is_human(self):
        self.assertEqual(self._one("blocked").get("blocker"), "human")

    def test_blocked_with_ask_unblock_is_human(self):
        self.assertEqual(
            self._one("blocked", {"type": "ask", "step": "which creds?"}).get(
                "blocker"
            ),
            "human",
        )

    def test_blocked_with_run_unblock_is_agent(self):
        self.assertEqual(
            self._one("blocked", {"type": "run", "step": "make recheck"}).get(
                "blocker"
            ),
            "agent",
        )

    def test_failed_without_unblock_is_human(self):
        self.assertEqual(self._one("failed").get("blocker"), "human")

    def test_pending_and_done_carry_no_blocker_key(self):
        self.assertNotIn("blocker", self._one("pending"))
        self.assertNotIn("blocker", self._one("done"))

    def test_draft_carries_no_blocker_key(self):
        # Drafts are agent queue state (intake promotes them), never a badge.
        self.assertNotIn("blocker", self._one("draft"))


class TestHumanBlockedSpecAutoExpands(unittest.TestCase):
    def _render(self, tasks):
        fixture = {
            "repos": [
                {
                    "path": "/tmp/nonexistent-repo-xyz",
                    "name": "r1",
                    "git": {"branch": "main", "dirty": 0, "ahead": 0, "behind": 0},
                    "specs": [
                        {
                            "kind": "toolkit",
                            "slug": "s1",
                            "title": "Spec One",
                            "path": "specs/s1/SPEC.md",
                            "tasks_total": len(tasks),
                            "tasks_done": 0,
                            "tasks": tasks,
                            "last_touched": 100.0,
                        }
                    ],
                    "handoffs": [],
                    "sessions": [],
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
            board = ac._adapt_board(fixture, [], [])
        return ac.render_workboard(board)

    def test_human_blocked_spec_renders_details_open(self):
        html_out = self._render(
            [_task("01-a.md", "done"), _task("02-b.md", "blocked")]
        )
        self.assertIn('<details class="spec"', html_out)
        self.assertIn(" open>", html_out.split('<details class="spec"', 1)[1][:200])

    def test_agent_blocked_spec_stays_collapsed(self):
        html_out = self._render(
            [
                _task("01-a.md", "done"),
                _task(
                    "02-b.md", "blocked", {"type": "agent", "step": "recheck it"}
                ),
            ]
        )
        detail = html_out.split('<details class="spec"', 1)[1][:200]
        self.assertNotIn(" open>", detail)


if __name__ == "__main__":
    unittest.main()
