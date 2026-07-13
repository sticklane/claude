"""Tests for list_specs.py: scan + bucket + classify + render.

Run: python3 -m unittest discover -s .agents/skills/list-specs
or:  pytest .agents/skills/list-specs/test_list_specs.py -v

Stdlib-only, like workboard.py. Each test builds a real specs/ tree under a
tmp dir (tempfile.TemporaryDirectory) and calls the script's functions
directly — no mocking.
"""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent / "list_specs.py"
_spec = importlib.util.spec_from_file_location("list_specs", _SCRIPT)
list_specs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(list_specs)


def find_repo_root():
    """Walk up from this file to the first directory containing .git.

    Location-independent on purpose: this file is byte-copied into the
    antigravity mirror one directory deeper, so a fixed parent count
    would resolve to the wrong root there.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("no .git directory found above test file")


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_spec_md(root, slug, open_questions_body="(none)"):
    write(
        root / "specs" / slug / "SPEC.md",
        f"# {slug}\n\n## Open questions\n\n{open_questions_body}\n",
    )


def make_task(root, slug, filename, status=None, title=None):
    body = f"# {title or filename}\n\n"
    if status is not None:
        body += f"Status: {status}\n\n"
    body += "## Goal\n\nDo the thing.\n"
    write(root / "specs" / slug / "tasks" / filename, body)


class ClassifySpecTestCase(unittest.TestCase):
    """Exercises classify_spec() (R3+R4) directly against constructed task
    dicts, mirroring the shape scan_toolkit_specs() produces."""

    def _tasks(self, statuses):
        return [{"file": f"t{i}.md", "status": s} for i, s in enumerate(statuses)]

    def test_no_tasks_dir_with_unresolved_open_questions_suggests_critique(self):
        row = list_specs.classify_spec("foo", tasks=[], open_questions_unresolved=True)
        self.assertEqual(row["next_command"], "/critique specs/foo/SPEC.md")

    def test_no_tasks_dir_with_resolved_open_questions_suggests_breakdown(self):
        row = list_specs.classify_spec("foo", tasks=[], open_questions_unresolved=False)
        self.assertEqual(row["next_command"], "/breakdown specs/foo/SPEC.md")

    def test_empty_tasks_dir_same_as_no_tasks_dir(self):
        row = list_specs.classify_spec("foo", tasks=[], open_questions_unresolved=False)
        self.assertEqual(row["next_command"], "/breakdown specs/foo/SPEC.md")
        self.assertIn("no tasks/", row["status"])

    def test_two_pending_one_done_suggests_drain(self):
        row = list_specs.classify_spec(
            "foo",
            tasks=self._tasks(["pending", "pending", "done"]),
            open_questions_unresolved=False,
        )
        self.assertEqual(row["next_command"], "/drain specs/foo")

    def test_exactly_one_pending_suggests_build_with_task_file(self):
        tasks = [{"file": "specs/foo/tasks/03-foo.md", "status": "pending"}]
        row = list_specs.classify_spec(
            "foo", tasks=tasks, open_questions_unresolved=False
        )
        self.assertEqual(row["next_command"], "/build specs/foo/tasks/03-foo.md")

    def test_deferred_plus_two_pending_suggests_drain_deferred_precedence(self):
        row = list_specs.classify_spec(
            "foo",
            tasks=self._tasks(["deferred", "pending", "pending"]),
            open_questions_unresolved=False,
        )
        self.assertEqual(row["next_command"], "/drain specs/foo")

    def test_blocked_plus_two_pending_flags_blocked_no_command(self):
        row = list_specs.classify_spec(
            "foo",
            tasks=self._tasks(["blocked", "pending", "pending"]),
            open_questions_unresolved=False,
        )
        self.assertIsNone(row["next_command"])
        self.assertIn("blocked/failed", row["status"])

    def test_agent_unblockable_blocked_does_not_flag_needs_attention(self):
        # Agent-bounded blockage (Unblock: run/agent) proceeds — the spec
        # routes to /drain instead of halting for the human.
        tasks = [
            {
                "file": "specs/foo/tasks/01-a.md",
                "status": "blocked",
                "unblock": {"type": "agent", "step": "recheck the deploy"},
            },
            {"file": "specs/foo/tasks/02-b.md", "status": "pending"},
            {"file": "specs/foo/tasks/03-c.md", "status": "pending"},
        ]
        row = list_specs.classify_spec(
            "foo", tasks=tasks, open_questions_unresolved=False
        )
        self.assertNotIn("needs attention", row["status"])
        self.assertEqual(row["next_command"], "/drain specs/foo")

    def test_ask_unblock_blocked_still_flags_needs_attention(self):
        tasks = [
            {
                "file": "specs/foo/tasks/01-a.md",
                "status": "blocked",
                "unblock": {"type": "ask", "step": "which creds?"},
            },
            {"file": "specs/foo/tasks/02-b.md", "status": "pending"},
        ]
        row = list_specs.classify_spec(
            "foo", tasks=tasks, open_questions_unresolved=False
        )
        self.assertIsNone(row["next_command"])
        self.assertIn("needs attention", row["status"])

    def test_only_agent_unblockable_blocked_left_suggests_drain(self):
        tasks = [
            {
                "file": "specs/foo/tasks/01-a.md",
                "status": "blocked",
                "unblock": {"type": "run", "step": "make recheck"},
            },
            {"file": "specs/foo/tasks/02-b.md", "status": "done"},
        ]
        row = list_specs.classify_spec(
            "foo", tasks=tasks, open_questions_unresolved=False
        )
        self.assertEqual(row["next_command"], "/drain specs/foo")

    def test_deferred_plus_blocked_no_pending_suggests_drain_rule3_over_rule4(self):
        row = list_specs.classify_spec(
            "foo",
            tasks=self._tasks(["deferred", "blocked"]),
            open_questions_unresolved=False,
        )
        self.assertEqual(row["next_command"], "/drain specs/foo")

    def test_all_claimed_in_progress_flags_in_progress_no_command(self):
        row = list_specs.classify_spec(
            "foo",
            tasks=self._tasks(["claimed", "in-progress"]),
            open_questions_unresolved=False,
        )
        self.assertIsNone(row["next_command"])
        self.assertIn("in-progress/awaiting", row["status"])

    def test_all_done_plus_one_draft_flags_drafts_ready(self):
        row = list_specs.classify_spec(
            "foo",
            tasks=self._tasks(["done", "done", "draft"]),
            open_questions_unresolved=False,
        )
        self.assertIsNone(row["next_command"])
        self.assertIn("drafts ready for promotion", row["status"])

    def test_all_done_no_drafts_suggests_distill(self):
        row = list_specs.classify_spec(
            "foo",
            tasks=self._tasks(["done", "skipped"]),
            open_questions_unresolved=False,
        )
        self.assertEqual(row["next_command"], "/distill")

    def test_missing_status_header_counts_as_pending_like(self):
        # Two "pending_like" tasks (one via missing header) -> /drain, proving
        # the no-header task counted toward the pending bucket.
        tasks = [
            {"file": "a.md", "status": "pending"},
            {"file": "b.md", "status": "pending"},
        ]
        row = list_specs.classify_spec(
            "foo", tasks=tasks, open_questions_unresolved=False
        )
        self.assertEqual(row["next_command"], "/drain specs/foo")

    def test_one_unrecognized_status_flags_unrecognized_no_command(self):
        row = list_specs.classify_spec(
            "foo", tasks=self._tasks(["wat"]), open_questions_unresolved=False
        )
        self.assertIsNone(row["next_command"])
        self.assertIn("unrecognized task status", row["status"])

    def test_draft_plus_unrecognized_flags_unrecognized_rule10_over_rule8(self):
        row = list_specs.classify_spec(
            "foo", tasks=self._tasks(["draft", "wat"]), open_questions_unresolved=False
        )
        self.assertIsNone(row["next_command"])
        self.assertIn("unrecognized task status", row["status"])
        self.assertNotIn("drafts ready for promotion", row["status"])

    def test_no_tasks_open_questions_exactly_none_suggests_breakdown(self):
        row = list_specs.classify_spec("foo", tasks=[], open_questions_unresolved=False)
        self.assertEqual(row["next_command"], "/breakdown specs/foo/SPEC.md")


class BucketTaskStatusTestCase(unittest.TestCase):
    """R3 bucketing of raw status strings into disjoint categories."""

    def test_pending_like_statuses(self):
        for s in ("pending", "open", "todo", "ready"):
            self.assertEqual(list_specs.bucket_status(s), "pending_like")

    def test_in_progress_like_statuses(self):
        for s in ("in-progress", "in_progress", "claimed"):
            self.assertEqual(list_specs.bucket_status(s), "in_progress_like")

    def test_deferred_status(self):
        self.assertEqual(list_specs.bucket_status("deferred"), "deferred")

    def test_blocked_or_failed_statuses(self):
        for s in ("blocked", "failed"):
            self.assertEqual(list_specs.bucket_status(s), "blocked_or_failed")

    def test_draft_status(self):
        self.assertEqual(list_specs.bucket_status("draft"), "draft")

    def test_done_like_statuses(self):
        for s in ("done", "skipped"):
            self.assertEqual(list_specs.bucket_status(s), "done_like")

    def test_unrecognized_status(self):
        self.assertEqual(list_specs.bucket_status("wat"), "unrecognized")


class EndToEndFixtureTestCase(unittest.TestCase):
    """Builds real specs/ trees under a tmp dir and drives main()/scan
    end-to-end, matching the acceptance list's fixture scenarios."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_no_specs_dir_prints_message_and_exits_0(self):
        with self.assertRaises(SystemExit) as ctx:
            list_specs.run(self.root)
        self.assertEqual(ctx.exception.code, 0)

    def test_archive_only_repo_has_zero_data_rows(self):
        make_spec_md(self.root, "archive/old-one")
        rows = list_specs.scan_and_classify(self.root)
        self.assertEqual(rows, [])

    def test_tasks_dir_present_but_empty_same_as_no_tasks_dir(self):
        make_spec_md(self.root, "foo", open_questions_body="(none)")
        (self.root / "specs" / "foo" / "tasks").mkdir(parents=True)
        rows = list_specs.scan_and_classify(self.root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["next_command"], "/breakdown specs/foo/SPEC.md")

    def test_real_prose_open_questions_suggests_critique(self):
        make_spec_md(
            self.root,
            "foo",
            open_questions_body="Should we use approach A or B? Undecided.",
        )
        rows = list_specs.scan_and_classify(self.root)
        self.assertEqual(rows[0]["next_command"], "/critique specs/foo/SPEC.md")

    def test_rows_sorted_alphabetically_by_slug(self):
        make_spec_md(self.root, "zeta")
        make_spec_md(self.root, "alpha")
        rows = list_specs.scan_and_classify(self.root)
        self.assertEqual([r["slug"] for r in rows], ["alpha", "zeta"])

    def test_render_table_has_expected_columns_and_no_archive_rows(self):
        make_spec_md(self.root, "archive/old-one")
        make_spec_md(self.root, "foo")
        rows = list_specs.scan_and_classify(self.root)
        table = list_specs.render_table(rows)
        self.assertIn("| Spec | Status | Next command |", table)
        self.assertIn("foo", table)
        self.assertNotIn("archive", table)


class CliSubprocessTestCase(unittest.TestCase):
    """Smoke-tests the script as a subprocess against real tmp-dir cwds,
    matching the acceptance criteria's exact invocations."""

    def test_no_specs_dir_prints_message_and_exits_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(_SCRIPT)],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=30,
            )
        self.assertEqual(result.returncode, 0)
        self.assertIn("no specs/", result.stdout.lower())

    def test_this_repo_produces_table_no_archive_rows_no_crash(self):
        repo_root = find_repo_root()
        result = subprocess.run(
            [sys.executable, str(_SCRIPT)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("| Spec | Status | Next command |", result.stdout)
        self.assertNotIn("archive/", result.stdout)


if __name__ == "__main__":
    unittest.main()
