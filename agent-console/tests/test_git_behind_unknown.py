"""Workboard git-chip rendering of an unknown `behind` count (workboard-actions
task 10).

`workboard.git_info` reports `behind` as None when a config-derived upstream
SHA resolved via ls-remote but is absent from the local object store (nothing
fetched): the count is genuinely unknown, not zero. The board must surface that
as a distinct "behind: ?" chip rather than silently dropping it (a falsy None
would render nothing, reading as "not behind"). These assert rendered structure
(parse, don't match exact strings) via the production `_adapt_board` ->
`render_workboard` seam, matching the other workboard render tests.
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


def _render(behind):
    fixture = {
        "repos": [
            {
                "path": "/tmp/fixture-repo",
                "name": "alpha",
                "git": {"branch": "main", "dirty": 0, "ahead": 0, "behind": behind},
                "specs": [],
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
        patch.object(ac, "_repo_extras", return_value=({}, {})),
    ):
        board = ac._adapt_board(fixture, [], [])
    return ac.render_workboard(board)


def _gchips(html: str):
    """The rendered text/title of every git chip, in order."""
    out = []
    collecting = False
    text = ""
    title = ""

    class P(HTMLParser):
        def handle_starttag(self, tag, attrs):
            nonlocal collecting, text, title
            a = dict(attrs)
            if "gchip" in (a.get("class") or "").split():
                collecting = True
                text = ""
                title = a.get("title") or ""

        def handle_data(self, data):
            nonlocal text
            if collecting:
                text += data

        def handle_endtag(self, tag):
            nonlocal collecting
            if collecting and tag in ("span", "button"):
                out.append((text, title))
                collecting = False

    P().feed(html)
    return out


class GitBehindUnknownChip(unittest.TestCase):
    def test_behind_none_renders_an_unknown_marker_chip(self):
        html = _render(None)
        chips = _gchips(html)
        # A chip must surface the unknown behind state — carrying a "?" rather
        # than a numeric count, and identifying itself as the behind axis.
        unknown = [
            (t, ti)
            for (t, ti) in chips
            if "?" in t and ("behind" in ti.lower() or "behind" in t.lower())
        ]
        self.assertTrue(
            unknown,
            f"expected a 'behind: ?' unknown chip; got chips {chips!r}",
        )

    def test_behind_zero_renders_no_behind_chip(self):
        # A known-zero behind stays chip-less (unchanged behavior); only the
        # unknown (None) state gets the "?" marker.
        chips = _gchips(_render(0))
        self.assertFalse(
            [c for c in chips if "?" in c[0]],
            "behind=0 must not render an unknown '?' chip",
        )

    def test_behind_positive_renders_numeric_chip(self):
        chips = _gchips(_render(4))
        self.assertTrue(
            [t for (t, _ti) in chips if "4" in t],
            "behind=4 must render its numeric count",
        )


if __name__ == "__main__":
    unittest.main()
