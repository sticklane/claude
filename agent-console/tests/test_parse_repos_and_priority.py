"""Coverage for two gaps the mutation-endpoints spec left open (agentic-69n):

- `parse_repos()` was only ever mocked (test_parsers.py patches it), never
  exercised directly — so its REPOS.md table parsing, `~` expansion,
  dedup, and drop-nonexistent-dir filtering were untested.
- `apply_priority()`'s insert-after-H1 branch (no `Priority:` AND no `Status:`
  header) had no test — only the replace-existing and insert-under-Status
  branches were covered in test_parsers.py's TestPriority.

Pure/filesystem tests only: no server, no network, no `claude`/`gh`.
"""

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_spec = importlib.util.spec_from_file_location(
    "ac", str(Path(__file__).resolve().parent.parent / "agent-console.py")
)
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)


class TestParseRepos(unittest.TestCase):
    """Drive the real REPOS.md table parser against a temp file + temp dirs,
    with `~` expansion redirected into the temp root so `.is_dir()` is real."""

    def _run(self, root: Path, body: str):
        repos_md = root / "REPOS.md"
        repos_md.write_text(body, encoding="utf-8")

        def fake_expand(p):
            return p.replace("~", str(root), 1) if p.startswith("~") else p

        with (
            patch.object(ac, "REPOS_MD", repos_md),
            patch.object(ac.os.path, "expanduser", side_effect=fake_expand),
        ):
            return ac.parse_repos()

    def test_parses_table_rows_keeping_only_existing_dirs_in_order(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "alpha").mkdir()
            (root / "beta").mkdir()
            # 'gamma' intentionally not created -> filtered out (not a dir).
            out = self._run(
                root,
                "| Repo | Notes |\n"
                "|------|-------|\n"
                "| ~/alpha | a |\n"
                "| ~/beta | b |\n"
                "| ~/gamma | missing, dropped |\n",
            )
            self.assertEqual([p.name for p in out], ["alpha", "beta"])

    def test_dedups_repeated_rows(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "alpha").mkdir()
            out = self._run(
                root,
                "| ~/alpha | first |\n| ~/alpha | duplicate row |\n",
            )
            self.assertEqual(len(out), 1)
            self.assertEqual(out[0].name, "alpha")

    def test_ignores_non_table_and_non_tilde_lines(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "alpha").mkdir()
            out = self._run(
                root,
                "# a heading\n"
                "some prose, not a row\n"
                "| /abs/path | leading slash, not a ~ row |\n"
                "| ~/alpha | kept |\n",
            )
            self.assertEqual([p.name for p in out], ["alpha"])

    def test_missing_repos_md_yields_empty_list(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            missing = root / "nope" / "REPOS.md"
            with patch.object(ac, "REPOS_MD", missing):
                self.assertEqual(ac.parse_repos(), [])


class TestApplyPriorityInsertAfterH1(unittest.TestCase):
    """The branch used when a spec has an H1 title but neither a `Priority:`
    nor a `Status:` line — the priority is inserted a blank line below the H1."""

    def test_inserts_priority_after_h1_when_no_status(self):
        out = ac.apply_priority("# My Spec\n\nbody text\n", "P3")
        self.assertRegex(out, r"^# My Spec\n\nPriority: P3\n")
        self.assertIn("body text", out)
        # exactly one Priority line was introduced
        self.assertEqual(out.count("Priority: P3"), 1)

    def test_h1_branch_does_not_fire_when_status_present(self):
        # Sanity guard: with a Status line, the priority attaches under Status,
        # never after the H1 — keeps this test distinct from the Status branch.
        out = ac.apply_priority("# My Spec\n\nStatus: ready\n", "P1")
        self.assertRegex(out, r"Status: ready\nPriority: P1")


if __name__ == "__main__":
    unittest.main()
