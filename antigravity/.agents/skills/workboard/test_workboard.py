"""Tests for workboard's Antigravity abandon mechanism.

Run: python3 -m unittest discover -s .claude/skills/workboard
Stdlib-only, like the scanner. Each test builds a throwaway HOME with a
fake ~/.gemini/antigravity/brain store — the real one is never touched.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import workboard  # noqa: E402

OLD_TS = "2020-01-01T00:00:00Z"    # far past --stale-days
FRESH_TS = None                    # filled per-test from now


def make_conv(brain, conv_id, boxes="", updated_at=OLD_TS, summary="s"):
    conv = brain / conv_id
    conv.mkdir(parents=True)
    if boxes:
        (conv / "task.md").write_text(boxes, encoding="utf-8")
    (conv / "task.md.metadata.json").write_text(
        json.dumps({"summary": summary, "updatedAt": updated_at}),
        encoding="utf-8")
    return conv


class AbandonTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self._tmp.name
        self.brain = Path(self._tmp.name) / ".gemini" / "antigravity" / "brain"
        self.brain.mkdir(parents=True)

    def tearDown(self):
        os.environ["HOME"] = self._old_home
        self._tmp.cleanup()


class TestScanSkipsAbandoned(AbandonTestCase):
    def test_scan_antigravity_skips_conversations_with_abandon_marker(self):
        make_conv(self.brain, "kept", boxes="- [ ] open item\n")
        abandoned = make_conv(self.brain, "gone", boxes="- [ ] open item\n")
        (abandoned / workboard.ABANDON_MARKER).write_text("", encoding="utf-8")

        ids = {c["id"] for c in workboard.scan_antigravity()}

        self.assertEqual(ids, {"kept"})


class TestAbandonConversations(AbandonTestCase):
    def test_abandon_writes_marker_into_named_conversation(self):
        conv = make_conv(self.brain, "target", boxes="- [ ] open\n")

        marked, missing = workboard.abandon_conversations(["target"])

        self.assertEqual(marked, ["target"])
        self.assertEqual(missing, [])
        self.assertTrue((conv / workboard.ABANDON_MARKER).is_file())

    def test_abandon_reports_unknown_ids_without_touching_disk(self):
        make_conv(self.brain, "other", boxes="- [ ] open\n")

        marked, missing = workboard.abandon_conversations(["nope"])

        self.assertEqual(marked, [])
        self.assertEqual(missing, ["nope"])


class TestAbandonStale(AbandonTestCase):
    def test_abandon_stale_marks_only_old_conversations_with_open_items(self):
        from datetime import datetime, timezone
        fresh = datetime.now(timezone.utc).isoformat()
        stale_open = make_conv(self.brain, "stale-open",
                               boxes="- [ ] a\n- [x] b\n", updated_at=OLD_TS)
        fresh_open = make_conv(self.brain, "fresh-open",
                               boxes="- [ ] a\n", updated_at=fresh)
        stale_done = make_conv(self.brain, "stale-done",
                               boxes="- [x] a\n", updated_at=OLD_TS)

        marked = workboard.abandon_stale(stale_days=7)

        self.assertEqual(marked, ["stale-open"])
        self.assertTrue((stale_open / workboard.ABANDON_MARKER).is_file())
        self.assertFalse((fresh_open / workboard.ABANDON_MARKER).is_file())
        self.assertFalse((stale_done / workboard.ABANDON_MARKER).is_file())

    def test_stale_antigravity_inbox_item_carries_runnable_abandon_command(self):
        make_conv(self.brain, "stale-open", boxes="- [ ] a\n", updated_at=OLD_TS)

        inbox = workboard.attention_items(
            repos=[], sessions=[], antigravity=workboard.scan_antigravity(),
            stale_days=7)

        self.assertEqual(len(inbox), 1)
        self.assertIn("--abandon stale-open", inbox[0].get("cmd", ""))

    def test_abandoned_conversations_leave_the_attention_inbox(self):
        make_conv(self.brain, "stale-open", boxes="- [ ] a\n", updated_at=OLD_TS)
        workboard.abandon_stale(stale_days=7)

        inbox = workboard.attention_items(
            repos=[], sessions=[], antigravity=workboard.scan_antigravity(),
            stale_days=7)

        self.assertEqual(inbox, [])


def make_repo_record(path="/r/demo", **git):
    g = {"branch": "main", "dirty": 0, "ahead": 0, "behind": 0,
         "worktrees": [], "last_commit_ts": 1.0}
    g.update(git)
    return {"path": path, "name": Path(path).name, "git": g,
            "specs": [], "handoffs": [], "sessions": []}


class TestOpenStatusNotBlocked(unittest.TestCase):
    def test_status_open_counts_as_open_not_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "specs" / "demo"
            (spec / "tasks").mkdir(parents=True)
            (spec / "SPEC.md").write_text("# Demo\n", encoding="utf-8")
            (spec / "tasks" / "01-a.md").write_text(
                "# A\nStatus: open\n", encoding="utf-8")

            specs = workboard.scan_toolkit_specs(Path(tmp))

            self.assertEqual(specs[0]["tasks_blocked"], [])

    def test_status_failed_still_flags_as_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "specs" / "demo"
            (spec / "tasks").mkdir(parents=True)
            (spec / "SPEC.md").write_text("# Demo\n", encoding="utf-8")
            (spec / "tasks" / "01-a.md").write_text(
                "# A\nStatus: failed\n", encoding="utf-8")

            specs = workboard.scan_toolkit_specs(Path(tmp))

            self.assertEqual(len(specs[0]["tasks_blocked"]), 1)


class TestSimpleCommandsInInbox(unittest.TestCase):
    def test_unpushed_commits_item_carries_git_push_command(self):
        repo = make_repo_record(ahead=2)

        inbox = workboard.attention_items([repo], [], [], stale_days=7)

        push_items = [i for i in inbox if "unpushed" in i["what"]]
        self.assertEqual(len(push_items), 1)
        self.assertIn("git -C /r/demo push", push_items[0].get("cmd", ""))

    def test_parked_handoff_item_carries_resume_command(self):
        repo = make_repo_record()
        repo["handoffs"] = [{"path": "docs/HANDOFF.md", "title": "t", "mtime": 1.0}]

        inbox = workboard.attention_items([repo], [], [], stale_days=7)

        self.assertIn("claude", inbox[0].get("cmd", ""))
        self.assertIn("docs/HANDOFF.md", inbox[0]["cmd"])

    def test_all_tasks_done_spec_carries_verifier_command(self):
        repo = make_repo_record()
        repo["specs"] = [{"kind": "toolkit", "slug": "demo", "title": "Demo",
                          "path": "specs/demo/SPEC.md", "tasks_total": 2,
                          "tasks_done": 2, "tasks_doing": 0,
                          "tasks_blocked": [], "tasks": [],
                          "last_touched": 1.0}]

        inbox = workboard.attention_items([repo], [], [], stale_days=7)

        self.assertIn("claude", inbox[0].get("cmd", ""))
        self.assertIn("demo", inbox[0]["cmd"])


BATON_FIXTURE = """# Drain baton: demo

