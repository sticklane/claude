"""Unit tests for the kanban board's status→column mapping — pure function,
no server/network. Loads the hyphenated module via importlib like
test_parsers.py does.
"""

import importlib.util
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "ac", str(Path(__file__).resolve().parent.parent / "agent-console.py")
)
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)


class TestKanbanColumn(unittest.TestCase):
    def test_open_status_maps_to_pending_column(self):
        self.assertEqual(ac._kanban_column("open"), "Pending")

    def test_claimed_status_maps_to_in_progress_column(self):
        self.assertEqual(ac._kanban_column("claimed"), "In Progress")

    def test_needs_verification_status_maps_to_its_column(self):
        self.assertEqual(ac._kanban_column("needs_verification"), "Needs Verification")

    def test_unknown_status_maps_to_blocked_catch_all(self):
        self.assertEqual(ac._kanban_column("waiting"), "Blocked")

    def test_done_status_maps_to_done_column(self):
        self.assertEqual(ac._kanban_column("done"), "Done")

    def test_deferred_status_maps_to_deferred_column(self):
        self.assertEqual(ac._kanban_column("deferred"), "Deferred")

    def test_skipped_status_maps_to_skipped_column(self):
        self.assertEqual(ac._kanban_column("skipped"), "Skipped")


if __name__ == "__main__":
    unittest.main()
