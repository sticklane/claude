"""Tests for prioritize_scan.py: scan + filter + priority-parse + render.

Run: python3 -m pytest .agents/skills/prioritize/test_prioritize_scan.py -q
or:  python3 -m unittest discover -s .agents/skills/prioritize

Stdlib-only, like workboard.py / list_specs.py. Each test builds a real
specs/ tree under a tmp dir and calls the script's functions directly — no
mocking. Assertions parse the rendered structure rather than pinning exact
whole-output strings.
"""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent / "prioritize_scan.py"
_spec = importlib.util.spec_from_file_location("prioritize_scan", _SCRIPT)
prioritize_scan = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prioritize_scan)


def find_repo_root():
    """Walk up from this file to the first directory containing .git.

    Location-independent on purpose (mirrors list_specs' test): this file is
    byte-copied into the antigravity mirror one directory deeper, so a fixed
    parent count would resolve to the wrong root there.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("no .git directory found above test file")


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_spec_md(root, slug, status=None, priority=None, title=None):
    header = ""
    if status is not None:
        header += f"Status: {status}\n"
    if priority is not None:
        header += f"Priority: {priority}\n"
    write(
        root / "specs" / slug / "SPEC.md",
        f"# {title or slug}\n\n{header}\n## Goal\n\nx\n",
    )


def make_task(root, slug, filename, status="pending", priority=None, title=None):
    """Write a task file. status=None omits the Status: header entirely
    (scanner then defaults it to 'pending'); priority=None omits Priority:."""
    header = ""
    if status is not None:
        header += f"Status: {status}\n"
    if priority is not None:
        header += f"Priority: {priority}\n"
    body = f"# {title or filename}\n\n{header}\n## Goal\n\nDo the thing.\n"
    write(root / "specs" / slug / "tasks" / filename, body)


def parse_rows(table):
    """Parse a rendered markdown table into a list of {ref,title,status,
    priority} dicts, skipping the header + separator rows."""
    rows = []
    for line in table.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells[0] in ("Ref", "---") or set(cells[0]) == {"-"}:
            continue
        rows.append(
            {
                "ref": cells[0],
                "title": cells[1],
                "status": cells[2],
                "priority": cells[3],
            }
        )
    return rows


class CollectTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_zero_qualifying_tasks_collects_nothing(self):
        make_spec_md(self.root, "foo")
        make_task(self.root, "foo", "01-a.md", status="done")
        make_task(self.root, "foo", "02-b.md", status="in-progress")
        self.assertEqual(prioritize_scan.collect(self.root), [])

    def test_only_pending_blocked_deferred_draft_are_collected(self):
        make_spec_md(self.root, "foo")
        make_task(self.root, "foo", "01-pending.md", status="pending")
        make_task(self.root, "foo", "02-blocked.md", status="blocked")
        make_task(self.root, "foo", "03-deferred.md", status="deferred")
        make_task(self.root, "foo", "04-done.md", status="done")
        make_task(self.root, "foo", "05-skipped.md", status="skipped")
        make_task(self.root, "foo", "06-inprogress.md", status="in-progress")
        make_task(self.root, "foo", "07-inprogress2.md", status="in_progress")
        make_task(self.root, "foo", "08-claimed.md", status="claimed")
        make_task(self.root, "foo", "09-draft.md", status="draft")
        make_task(self.root, "foo", "10-failed.md", status="failed")
        rows = prioritize_scan.collect(self.root)
        statuses = sorted(r["status"] for r in rows)
        self.assertEqual(statuses, ["blocked", "deferred", "draft", "pending"])

    def test_spec_with_no_tasks_dir_gets_spec_md_fallback_row(self):
        make_spec_md(self.root, "no-tasks-yet", title="No Tasks Yet")
        rows = prioritize_scan.collect(self.root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["ref"], "no-tasks-yet/SPEC.md")
        self.assertEqual(rows[0]["title"], "No Tasks Yet")
        self.assertEqual(rows[0]["status"], "open")
        self.assertEqual(rows[0]["priority"], "P2 (default)")

    def test_spec_md_fallback_row_reads_its_own_status_and_priority(self):
        make_spec_md(self.root, "no-tasks-yet", status="blocked", priority="P1")
        rows = prioritize_scan.collect(self.root)
        self.assertEqual(rows[0]["status"], "blocked")
        self.assertEqual(rows[0]["priority"], "P1")

    def test_done_task_less_spec_gets_no_fallback_row(self):
        make_spec_md(self.root, "finished", status="done")
        self.assertEqual(prioritize_scan.collect(self.root), [])

    def test_skipped_task_less_spec_gets_no_fallback_row(self):
        make_spec_md(self.root, "shelved", status="skipped")
        self.assertEqual(prioritize_scan.collect(self.root), [])

    def test_ref_is_slug_slash_filename(self):
        make_spec_md(self.root, "my-spec")
        make_task(self.root, "my-spec", "03-worker.md", status="pending")
        rows = prioritize_scan.collect(self.root)
        self.assertEqual(rows[0]["ref"], "my-spec/03-worker.md")

    def test_rows_sorted_by_spec_slug_then_task_number(self):
        make_spec_md(self.root, "zeta")
        make_spec_md(self.root, "alpha")
        make_task(self.root, "zeta", "01-z.md", status="pending")
        make_task(self.root, "alpha", "10-late.md", status="pending")
        make_task(self.root, "alpha", "02-early.md", status="blocked")
        rows = prioritize_scan.collect(self.root)
        refs = [r["ref"] for r in rows]
        self.assertEqual(
            refs, ["alpha/02-early.md", "alpha/10-late.md", "zeta/01-z.md"]
        )

    def test_task_with_priority_header_shows_that_value(self):
        make_spec_md(self.root, "foo")
        make_task(self.root, "foo", "01-a.md", status="pending", priority="P0")
        rows = prioritize_scan.collect(self.root)
        self.assertEqual(rows[0]["priority"], "P0")

    def test_task_without_priority_header_shows_default(self):
        make_spec_md(self.root, "foo")
        make_task(self.root, "foo", "01-a.md", status="pending", priority=None)
        rows = prioritize_scan.collect(self.root)
        self.assertEqual(rows[0]["priority"], "P2 (default)")

    def test_headerless_task_counts_as_pending_and_is_listed(self):
        make_spec_md(self.root, "foo")
        make_task(self.root, "foo", "01-noheader.md", status=None)
        rows = prioritize_scan.collect(self.root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "pending")
        self.assertEqual(rows[0]["ref"], "foo/01-noheader.md")

    def test_archive_specs_are_excluded(self):
        make_spec_md(self.root, "foo")
        make_task(self.root, "foo", "01-a.md", status="pending")
        make_spec_md(self.root, "archive/old-one")
        make_task(self.root, "archive/old-one", "01-old.md", status="pending")
        rows = prioritize_scan.collect(self.root)
        refs = [r["ref"] for r in rows]
        self.assertEqual(refs, ["foo/01-a.md"])
        self.assertFalse(any("archive" in r for r in refs))


class RenderTestCase(unittest.TestCase):
    def test_empty_rows_render_nothing_to_reprioritize(self):
        out = prioritize_scan.render([])
        self.assertEqual(out.strip(), "nothing to reprioritize")
        self.assertNotIn("|", out)

    def test_nonempty_rows_render_table_with_expected_columns(self):
        rows = [
            {
                "ref": "foo/01-a.md",
                "title": "A",
                "status": "pending",
                "priority": "P2 (default)",
            },
        ]
        out = prioritize_scan.render(rows)
        parsed = parse_rows(out)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["ref"], "foo/01-a.md")
        self.assertEqual(parsed[0]["priority"], "P2 (default)")
        # header names present
        self.assertIn("Ref", out)
        self.assertIn("Title", out)
        self.assertIn("Status", out)
        self.assertIn("Priority", out)


class CliSubprocessTestCase(unittest.TestCase):
    def test_zero_qualifying_prints_nothing_to_reprioritize(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_spec_md(root, "foo")
            make_task(root, "foo", "01-a.md", status="done")
            result = subprocess.run(
                [sys.executable, str(_SCRIPT)],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=30,
            )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("nothing to reprioritize", result.stdout)
        self.assertNotIn("|", result.stdout)

    def test_fixture_prints_table_only_qualifying_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_spec_md(root, "foo")
            make_task(root, "foo", "01-a.md", status="pending", priority="P1")
            make_task(root, "foo", "02-b.md", status="done")
            result = subprocess.run(
                [sys.executable, str(_SCRIPT)],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=30,
            )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        rows = parse_rows(result.stdout)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["ref"], "foo/01-a.md")
        self.assertEqual(rows[0]["priority"], "P1")

    def test_this_repo_runs_clean_and_excludes_archive(self):
        repo_root = find_repo_root()
        result = subprocess.run(
            [sys.executable, str(_SCRIPT)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotIn("archive/", result.stdout)


if __name__ == "__main__":
    unittest.main()
