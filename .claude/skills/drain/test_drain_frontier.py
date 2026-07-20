"""Tests for drain_frontier.py: deterministic dispatch-frontier scanner.

Run: python3 .claude/skills/drain/test_drain_frontier.py
or:  python3 -m unittest discover -s .claude/skills/drain

Stdlib-only, like list_specs.py. Each test builds a real spec dir under a
tmp dir (tempfile.TemporaryDirectory) and either calls the module's
functions directly or invokes the script as a subprocess to pin exit codes.
No mocking. One test class per R2 incident class.
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent / "drain_frontier.py"
_spec = importlib.util.spec_from_file_location("drain_frontier", _SCRIPT)
drain_frontier = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(drain_frontier)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_task(
    spec_dir,
    filename,
    status="pending",
    priority=None,
    depends=None,
    touch=None,
    unblock=None,
    title=None,
):
    """Write one task file with the requested single-line headers."""
    body = f"# {title or filename}\n\n"
    if status is not None:
        body += f"Status: {status}\n"
    if unblock is not None:
        body += f"Unblock: {unblock}\n"
    if priority is not None:
        body += f"Priority: {priority}\n"
    if depends is not None:
        body += f"Depends on: {depends}\n"
    if touch is not None:
        body += f"Touch: {touch}\n"
    body += "\n## Goal\n\nDo the thing.\n"
    write(spec_dir / "tasks" / filename, body)


def make_spec(spec_dir, groups=None):
    """Write a SPEC.md with an optional ## Parallelization section."""
    text = f"# {spec_dir.name}\n\nStatus: open\n\n## Solution\n\nStuff.\n"
    if groups:
        text += "\n## Parallelization\n\nRationale.\n\n"
        for g in groups:
            text += f"- Group: {g}\n"
    write(spec_dir / "SPEC.md", text)


def paths(entries):
    """Basenames of a frontier entry list, order preserved."""
    return [Path(e["path"]).name for e in entries]


def run_cli(*args):
    """Invoke the scanner as a subprocess; return (returncode, stdout, stderr)."""
    proc = subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


class DependencyGatingTestCase(unittest.TestCase):
    """A pending task with a non-done dependency is blocked, not dispatchable."""

    def test_pending_task_with_undone_dep_is_blocked_not_dispatchable(self):
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "s"
            make_spec(sd)
            make_task(sd, "01-a.md", status="pending", touch="src/a")
            make_task(sd, "02-b.md", status="pending", depends="01", touch="src/b")
            fr = drain_frontier.compute_frontier([str(sd)], None, [])
            self.assertNotIn("02-b.md", paths(fr["dispatchable"]))
            self.assertIn("02-b.md", paths(fr["blocked"]))

    def test_pending_task_with_done_dep_is_dispatchable(self):
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "s"
            make_spec(sd)
            make_task(sd, "01-a.md", status="done", touch="src/a")
            make_task(sd, "02-b.md", status="pending", depends="01", touch="src/b")
            fr = drain_frontier.compute_frontier([str(sd)], None, [])
            self.assertIn("02-b.md", paths(fr["dispatchable"]))


class OrderingTripleTestCase(unittest.TestCase):
    """dispatchable order = Priority, then unblocking-power, then lexicographic."""

    def test_lower_priority_number_sorts_first(self):
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "s"
            make_spec(sd)
            make_task(sd, "01-a.md", status="pending", priority="P3", touch="src/a")
            make_task(sd, "02-b.md", status="pending", priority="P1", touch="src/b")
            fr = drain_frontier.compute_frontier([str(sd)], None, [])
            self.assertEqual(paths(fr["dispatchable"]), ["02-b.md", "01-a.md"])

    def test_unblocking_power_breaks_priority_tie(self):
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "s"
            make_spec(sd)
            # Same priority; 01 unblocks two pending tasks, 02 unblocks none.
            make_task(sd, "01-a.md", status="pending", priority="P2", touch="src/a")
            make_task(sd, "02-b.md", status="pending", priority="P2", touch="src/b")
            make_task(sd, "03-c.md", status="pending", depends="01", touch="src/c")
            make_task(sd, "04-d.md", status="pending", depends="01", touch="src/d")
            fr = drain_frontier.compute_frontier([str(sd)], None, [])
            # 01 (power 2) precedes 02 (power 0) despite lexicographic tie loss.
            disp = paths(fr["dispatchable"])
            self.assertLess(disp.index("01-a.md"), disp.index("02-b.md"))

    def test_lexicographic_final_tie_break(self):
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "s"
            make_spec(sd)
            make_task(sd, "02-b.md", status="pending", priority="P2", touch="src/b")
            make_task(sd, "01-a.md", status="pending", priority="P2", touch="src/a")
            fr = drain_frontier.compute_frontier([str(sd)], None, [])
            self.assertEqual(paths(fr["dispatchable"]), ["01-a.md", "02-b.md"])