Generation: 3

## Done this generation
- 01-a: merged (verifier PASS)
- 02-b: merged (verifier PASS)

## Next
- 03-c: ready to dispatch

## Relaunch
```bash
nohup claude -p "/drain specs/demo (generation 4, baton: specs/demo/DRAIN-BATON.md)" \\
  --allowedTools "Task,Read,Edit,Write,Glob,Grep,Bash(git *)" \\
  --permission-mode dontAsk --max-turns 80 \\
  >> specs/demo/.drain-gen.log 2>&1 &
```

## Needs attention
- 05-e deferred: which auth provider should the login flow use?
"""


def write_baton(root, slug="demo", body=BATON_FIXTURE):
    spec = Path(root) / "specs" / slug
    spec.mkdir(parents=True)
    (spec / "DRAIN-BATON.md").write_text(body, encoding="utf-8")
    return spec / "DRAIN-BATON.md"


class TestScanBatons(unittest.TestCase):
    def test_scan_batons_extracts_generation_command_and_needs_attention(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_baton(tmp)

            batons = workboard.scan_batons(Path(tmp))

            self.assertEqual(len(batons), 1)
            b = batons[0]
            self.assertEqual(b["path"], "specs/demo/DRAIN-BATON.md")
            self.assertEqual(b["generation"], 3)
            self.assertIn("claude -p", b["command"])
            self.assertIn("/drain specs/demo", b["command"])
            self.assertIn("auth provider", b["needs_attention"])

    def test_scan_batons_returns_empty_when_no_baton_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "specs" / "demo").mkdir(parents=True)

            self.assertEqual(workboard.scan_batons(Path(tmp)), [])


class TestRenderBatons(unittest.TestCase):
    def test_baton_card_shows_generation_command_and_needs_attention(self):
        html = workboard.render_batons([{
            "path": "specs/demo/DRAIN-BATON.md", "generation": 3,
            "command": 'claude -p "/drain specs/demo (generation 4, baton: x)"',
            "needs_attention": "05-e deferred: which auth provider?",
            "mtime": 1.0,
        }])

        self.assertIn("3", html)
        self.assertIn("claude -p", html)
        self.assertIn("auth provider", html)

    def test_baton_card_text_differs_from_handoff_resume_then_delete(self):
        html = workboard.render_batons([{
            "path": "specs/demo/DRAIN-BATON.md", "generation": 2,
            "command": 'claude -p "/drain x"', "needs_attention": "",
            "mtime": 1.0,
        }])

        self.assertNotIn("resume it in a fresh session, then delete", html)
        self.assertIn("relaunch", html.lower())


class TestBatonInFullRender(unittest.TestCase):
    def test_baton_and_handoff_both_render_on_the_board(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_baton(tmp)
            (Path(tmp) / "HANDOFF.md").write_text(
                "# Parked work\nsome context\n", encoding="utf-8")
            repo = make_repo_record(path=tmp)
            repo["batons"] = workboard.scan_batons(Path(tmp))
            repo["handoffs"] = workboard.scan_handoffs(Path(tmp))
            data = {
                "totals": {"repos": 1, "specs_open": 0, "tasks_open": 0,
                           "sessions_active": 0, "attention": 0},
                "generated_at": "now", "stale_days": 7,
                "inbox": [], "ready": {"items": [], "blocked_unresolved": []},
                "repos": [repo],
                "antigravity": [], "todos": [], "orphan_sessions": [],
            }

            html = workboard.render_html(data)

            self.assertIn("DRAIN-BATON.md", html)      # baton card present
            self.assertIn("generation", html.lower())
            self.assertIn("HANDOFF.md", html)          # handoff still renders


if __name__ == "__main__":
    unittest.main()
