"""Unit tests for pure parse/transform functions — no network, no server.

Run by scripts/check.sh. Seeded here for the supported-cli-migration spec
(enabled-filter + CLI parsing); the parser-unit-tests spec expands coverage.
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


class TestPluginCliParsing(unittest.TestCase):
    def test_enabled_filter_drops_disabled_plugins(self):
        data = [
            {
                "id": "agentic@agentic-toolkit",
                "enabled": True,
                "installPath": str(Path.home()),
            },
            {
                "id": "auto-memory@marketplace",
                "enabled": False,
                "installPath": str(Path.home()),
            },
        ]
        out = ac.plugin_paths_from_cli(data)
        labels = [label for label, _ in out]
        self.assertIn("agentic", labels)
        self.assertNotIn("auto-memory", labels)  # disabled → excluded

    def test_skips_missing_installpath_and_bad_shapes(self):
        data = [
            {"id": "x@m", "enabled": True, "installPath": "/no/such/dir/xyz123"},
            {"id": "y@m", "enabled": True},  # no installPath
            "not-a-dict",
        ]
        self.assertEqual(ac.plugin_paths_from_cli(data), [])

    def test_returns_none_on_wrong_shape(self):
        self.assertIsNone(ac.plugin_paths_from_cli({"plugins": []}))
        self.assertIsNone(ac.plugin_paths_from_cli(None))


class TestAgentsCliParsing(unittest.TestCase):
    def test_parses_live_sessions(self):
        data = [
            {
                "sessionId": "abc",
                "cwd": "/repo",
                "name": "s1",
                "startedAt": 1783139484428,
            },
            {"sessionId": "", "cwd": "/x"},  # no sid → skipped
            {"cwd": "/y"},  # no sid → skipped
        ]
        out = ac.live_sessions_from_cli(data)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["sid"], "abc")
        self.assertEqual(out[0]["cwd"], "/repo")
        self.assertGreater(out[0]["last"], 1e9)  # epoch-ms parsed to epoch-sec

    def test_returns_none_on_wrong_shape(self):
        self.assertIsNone(ac.live_sessions_from_cli({"agents": []}))
        self.assertIsNone(ac.live_sessions_from_cli(None))


class TestGhSlug(unittest.TestCase):
    def test_https_ssh_and_non_github(self):
        self.assertEqual(ac._gh_slug("https://github.com/o/r.git"), "o/r")
        self.assertEqual(ac._gh_slug("git@github.com:o/r.git"), "o/r")
        self.assertEqual(ac._gh_slug("https://gitlab.com/o/r.git"), "")
        self.assertEqual(ac._gh_slug(None), "")


class TestIso(unittest.TestCase):
    def test_ms_int_iso_str_and_junk(self):
        self.assertAlmostEqual(ac._iso(1783172065122), 1783172065.122, places=2)
        self.assertGreater(ac._iso("2026-01-08T14:59:47.651Z"), 1e9)
        self.assertEqual(ac._iso("junk"), 0.0)
        self.assertEqual(ac._iso(None), 0.0)


class TestFrontmatter(unittest.TestCase):
    def test_folds_multiline_description(self):
        fm = ac._parse_frontmatter(
            "---\nname: x\ndescription: line one\n  line two\n---\nbody"
        )
        self.assertEqual(fm["name"], "x")
        self.assertIn("line one", fm["description"])
        self.assertIn("line two", fm["description"])

    def test_no_frontmatter(self):
        self.assertEqual(ac._parse_frontmatter("# just a heading"), {})


class TestDepGraph(unittest.TestCase):
    # Renders via the vendored viz.dag() now (_dep_graph_svg/_task_stroke were
    # deleted in favor of the shared module); still test our usage.
    def test_cyclic_deps_do_not_hang(self):
        tasks = [
            {"num": "01", "title": "a", "status": "open", "deps": ["02"]},
            {"num": "02", "title": "b", "status": "open", "deps": ["01"]},
        ]
        svg = ac.viz.dag(tasks)  # must return, not hang
        self.assertIn("<svg", svg)

    def test_no_edges_returns_empty(self):
        tasks = [{"num": "01", "title": "a", "status": "open", "deps": []}]
        self.assertEqual(ac.viz.dag(tasks), "")


class TestDagTasksAdapter(unittest.TestCase):
    def test_maps_workboard_task_shape_to_viz_dag_shape(self):
        tasks = [
            {"file": "tasks/01-a.md", "abs": "/r/tasks/01-a.md", "title": "A",
             "status": "done", "deps": []},
            {"file": "tasks/02-b.md", "abs": "/r/tasks/02-b.md", "title": "B",
             "status": "pending", "deps": ["01"]},
        ]
        out = ac._dag_tasks(tasks)
        self.assertEqual(out[0], {"num": 1, "deps": [], "status": "done", "title": "A"})
        self.assertEqual(out[1], {"num": 2, "deps": [1], "status": "pending", "title": "B"})

    def test_skips_unparseable_filenames(self):
        tasks = [{"file": "tasks/notes.md", "abs": "/r/tasks/notes.md",
                  "title": "Notes", "status": "pending", "deps": []}]
        self.assertEqual(ac._dag_tasks(tasks), [])


class TestAdaptBoard(unittest.TestCase):
    """R4: workboard.assemble()'s result shape -> render_workboard's board
    shape, including the inbox field rename (severity/state/what/why/cmd/
    repo/age_ts -> sev/state/item/why/cmd/repo/age)."""

    def _assembled(self):
        return {
            "repos": [
                {
                    "path": "/tmp/nonexistent-repo-xyz",
                    "name": "r1",
                    "git": {"branch": "main", "dirty": 2, "ahead": 1, "behind": 0},
                    "specs": [
                        {
                            "kind": "toolkit",
                            "slug": "s1",
                            "title": "Spec One",
                            "path": "specs/s1/SPEC.md",
                            "tasks_total": 2,
                            "tasks_done": 1,
                            "tasks": [],
                            "last_touched": 100.0,
                        }
                    ],
                    "handoffs": [{"title": "H", "path": "HANDOFF.md", "mtime": 5.0}],
                    "sessions": [
                        {
                            "id": "sid1",
                            "cwd": "/tmp/nonexistent-repo-xyz",
                            "branch": "main",
                            "prompt": "do x",
                            "last_ts": 10.0,
                            "start_ts": 1.0,
                            "end_ts": 10.0,
                            "bytes": 1,
                            "state": "active",
                        }
                    ],
                }
            ],
            "orphan_sessions": [
                {
                    "id": "sid2",
                    "cwd": "/somewhere/else",
                    "branch": "",
                    "prompt": "orphaned",
                    "last_ts": 20.0,
                    "start_ts": 15.0,
                    "end_ts": 20.0,
                    "bytes": 1,
                    "state": "recent",
                }
            ],
            "inbox": [
                {
                    "severity": "warning",
                    "state": "needs-review",
                    "repo": "r1",
                    "what": "2 uncommitted change(s), no live session",
                    "why": "on branch main — commit or stash",
                    "age_ts": 3.0,
                }
            ],
            "liveness_unknown": False,
        }

    def test_adapts_repos_specs_sessions_and_inbox(self):
        with patch.object(ac, "gh_visibility", return_value={}), patch.object(
            ac, "_git", return_value=None
        ):
            board = ac._adapt_board(self._assembled(), [], [])

        self.assertEqual(board["n_repos"], 1)
        self.assertEqual(board["n_open_specs"], 1)
        self.assertEqual(board["n_active"], 1)
        self.assertEqual(board["actives"][0]["repo"], "r1")

        r1 = board["repos"][0]
        self.assertEqual(r1["name"], "r1")
        self.assertEqual(r1["git"]["dirty"], 2)
        self.assertEqual(r1["specs"][0]["slug"], "s1")
        self.assertEqual(r1["specs"][0]["done"], 1)
        self.assertEqual(r1["handoffs"][0]["title"], "H")
        self.assertEqual(r1["sessions"][0]["sid"], "sid1")

        inbox = board["inbox"][0]
        self.assertEqual(inbox["sev"], "warning")
        self.assertEqual(inbox["item"], "2 uncommitted change(s), no live session")
        self.assertEqual(inbox["repo"], "r1")
        self.assertEqual(inbox["age"], 3.0)

        self.assertEqual(len(board["orphans"]), 1)
        self.assertEqual(board["orphans"][0]["prompt"], "orphaned")


class TestPriority(unittest.TestCase):
    def test_apply_replaces_existing(self):
        out = ac.apply_priority("# T\nStatus: ready\nPriority: P2\n", "P0")
        self.assertIn("Priority: P0", out)
        self.assertNotIn("Priority: P2", out)

    def test_apply_inserts_under_status(self):
        out = ac.apply_priority("# T\nStatus: ready\n\nbody\n", "P1")
        self.assertRegex(out, r"Status: ready\nPriority: P1")

    def test_apply_unset_removes_line(self):
        out = ac.apply_priority("# T\nStatus: ready\nPriority: P1\nbody\n", "")
        self.assertNotIn("Priority", out)
        self.assertIn("Status: ready\nbody", out)


class TestAgentsView(unittest.TestCase):
    def test_stop_only_kills_known_pids(self):
        # stop_agent must reject a pid not reported by `claude agents`
        ok, msg = ac.stop_agent(999999)  # not a real agent
        self.assertFalse(ok)

    def test_start_rejects_untracked_cwd(self):
        ok, msg = ac.start_agent("/definitely/not/a/repo", "do x")
        self.assertFalse(ok)

    def test_start_rejects_empty_prompt(self):
        ok, msg = ac.start_agent(str(Path.home()), "")
        self.assertFalse(ok)


class TestPluginSourceDiscriminator(unittest.TestCase):
    def test_detects_plugin_source_repo(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / ".claude").mkdir()
            self.assertFalse(ac._is_plugin_source(repo))  # plain project repo
            cp = repo / ".claude-plugin"
            cp.mkdir()
            (cp / "plugin.json").write_text("{}")
            self.assertTrue(ac._is_plugin_source(repo))  # now a plugin source

    def test_marketplace_also_counts(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / ".claude-plugin").mkdir()
            (repo / ".claude-plugin" / "marketplace.json").write_text("{}")
            self.assertTrue(ac._is_plugin_source(repo))


if __name__ == "__main__":
    unittest.main()