class TouchDisjointPerSpecTestCase(unittest.TestCase):
    """Touch disjointness gates admissible, computed per-spec not globally."""

    def test_touch_collision_keeps_task_dispatchable_but_out_of_admissible(self):
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "s"
            make_spec(sd)  # no groups: each ungrouped runs alone
            make_task(
                sd, "01-a.md", status="pending", priority="P1", touch="src/shared"
            )
            make_task(
                sd, "02-b.md", status="pending", priority="P2", touch="src/shared"
            )
            fr = drain_frontier.compute_frontier([str(sd)], None, [])
            # Both dispatchable; only the first (ungrouped, empty window) admits.
            self.assertEqual(sorted(paths(fr["dispatchable"])), ["01-a.md", "02-b.md"])
            self.assertEqual(paths(fr["admissible"]), ["01-a.md"])


class GroupCoAdmissibilityTestCase(unittest.TestCase):
    """- Group: predicate governs co-admission; ungrouped runs alone."""

    def test_grouped_disjoint_tasks_co_admit(self):
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "s"
            make_spec(sd, groups=["01, 02"])
            make_task(sd, "01-a.md", status="pending", priority="P1", touch="src/a")
            make_task(sd, "02-b.md", status="pending", priority="P1", touch="src/b")
            fr = drain_frontier.compute_frontier([str(sd)], None, [])
            self.assertEqual(sorted(paths(fr["admissible"])), ["01-a.md", "02-b.md"])

    def test_ungrouped_task_runs_alone(self):
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "s"
            make_spec(sd)  # no groups
            make_task(sd, "01-a.md", status="pending", priority="P1", touch="src/a")
            make_task(sd, "02-b.md", status="pending", priority="P1", touch="src/b")
            fr = drain_frontier.compute_frontier([str(sd)], None, [])
            self.assertEqual(len(fr["admissible"]), 1)


class ClaimedCollisionTestCase(unittest.TestCase):
    """--claimed filters Touch collisions only; no live-slot arithmetic."""

    def test_claimed_touch_collision_excludes_from_admissible(self):
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "s"
            make_spec(sd, groups=["01, 02"])
            make_task(sd, "01-a.md", status="pending", priority="P1", touch="src/a")
            make_task(sd, "02-b.md", status="pending", priority="P1", touch="src/b")
            claimed = Path(td) / "claim"
            make_spec(claimed)
            make_task(claimed, "09-x.md", status="in-progress", touch="src/a")
            claim_path = str(claimed / "tasks" / "09-x.md")
            fr = drain_frontier.compute_frontier([str(sd)], None, [claim_path])
            self.assertNotIn("01-a.md", paths(fr["admissible"]))
            self.assertIn("01-a.md", paths(fr["dispatchable"]))

    def test_admissible_is_min_window_candidates_not_reduced_by_claimed(self):
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "s"
            make_spec(sd, groups=["01, 02, 03"])
            make_task(sd, "01-a.md", status="pending", priority="P1", touch="src/a")
            make_task(sd, "02-b.md", status="pending", priority="P1", touch="src/b")
            make_task(sd, "03-c.md", status="pending", priority="P1", touch="src/c")
            claimed = Path(td) / "claim"
            make_spec(claimed)
            # claim touches something disjoint from all candidates
            make_task(claimed, "09-x.md", status="in-progress", touch="other/z")
            claim_path = str(claimed / "tasks" / "09-x.md")
            fr = drain_frontier.compute_frontier([str(sd)], 2, [claim_path])
            # length is min(2, 3) == 2, NOT 2 - 1 == 1
            self.assertEqual(len(fr["admissible"]), 2)


class GlobPrefixPredicateTestCase(unittest.TestCase):
    """literal-prefix conflict predicate: overlap, no-overlap, ambiguous."""

    def test_overlapping_glob_prefixes_conflict(self):
        self.assertFalse(
            drain_frontier.entries_disjoint({"src/pkg/**"}, {"src/pkg/mod.py"})
        )

    def test_non_overlapping_prefixes_are_disjoint(self):
        self.assertTrue(drain_frontier.entries_disjoint({"src/a/**"}, {"src/b/**"}))

    def test_ambiguous_glob_resolves_conservatively_to_conflict(self):
        # One entry is a bare glob whose literal prefix is a prefix of the other.
        self.assertFalse(
            drain_frontier.entries_disjoint({"src/*"}, {"src/deep/thing.py"})
        )


