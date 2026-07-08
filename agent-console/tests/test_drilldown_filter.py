"""Workboard filter-bar rendering (drilldown task 04).

The workboard view must expose the same client-side `#q` filter the Skills
tab has: a filterbar input, plus a lowercase `data-text` attribute on every
repo card and inbox row so typing narrows the board. These tests assert the
rendered structure (parse, don't match exact strings); the typing/clearing
behavior itself is JS and is covered by the manual e2e pass.
"""

import importlib.util
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

_spec = importlib.util.spec_from_file_location(
    "ac", str(Path(__file__).resolve().parent.parent / "agent-console.py")
)
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)


class _Collector(HTMLParser):
    """Collect (tag, {attrs}) for every start/startend tag."""

    def __init__(self):
        super().__init__()
        self.tags: list[tuple[str, dict]] = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def handle_startendtag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def _tags(html: str) -> list[tuple[str, dict]]:
    c = _Collector()
    c.feed(html)
    return c.tags


def _classes(attrs: dict) -> set:
    return set((attrs.get("class") or "").split())


def _render(*, repo_name, spec_title, spec_slug, handoff_title, inbox_what):
    """Render the workboard from an assemble()-shaped fixture (hermetic:
    git/gh introspection patched out) via the production adapter."""
    fixture = {
        "repos": [
            {
                "path": "/tmp/fixture-repo",
                "name": repo_name,
                "git": {"branch": "main", "dirty": 1, "ahead": 0, "behind": 0},
                "specs": [
                    {
                        "title": spec_title,
                        "slug": spec_slug,
                        "tasks_done": 1,
                        "tasks_total": 3,
                        "path": "specs/" + spec_slug,
                        "priority": "P2",
                        "last_touched": 0,
                        "tasks": [],
                    }
                ],
                "handoffs": [
                    {"title": handoff_title, "path": "handoffs/h.md", "mtime": 0}
                ],
                "sessions": [],
            }
        ],
        "orphan_sessions": [],
        "inbox": [
            {
                "severity": "warning",
                "state": "needs-review",
                "repo": repo_name,
                "what": inbox_what,
                "why": "on branch main — commit or stash",
                "age_ts": 0,
            }
        ],
        "liveness_unknown": False,
    }
    with (
        patch.object(ac, "gh_visibility", return_value={}),
        patch.object(ac, "_repo_extras", return_value=({}, {})),
    ):
        board = ac._adapt_board(fixture, [], [])
    return ac.render_workboard(board)


class WorkboardFilterBar(unittest.TestCase):
    def setUp(self):
        self.html = _render(
            repo_name="alpha-console",
            spec_title="Widget Pipeline Overhaul",
            spec_slug="widget-pipeline",
            handoff_title="Resume Frobnicator",
            inbox_what="Uncommitted change on main",
        )

    def test_workboard_renders_the_filterbar_search_input(self):
        inputs = [
            a for (t, a) in _tags(self.html) if t == "input" and a.get("id") == "q"
        ]
        self.assertEqual(
            len(inputs), 1, "workboard must render exactly one #q filter input"
        )
        self.assertEqual(inputs[0].get("type"), "search")

    def test_repo_card_carries_lowercase_data_text_with_name_and_titles(self):
        repos = [
            a for (t, a) in _tags(self.html) if t == "details" and "repo" in _classes(a)
        ]
        self.assertTrue(repos, "expected a repo <details> card")
        dt = repos[0].get("data-text")
        self.assertIsNotNone(dt, "repo card must carry a data-text attribute")
        self.assertEqual(dt, dt.lower(), "data-text must be lowercase")
        self.assertIn("alpha-console", dt)
        self.assertIn("widget pipeline overhaul", dt)

    def test_repo_card_data_text_includes_spec_slug_for_slug_fragment_filtering(self):
        repos = [
            a for (t, a) in _tags(self.html) if t == "details" and "repo" in _classes(a)
        ]
        self.assertIn("widget-pipeline", repos[0].get("data-text", ""))

    def test_inbox_row_carries_lowercase_data_text_with_its_text(self):
        rows = [
            a for (t, a) in _tags(self.html) if t == "div" and _classes(a) == {"row"}
        ]
        self.assertTrue(rows, "expected an inbox .row div")
        dt = rows[0].get("data-text")
        self.assertIsNotNone(dt, "inbox row must carry a data-text attribute")
        self.assertEqual(dt, dt.lower(), "data-text must be lowercase")
        self.assertIn("uncommitted change on main", dt)

    def test_filter_targets_data_text_nodes_not_only_skills_cards(self):
        # Behavioral: the delegated #q handler must select by the shared
        # [data-text] attribute (which repo cards + inbox rows now carry),
        # not the Skills-only `.card` class — otherwise typing on the
        # workboard would hide nothing.
        self.assertIn("[data-text]", ac.PAGE_JS)


if __name__ == "__main__":
    unittest.main()
