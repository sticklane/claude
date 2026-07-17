"""Render tests for the unblock/recheck dispatch buttons on spec cards
(unblock-next-steps task 08).

Task 04 built the `unblock`/`recheck` action registry; this suite covers the
HTML side — `render_workboard()` must emit `_dispatch_btn(...)` buttons whose
`data-id` matches the ids `build_action_registry` keys (`_entity_id(kind,
path)`), gated identically to the registry (git-repo root, truthy path, truthy
unblock, non-`ask`). Fixtures are the `_adapt_board()`-shaped board dicts
render_workboard consumes, built directly in test_unblock_actions.py's style;
assertions parse rendered structure (button presence + data-id), never exact
strings.
"""

import importlib.util
import unittest
from html.parser import HTMLParser
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "ac", str(Path(__file__).resolve().parent.parent / "agent-console.py")
)
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)


# --------------------------------------------------------------------------- #
# Fixtures — the board dict render_workboard() consumes (what _adapt_board
# produces). Real temp dirs back each repo so the git-root gate is exercised.
# --------------------------------------------------------------------------- #
import os
import tempfile


def _git_root():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, ".git"))
    return d


def _non_git_dir():
    return tempfile.mkdtemp()


def _spec_entry(slug, path, done=0, total=0, status=None, unblock=None, blocked_tasks=()):
    return {
        "id": ac._entity_id("spec", path) if path else "",
        "slug": slug,
        "title": slug,
        "status": status,
        "priority": "",
        "path": path,
        "done": done,
        "total": total,
        "tasks": [],
        "blocked_tasks": list(blocked_tasks),
        "unblock": unblock,
        "mtime": 0,
    }


def _blocked_task(path, title, unblock):
    return {"path": path, "title": title, "unblock": unblock}


def _repo_entry(path, name, specs=()):
    return {
        "id": ac._entity_id("repo", path),
        "name": name,
        "path": path,
        "git": {"branch": "main", "dirty": 0, "ahead": 0, "behind": 0},
        "specs": list(specs),
        "handoffs": [],
        "tasks": None,
        "sessions": [],
    }


def _full_board(repos):
    """A render_workboard()-consumable board with the top-level keys the
    renderer reads, plus the given repos. Mirrors _adapt_board's output shape."""
    return {
        "repos": list(repos),
        "inbox": [],
        "orphans": [],
        "open_specs": [],
        "task_repos": [],
        "actives": [],
        "agents": [],
        "resumable": [],
        "repo_names": [r["name"] for r in repos],
        "health": [],
        "n_repos": len(repos),
        "n_open_specs": 0,
        "n_open_tasks": 0,
        "n_active": 0,
    }


class _Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def handle_startendtag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def _tags(html):
    c = _Collector()
    c.feed(html)
    return c.tags


def _dispatch_ids(html):
    return {
        a["data-id"]
        for (t, a) in _tags(html)
        if t == "button" and a.get("data-act") == "dispatch" and a.get("data-id")
    }


def _render(repos):
    return ac.render_workboard(_full_board(repos))


class WaitingSpecHeader(unittest.TestCase):
    def test_waiting_spec_in_git_root_renders_unblock_and_recheck(self):
        repo = _git_root()
        sp = os.path.join(repo, "specs", "w", "SPEC.md")
        html = _render(
            [
                _repo_entry(
                    repo,
                    "alpha",
                    specs=[
                        _spec_entry(
                            "w",
                            sp,
                            status="waiting",
                            unblock={"type": "agent", "step": "check the deploy"},
                        )
                    ],
                )
            ]
        )
        ids = _dispatch_ids(html)
        self.assertIn(ac._entity_id("unblock", sp), ids)
        self.assertIn(ac._entity_id("recheck", sp), ids)

    def test_buttons_not_gated_behind_total(self):
        # A waiting spec commonly has no tasks/ (total 0); buttons must still render.
        repo = _git_root()
        sp = os.path.join(repo, "specs", "w", "SPEC.md")
        html = _render(
            [
                _repo_entry(
                    repo,
                    "alpha",
                    specs=[
                        _spec_entry(
                            "w",
                            sp,
                            total=0,
                            unblock={"type": "run", "step": "make deploy"},
                        )
                    ],
                )
            ]
        )
        self.assertIn(ac._entity_id("recheck", sp), _dispatch_ids(html))


class BlockedTasks(unittest.TestCase):
    def test_blocked_task_renders_its_own_buttons_keyed_on_task_path(self):
        repo = _git_root()
        sp = os.path.join(repo, "specs", "x", "SPEC.md")
        tf = os.path.join(repo, "specs", "x", "tasks", "01-foo.md")
        html = _render(
            [
                _repo_entry(
                    repo,
                    "alpha",
                    specs=[
                        _spec_entry(
                            "x",
                            sp,
                            blocked_tasks=[
                                _blocked_task(
                                    tf, "Foo", {"type": "run", "step": "make deploy"}
                                )
                            ],
                        )
                    ],
                )
            ]
        )
        ids = _dispatch_ids(html)
        self.assertIn(ac._entity_id("unblock", tf), ids)
        self.assertIn(ac._entity_id("recheck", tf), ids)


class NoButtons(unittest.TestCase):
    def test_ask_typed_spec_renders_no_buttons(self):
        repo = _git_root()
        sp = os.path.join(repo, "specs", "w", "SPEC.md")
        html = _render(
            [
                _repo_entry(
                    repo,
                    "alpha",
                    specs=[
                        _spec_entry(
                            "w",
                            sp,
                            unblock={"type": "ask", "step": "which creds path?"},
                        )
                    ],
                )
            ]
        )
        ids = _dispatch_ids(html)
        self.assertNotIn(ac._entity_id("unblock", sp), ids)
        self.assertNotIn(ac._entity_id("recheck", sp), ids)

    def test_non_git_root_renders_no_buttons(self):
        home = _non_git_dir()
        sp = os.path.join(home, "specs", "w", "SPEC.md")
        html = _render(
            [
                _repo_entry(
                    home,
                    "specs-home",
                    specs=[
                        _spec_entry(
                            "w",
                            sp,
                            unblock={"type": "agent", "step": "check the deploy"},
                        )
                    ],
                )
            ]
        )
        ids = _dispatch_ids(html)
        self.assertNotIn(ac._entity_id("unblock", sp), ids)
        self.assertNotIn(ac._entity_id("recheck", sp), ids)

    def test_spec_without_unblock_renders_no_buttons(self):
        repo = _git_root()
        sp = os.path.join(repo, "specs", "w", "SPEC.md")
        html = _render(
            [_repo_entry(repo, "alpha", specs=[_spec_entry("w", sp, unblock=None)])]
        )
        ids = _dispatch_ids(html)
        self.assertNotIn(ac._entity_id("unblock", sp), ids)
        self.assertNotIn(ac._entity_id("recheck", sp), ids)


class DrainVerifyUnaffected(unittest.TestCase):
    def test_drain_button_still_renders_for_open_spec(self):
        repo = _git_root()
        sp = os.path.join(repo, "specs", "d", "SPEC.md")
        html = _render(
            [
                _repo_entry(
                    repo,
                    "alpha",
                    specs=[_spec_entry("d", sp, done=1, total=3)],
                )
            ]
        )
        self.assertIn(ac._entity_id("dispatch-drain", sp), _dispatch_ids(html))


if __name__ == "__main__":
    unittest.main()