class UnresolvedExternalDepTestCase(unittest.TestCase):
    """A dep outside the scanned spec set lands in blocked, never guessed done."""

    def test_cross_spec_path_dep_outside_scan_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "s"
            make_spec(sd)
            make_task(
                sd,
                "01-a.md",
                status="pending",
                depends="../../other/tasks/07-z.md",
                touch="src/a",
            )
            fr = drain_frontier.compute_frontier([str(sd)], None, [])
            self.assertNotIn("01-a.md", paths(fr["dispatchable"]))
            self.assertIn("01-a.md", paths(fr["blocked"]))
            blob = json.dumps(fr)
            self.assertIn("unresolved-external-dep", blob)


class ParseSemanticsTestCase(unittest.TestCase):
    """Defaulted headers exit 0 w/ diagnostics; malformed Status exits non-zero."""

    def test_missing_status_defaults_pending_exit_zero(self):
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "s"
            make_spec(sd)
            make_task(sd, "01-a.md", status=None, touch="src/a")  # no Status line
            fr = drain_frontier.compute_frontier([str(sd)], None, [])
            self.assertIn("01-a.md", paths(fr["dispatchable"]))
            self.assertIn("Status", json.dumps(fr["diagnostics"]))

    def test_missing_priority_defaults_p2_recorded_in_diagnostics(self):
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "s"
            make_spec(sd)
            make_task(sd, "01-a.md", status="pending", priority=None, touch="src/a")
            fr = drain_frontier.compute_frontier([str(sd)], None, [])
            self.assertEqual(fr["dispatchable"][0]["priority"], "P2")

    def test_malformed_status_exits_nonzero_via_cli(self):
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "s"
            make_spec(sd)
            make_task(sd, "01-a.md", status="frobnicate", touch="src/a")
            rc, out, err = run_cli(str(sd))
            self.assertNotEqual(rc, 0)
            self.assertIn("frobnicate", err)

    def test_malformed_status_raises_in_process(self):
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "s"
            make_spec(sd)
            make_task(sd, "01-a.md", status="frobnicate", touch="src/a")
            with self.assertRaises(drain_frontier.FrontierError):
                drain_frontier.compute_frontier([str(sd)], None, [])

    def test_defaulted_headers_exit_zero_via_cli(self):
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "s"
            make_spec(sd)
            make_task(sd, "01-a.md", status=None, touch="src/a")
            rc, out, err = run_cli(str(sd))
            self.assertEqual(rc, 0)
            json.loads(out)  # valid JSON on stdout


class WindowTruncationTestCase(unittest.TestCase):
    """--window N truncates admissible only; dispatchable is never truncated."""

    def test_window_truncates_admissible_not_dispatchable(self):
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "s"
            make_spec(sd, groups=["01, 02, 03"])
            make_task(sd, "01-a.md", status="pending", priority="P1", touch="src/a")
            make_task(sd, "02-b.md", status="pending", priority="P1", touch="src/b")
            make_task(sd, "03-c.md", status="pending", priority="P1", touch="src/c")
            fr = drain_frontier.compute_frontier([str(sd)], 2, [])
            self.assertEqual(len(fr["admissible"]), 2)
            self.assertEqual(len(fr["dispatchable"]), 3)


class ExcludedStatusTestCase(unittest.TestCase):
    """blocked / deferred / needs-verification never appear in dispatchable."""

    def test_non_pending_statuses_excluded_from_dispatchable(self):
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "s"
            make_spec(sd)
            make_task(sd, "01-a.md", status="deferred", touch="src/a")
            make_task(sd, "02-b.md", status="needs-verification", touch="src/b")
            make_task(
                sd, "03-c.md", status="blocked", unblock="run: echo hi", touch="src/c"
            )
            make_task(sd, "04-d.md", status="pending", touch="src/d")
            fr = drain_frontier.compute_frontier([str(sd)], None, [])
            disp = paths(fr["dispatchable"])
            self.assertEqual(disp, ["04-d.md"])
            self.assertIn("03-c.md", paths(fr["blocked"]))


class GoldenFixtureTestCase(unittest.TestCase):
    """The committed fixture emits the documented admissible under --window 2."""

    def test_basic_window_fixture_admissible_matches_expectation(self):
        fixture = _SCRIPT.parent / "fixtures" / "basic-window"
        if not fixture.is_dir():
            self.skipTest("golden fixture not present")
        rc, out, err = run_cli(str(fixture), "--window", "2")
        self.assertEqual(rc, 0, err)
        fr = json.loads(out)
        self.assertEqual(paths(fr["admissible"]), ["02-alpha.md", "03-beta.md"])


if __name__ == "__main__":
    unittest.main()
