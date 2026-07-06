"""Workboard "needs your answer" inbox class (unblock task 02).

Task 01's scanner marks ask-typed unblocks and deferred questions with inbox
state `needs-answer` (the unblock step / question text baked into `why`).
The workboard must surface those as a visually distinct block grouped BEFORE
the rest of the needs-attention inbox, carrying no dispatch affordance;
blocked items show their unblock text on the row, and a blocked item with no
recorded unblock shows a warning chip. These assert rendered structure (parse,
don't match exact strings) via the production `_adapt_board` -> `render_workboard`
seam, mirroring the assemble()-shaped fixtures the other workboard tests use.
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


def _inbox_groups(html: str):
    """Ordered [(class_set, [row_data_texts])] for each `.inbox` container.
    `.row`+data-text divs are inbox-only, so they map cleanly to their block."""
    groups = []
    cur = None
    for tag, attrs in _tags(html):
        cls = _classes(attrs)
        if tag == "div" and "inbox" in cls:
            cur = (cls, [])
            groups.append(cur)
        elif (
            tag == "div"
            and "row" in cls
            and attrs.get("data-text") is not None
            and cur is not None
        ):
            cur[1].append(attrs["data-text"])
    return groups


def _render(inbox: list) -> str:
    fixture = {
        "repos": [],
        "orphan_sessions": [],
        "inbox": inbox,
        "liveness_unknown": False,
    }
    with patch.object(ac, "gh_visibility", return_value={}):
        board = ac._adapt_board(fixture, [], [])
    return ac.render_workboard(board)


def _ask_item():
    return {
        "severity": "serious",
        "state": "needs-answer",
        "repo": "alpha",
        "what": "Answer needed: Wire the creds",
        "why": "which creds path?",
        "age_ts": 0,
    }


def _deferred_item():
    return {
        "severity": "serious",
        "state": "needs-answer",
        "repo": "alpha",
        "what": "Deferred question: Choose the base URL",
        "why": "what is the base URL?",
        "age_ts": 0,
    }


def _review_item():
    return {
        "severity": "warning",
        "state": "needs-review",
        "repo": "beta",
        "what": "2 uncommitted change(s), no live session",
        "why": "commit (then push) or stash",
        "age_ts": 0,
    }


class NeedsAnswerGrouping(unittest.TestCase):
    def test_ask_item_is_grouped_first_in_a_distinct_needs_answer_block(self):
        html = _render([_review_item(), _ask_item()])
        groups = _inbox_groups(html)
        self.assertEqual(len(groups), 2, "expected a needs-answer block + a general block")
        answer_cls, answer_rows = groups[0]
        general_cls, general_rows = groups[1]
        self.assertIn(
            "needs-answer", answer_cls, "the first inbox block must be the needs-answer block"
        )
        self.assertNotIn(
            "needs-answer", general_cls, "the general inbox block must not carry needs-answer"
        )
        self.assertTrue(
            any("wire the creds" in t for t in answer_rows),
            "the ask item belongs in the needs-answer block",
        )
        self.assertTrue(
            any("uncommitted" in t for t in general_rows),
            "the review item belongs in the general block",
        )

    def test_deferred_question_item_is_grouped_as_needs_answer(self):
        html = _render([_deferred_item()])
        groups = _inbox_groups(html)
        self.assertTrue(groups, "expected an inbox block")
        self.assertIn("needs-answer", groups[0][0])
        self.assertTrue(any("base url" in t for t in groups[0][1]))

    def test_needs_answer_block_carries_no_dispatch_or_action_affordance(self):
        html = _render([_ask_item()])
        region = html[html.index("inbox needs-answer") : html.index('id="agents"')]
        self.assertNotIn("<button", region, "needs-answer rows must have no dispatch button")
        self.assertNotIn("data-act", region, "needs-answer rows must have no action control")
        self.assertNotIn("<code", region, "needs-answer rows must render no runnable command")


class BlockedUnblockRow(unittest.TestCase):
    def _warn_chips(self, html):
        return [
            a
            for (t, a) in _tags(html)
            if t == "span" and {"chip", "warn"} <= _classes(a)
        ]

    def test_blocked_item_with_run_unblock_shows_step_text_and_no_warning(self):
        item = {
            "severity": "serious",
            "state": "blocked",
            "repo": "gamma",
            "what": "Spec widget: waiting",
            "why": "make deploy",
            "age_ts": 0,
        }
        html = _render([item])
        self.assertIn("make deploy", html, "the unblock step text must show on the row")
        self.assertEqual(
            self._warn_chips(html), [], "an item with a recorded unblock gets no warning chip"
        )

    def test_blocked_item_without_unblock_shows_warning_chip(self):
        item = {
            "severity": "serious",
            "state": "blocked",
            "repo": "gamma",
            "what": "Spec widget: waiting",
            "why": "no unblock step recorded — add an Unblock: line",
            "age_ts": 0,
        }
        html = _render([item])
        self.assertTrue(
            self._warn_chips(html), "a blocked item with no recorded unblock must show a warning chip"
        )


class AbsenceTolerant(unittest.TestCase):
    def test_render_survives_inbox_items_without_unblock_or_deferred_fields(self):
        # Older scanner JSON carries no unblock/deferred_questions keys at all.
        html = _render([_review_item()])
        self.assertIn("uncommitted", html, "older-shape inbox items must still render")


if __name__ == "__main__":
    unittest.main()
