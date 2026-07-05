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


def make_session(toplevel, state="active"):
    """A session record as attention_items reads it: state + git toplevel."""
    return {"state": state, "toplevel": toplevel, "cwd": toplevel}


def task_worktree(activity_ts, path="/r/demo/.claude/worktrees/01",
                  branch="task/01-x"):
    return {"path": path, "branch": branch, "activity_ts": activity_ts}


class TestActiveCoverageReclassification(unittest.TestCase):
    """R10: a repo covered by a live session or an active drain moves its
    uncommitted/unpushed items out of needs-review into an Active
    (in-progress / active) group, and out of the attention headline count."""

    def _states(self, inbox):
        return [i["state"] for i in inbox]

    def test_live_session_reclassifies_dirty_and_unpushed_to_active(self):
        # session toplevel == repo root → live human coverage (both branches)
        repo = make_repo_record(path="/r/demo", dirty=3, ahead=2)
        inbox = workboard.attention_items(
            [repo], [make_session("/r/demo")], [], stale_days=7)

        self.assertEqual(len(inbox), 2)                       # dirty + unpushed
        self.assertEqual(set(self._states(inbox)), {"in-progress"})
        self.assertTrue(all(i["category"] == "active" for i in inbox))
        self.assertFalse(any(i["state"] == "needs-review" for i in inbox))

    def test_live_drain_worktree_reclassifies_active_without_matching_session(self):
        # the case that misfired: drain live, orchestrator session cwd NOT under
        # the repo — coverage must come from the task/* worktree activity window.
        repo = make_repo_record(
            path="/r/demo", dirty=1,
            worktrees=[task_worktree(workboard.now_ts())])
        inbox = workboard.attention_items([repo], [], [], stale_days=7)

        self.assertEqual(self._states(inbox), ["in-progress"])
        self.assertEqual(inbox[0]["category"], "active")

    def test_stale_task_worktree_still_flags_needs_review(self):
        # identical to the live-drain fixture EXCEPT activity mtime is older than
        # the drain window → stranded work, must still flag.
        stale_act = workboard.now_ts() - (workboard.DRAIN_WINDOW_DEFAULT + 600)
        repo = make_repo_record(
            path="/r/demo", dirty=1,
            worktrees=[task_worktree(stale_act)])
        inbox = workboard.attention_items([repo], [], [], stale_days=7)

        self.assertEqual(self._states(inbox), ["needs-review"])

    def test_live_and_stale_differ_only_by_worktree_activity(self):
        live = make_repo_record(path="/r/demo", dirty=1,
                                worktrees=[task_worktree(workboard.now_ts())])
        stale = make_repo_record(
            path="/r/demo", dirty=1,
            worktrees=[task_worktree(
                workboard.now_ts() - (workboard.DRAIN_WINDOW_DEFAULT + 600))])
        live_states = self._states(
            workboard.attention_items([live], [], [], stale_days=7))
        stale_states = self._states(
            workboard.attention_items([stale], [], [], stale_days=7))

        self.assertEqual(live_states, ["in-progress"])
        self.assertEqual(stale_states, ["needs-review"])

    def test_decay_session_gone_returns_to_needs_review(self):
        repo = make_repo_record(path="/r/demo", ahead=1)
        covered = workboard.attention_items(
            [repo], [make_session("/r/demo")], [], stale_days=7)
        uncovered = workboard.attention_items([repo], [], [], stale_days=7)

        self.assertEqual(self._states(covered), ["in-progress"])
        self.assertEqual(self._states(uncovered), ["needs-review"])

    def test_decay_worktree_ages_past_window_returns_to_needs_review(self):
        fresh = make_repo_record(path="/r/demo", dirty=1,
                                 worktrees=[task_worktree(workboard.now_ts())])
        aged = make_repo_record(
            path="/r/demo", dirty=1,
            worktrees=[task_worktree(
                workboard.now_ts() - (workboard.DRAIN_WINDOW_DEFAULT + 1))])

        self.assertEqual(
            self._states(workboard.attention_items([fresh], [], [], stale_days=7)),
            ["in-progress"])
        self.assertEqual(
            self._states(workboard.attention_items([aged], [], [], stale_days=7)),
            ["needs-review"])

    def test_nested_session_toplevel_does_not_cover_parent(self):
        # defect 3: a session inside a nested child repo (its toplevel is the
        # child, not the parent) must NOT mark the parent covered.
        parent = make_repo_record(path="/r/parent", dirty=1)
        inbox = workboard.attention_items(
            [parent], [make_session("/r/parent/child")], [], stale_days=7)

        self.assertEqual(self._states(inbox), ["needs-review"])

    def test_parked_baton_does_not_suppress_git_state(self):
        # a baton is a paused generation, not proof of a live drain.
        repo = make_repo_record(path="/r/demo", dirty=1)
        repo["batons"] = [{"path": "specs/x/DRAIN-BATON.md", "generation": 2,
                           "command": "", "needs_attention": "", "mtime": 1.0}]
        inbox = workboard.attention_items([repo], [], [], stale_days=7)

        self.assertEqual(self._states(inbox), ["needs-review"])

    def test_attention_total_excludes_in_progress(self):
        active = {"state": "in-progress", "category": "active", "age_ts": 1.0}
        review = {"state": "needs-review", "age_ts": 1.0}
        self.assertEqual(workboard.attention_total([active, review, active]), 1)


class TestBatonNeedsAttentionInbox(unittest.TestCase):
    """oc-06: a baton carrying a needs-attention section is promoted into the
    attention inbox so it ranks among blocked work, not just as a repo card."""

    def _baton(self, needs_attention, command='claude -p "/drain specs/x (gen 4)"'):
        return {"path": "specs/x/DRAIN-BATON.md", "generation": 3,
                "command": command, "needs_attention": needs_attention,
                "mtime": 5.0}

    def test_needs_attention_baton_becomes_blocked_inbox_item(self):
        repo = make_repo_record(path="/r/demo")
        repo["batons"] = [self._baton("05-e deferred: which auth provider?")]
        inbox = workboard.attention_items([repo], [], [], stale_days=7)

        baton_items = [i for i in inbox if "baton" in i["what"].lower()]
        self.assertEqual(len(baton_items), 1)
        self.assertEqual(baton_items[0]["state"], "blocked")
        self.assertEqual(baton_items[0]["severity"], "serious")
        self.assertIn("auth provider", baton_items[0]["why"])

    def test_needs_attention_baton_carries_relaunch_command(self):
        repo = make_repo_record(path="/r/demo")
        repo["batons"] = [self._baton("which provider?")]
        inbox = workboard.attention_items([repo], [], [], stale_days=7)

        baton_items = [i for i in inbox if "baton" in i["what"].lower()]
        self.assertIn("/drain specs/x", baton_items[0].get("cmd", ""))

    def test_baton_without_needs_attention_adds_no_inbox_item(self):
        repo = make_repo_record(path="/r/demo")
        repo["batons"] = [self._baton("")]
        inbox = workboard.attention_items([repo], [], [], stale_days=7)

        self.assertEqual([i for i in inbox if "baton" in i["what"].lower()], [])

    def test_needs_attention_baton_ranks_among_blocked_before_warnings(self):
        # a repo with both a needs-attention baton (serious) and dirty state
        # (warning): the baton sorts ahead in the flat, severity-ranked list.
        repo = make_repo_record(path="/r/demo", dirty=1)
        repo["batons"] = [self._baton("blocking question")]
        inbox = workboard.attention_items([repo], [], [], stale_days=7)

        self.assertIn("baton", inbox[0]["what"].lower())


class TestActiveRendering(unittest.TestCase):
    def _active(self):
        return {"state": "in-progress", "category": "active", "repo": "demo",
                "what": "1 uncommitted change(s) — a live session/drain is working here",
                "why": "owned work-in-progress, not neglected", "age_ts": 1.0}

    def test_active_group_renders_and_suppresses_inbox_zero(self):
        html = workboard.render_inbox([self._active()])
        self.assertIn('data-category="active"', html)
        self.assertNotIn("Inbox zero", html)
        self.assertIn("in-progress", html)     # its badge/state word

    def test_inbox_zero_only_when_no_attention_and_no_active(self):
        self.assertIn("Inbox zero", workboard.render_inbox([]))

    def test_active_group_renders_after_attention_groups(self):
        review = {"state": "needs-review", "repo": "demo",
                  "what": "stranded work", "why": "commit or stash", "age_ts": 2.0}
        html = workboard.render_inbox([self._active(), review])
        self.assertLess(html.index('data-category="needs-review"'),
                        html.index('data-category="active"'))

    def test_active_filter_tile_present_with_count(self):
        data = {"ready": {"items": []},
                "inbox": [self._active(), self._active()]}
        html = workboard.render_filter_tiles(data)
        self.assertIn('data-filter="active"', html)
        self.assertIn(">2<", html)             # active count


def write_session(projects_dir, proj="proj1", sid="sess1", records=None):
    """A session transcript .jsonl with the given records (dicts), oldest first."""
    d = projects_dir / proj
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{sid}.jsonl"
    p.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    return p


class TestSessionStartTs(unittest.TestCase):
    """R6 (workboard half): scan_sessions resolves a start_ts per session,
    keeping the existing last-activity as end_ts."""

    def test_scan_sessions_uses_earliest_transcript_record_as_start_ts(self):
        with tempfile.TemporaryDirectory() as tmp:
            claude_home = Path(tmp)
            write_session(claude_home / "projects", records=[
                {"type": "user", "message": {"content": "hi"}, "cwd": "/r/demo",
                 "gitBranch": "main", "timestamp": "2020-01-01T00:00:00Z"},
                {"type": "assistant", "message": {"content": "ok"},
                 "timestamp": "2020-01-01T01:00:00Z"},
            ])

            sessions = workboard.scan_sessions(claude_home, stale_days=7)

            self.assertEqual(len(sessions), 1)
            s = sessions[0]
            self.assertEqual(s["start_ts"], workboard.iso_to_ts("2020-01-01T00:00:00Z"))
            self.assertEqual(s["end_ts"], s["last_ts"])
            self.assertLess(s["start_ts"], s["end_ts"])

    def test_scan_sessions_start_ts_never_none_without_transcript_timestamps(self):
        # No record carries a `timestamp` field at all: start_ts must still
        # resolve (st_birthtime, then end_ts) rather than leave it None —
        # viz.timeline() raises ValueError on a missing start_ts.
        with tempfile.TemporaryDirectory() as tmp:
            claude_home = Path(tmp)
            write_session(claude_home / "projects", records=[
                {"type": "user", "message": {"content": "hi"}, "cwd": "/r/demo"},
            ])

            sessions = workboard.scan_sessions(claude_home, stale_days=7)

            s = sessions[0]
            self.assertIsNotNone(s["start_ts"])
            self.assertLessEqual(s["start_ts"], s["end_ts"])


class TestSessionTimelineRendering(unittest.TestCase):
    """R5 (workboard half): the Sessions section renders via viz.timeline()
    instead of a flat table."""

    def _data(self, repos=None, orphan_sessions=None):
        return {
            "totals": {"repos": len(repos or []), "specs_open": 0, "tasks_open": 0,
                       "sessions_active": 0, "attention": 0},
            "generated_at": "now", "stale_days": 7,
            "inbox": [], "ready": {"items": [], "blocked_unresolved": []},
            "repos": repos or [],
            "antigravity": [], "todos": [], "orphan_sessions": orphan_sessions or [],
        }

    def _session(self, state="active", start_ts=1.0, end_ts=100.0):
        return {"id": "s1", "cwd": "/r/demo", "branch": "main",
                "prompt": "do the thing", "last_ts": end_ts, "start_ts": start_ts,
                "end_ts": end_ts, "bytes": 10, "state": state}

    def test_repo_session_renders_viz_bar_with_color_fallback(self):
        repo = make_repo_record()
        repo["sessions"] = [self._session()]

        html = workboard.render_html(self._data(repos=[repo]))

        self.assertIn('viz-bar', html)
        self.assertIn('var(--viz-running,', html)   # "active" state -> canonical "running"

    def test_orphan_sessions_render_via_viz_timeline(self):
        html = workboard.render_html(
            self._data(orphan_sessions=[self._session(state="stale")]))

        self.assertIn('viz-bar viz-stale', html)


class TestSpecDagRendering(unittest.TestCase):
    """R5 (workboard half): a spec with deps renders its dependency DAG via
    viz.dag() (an SVG <path> per in-list edge)."""

    def _spec_with_dep(self, repo_root):
        tasks_dir = Path(repo_root) / "specs" / "demo" / "tasks"
        tasks_dir.mkdir(parents=True)
        (tasks_dir / "01-a.md").write_text(
            "# A\nStatus: done\n", encoding="utf-8")
        (tasks_dir / "02-b.md").write_text(
            "# B\nStatus: pending\nDepends on: 01\n", encoding="utf-8")
        tasks = [
            {"file": "specs/demo/tasks/01-a.md",
             "abs": str(tasks_dir / "01-a.md"),
             "title": "A", "status": "done", "deps": []},
            {"file": "specs/demo/tasks/02-b.md",
             "abs": str(tasks_dir / "02-b.md"),
             "title": "B", "status": "pending", "deps": ["01"]},
        ]
        return {"kind": "toolkit", "slug": "demo", "title": "Demo",
                "path": "specs/demo/SPEC.md", "tasks_total": 2, "tasks_done": 1,
                "tasks_doing": 0, "tasks_blocked": [], "tasks": tasks,
                "last_touched": 1.0}

    def test_spec_with_deps_renders_dag_edge(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo_record()
            repo["specs"] = [self._spec_with_dep(tmp)]

            data = {
                "totals": {"repos": 1, "specs_open": 1, "tasks_open": 1,
                           "sessions_active": 0, "attention": 0},
                "generated_at": "now", "stale_days": 7,
                "inbox": [], "ready": {"items": [], "blocked_unresolved": []},
                "repos": [repo],
                "antigravity": [], "todos": [], "orphan_sessions": [],
            }

            html = workboard.render_html(data)

            self.assertIn('<path', html)

    def test_spec_without_deps_renders_no_dag(self):
        repo = make_repo_record()
        repo["specs"] = [{"kind": "toolkit", "slug": "solo", "title": "Solo",
                          "path": "specs/solo/SPEC.md", "tasks_total": 1,
                          "tasks_done": 0, "tasks_doing": 0, "tasks_blocked": [],
                          "tasks": [{"file": "specs/solo/tasks/01-a.md",
                                    "abs": "/x/01-a.md", "title": "A",
                                    "status": "open", "deps": []}],
                          "last_touched": 1.0}]

        data = {
            "totals": {"repos": 1, "specs_open": 1, "tasks_open": 1,
                       "sessions_active": 0, "attention": 0},
            "generated_at": "now", "stale_days": 7,
            "inbox": [], "ready": {"items": [], "blocked_unresolved": []},
            "repos": [repo],
            "antigravity": [], "todos": [], "orphan_sessions": [],
        }

        html = workboard.render_html(data)

        self.assertNotIn('<path', html)


class TestSpecDagResolvesDeps(unittest.TestCase):
    """R3: _spec_dag_tasks resolves `Depends on:` entries through
    resolve_dep/_glob_task instead of a bare isdigit() filter."""

    def _make_spec(self, repo_root, slug, task_bodies):
        """Write real task files under <repo_root>/specs/<slug>/tasks/ and
        return the scanned spec dict for that slug (via scan_toolkit_specs,
        so `deps` comes from the real `Depends on:` parser)."""
        spec_dir = Path(repo_root) / "specs" / slug
        (spec_dir / "tasks").mkdir(parents=True)
        (spec_dir / "SPEC.md").write_text("# Demo\n", encoding="utf-8")
        for fname, status, depends in task_bodies:
            text = f"# {fname}\nStatus: {status}\n"
            if depends is not None:
                text += f"Depends on: {depends}\n"
            (spec_dir / "tasks" / fname).write_text(text, encoding="utf-8")
        specs = {s["slug"]: s for s in workboard.scan_toolkit_specs(Path(repo_root))}
        return specs[slug]

    def test_task_dir_relative_path_dep_draws_edge(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = self._make_spec(tmp, "demo", [
                ("01-a.md", "done", None),
                ("02-b.md", "pending", "01-a.md"),
            ])

            svg = workboard.viz.dag(workboard._spec_dag_tasks(spec))

            self.assertIn('<path', svg)

    def test_cyclic_deps_returns_without_hanging(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = self._make_spec(tmp, "demo", [
                ("01-a.md", "pending", "02-b.md"),
                ("02-b.md", "pending", "01-a.md"),
            ])

            svg = workboard.viz.dag(workboard._spec_dag_tasks(spec))

            self.assertIsInstance(svg, str)

    def test_no_deps_yields_no_dag_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = self._make_spec(tmp, "demo", [("01-a.md", "open", None)])

            self.assertEqual(workboard._spec_dag_html([spec]), "")

    def test_cross_spec_dep_draws_no_edge(self):
        with tempfile.TemporaryDirectory() as tmp:
            other_dir = Path(tmp) / "specs" / "other"
            (other_dir / "tasks").mkdir(parents=True)
            other_dir.joinpath("SPEC.md").write_text(
                "# Other\n", encoding="utf-8")
            (other_dir / "tasks" / "01-x.md").write_text(
                "# X\nStatus: done\n", encoding="utf-8")

            spec = self._make_spec(tmp, "demo", [
                ("01-b.md", "pending", "other/01"),
            ])

            deps = workboard._spec_dag_tasks(spec)[0]["deps"]

            self.assertEqual(deps, [])


class TestLiveSessionIdsCliAndFallback(unittest.TestCase):
    """R1: live_session_ids() sources liveness from the `claude agents --json`
    shim, falling back to the PID-record scan when the shim is absent/invalid,
    and returns the 2-tuple (live, liveness_unknown) in both paths."""

    def _patch_cli(self, result):
        orig = workboard._claude_agents_json
        workboard._claude_agents_json = lambda: result
        self.addCleanup(setattr, workboard, "_claude_agents_json", orig)

    def test_valid_cli_list_yields_liveness_map_ignoring_status(self):
        self._patch_cli([
            {"sessionId": "s1", "pid": 111, "status": "running"},
            {"sessionId": "s2", "pid": 222, "status": "idle"},  # status ignored
            {"pid": 333},  # missing sessionId -> not live
        ])

        live, liveness_unknown = workboard.live_session_ids(Path("/unused"))

        self.assertEqual(set(live), {"s1", "s2"})
        self.assertFalse(liveness_unknown)

    def test_cli_absent_falls_back_to_pid_record_scan(self):
        self._patch_cli(None)  # simulates claude missing from PATH / bad JSON
        with tempfile.TemporaryDirectory() as tmp:
            claude_home = Path(tmp)
            sess_dir = claude_home / "sessions"
            sess_dir.mkdir()
            (sess_dir / "a.json").write_text(
                json.dumps({"sessionId": "s1", "pid": os.getpid()}))

            live, liveness_unknown = workboard.live_session_ids(claude_home)

        self.assertEqual(set(live), {"s1"})
        self.assertFalse(liveness_unknown)

    def test_cli_non_empty_with_zero_live_marks_liveness_unknown(self):
        self._patch_cli([{"name": "orphan-record-missing-ids"}])

        live, liveness_unknown = workboard.live_session_ids(Path("/unused"))

        self.assertEqual(live, {})
        self.assertTrue(liveness_unknown)

    def test_cli_empty_list_is_not_liveness_unknown(self):
        self._patch_cli([])

        live, liveness_unknown = workboard.live_session_ids(Path("/unused"))

        self.assertEqual(live, {})
        self.assertFalse(liveness_unknown)

    def test_scan_sessions_plumbs_liveness_unknown_through(self):
        self._patch_cli([{"name": "orphan-record-missing-ids"}])
        with tempfile.TemporaryDirectory() as tmp:
            claude_home = Path(tmp)
            (claude_home / "projects").mkdir()

            workboard.scan_sessions(claude_home, stale_days=7)

        self.assertTrue(workboard._last_liveness_unknown)


class TestAttachSessionsRealpath(unittest.TestCase):
    """R2: the attach-sessions loop realpaths both sides of the match, so a
    session cwd that is a symlink into a repo still attributes to it."""

    def test_symlinked_session_cwd_attaches_to_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            real_repo = Path(tmp) / "real-repo"
            real_repo.mkdir()
            link = Path(tmp) / "link-to-repo"
            link.symlink_to(real_repo)

            repos = [{"path": str(real_repo)}]
            sessions = [{"id": "s1", "cwd": str(link)}]

            matched = workboard._attach_sessions(repos, sessions)

        self.assertEqual(matched, {"s1"})
        self.assertEqual([s["id"] for s in repos[0]["sessions"]], ["s1"])

    def test_non_symlinked_cwd_still_matches_as_before(self):
        repos = [{"path": "/r/demo"}]
        sessions = [{"id": "s1", "cwd": "/r/demo/sub"},
                    {"id": "s2", "cwd": "/other"}]

        matched = workboard._attach_sessions(repos, sessions)

        self.assertEqual(matched, {"s1"})


class TestScanToolkitSpecsUnparseableCount(unittest.TestCase):
    """R4: scan_toolkit_specs counts a task file as unparseable iff its
    filename lacks the leading NN- prefix _TASK_NUM_RE needs; every file
    still gets a defaulted row (no other rejection criterion)."""

    def test_all_tasks_missing_prefix_are_all_counted_unparseable(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec_dir = Path(tmp) / "specs" / "demo"
            (spec_dir / "tasks").mkdir(parents=True)
            (spec_dir / "SPEC.md").write_text("# Demo\n", encoding="utf-8")
            (spec_dir / "tasks" / "notes.md").write_text(
                "# Notes\nStatus: pending\n", encoding="utf-8")
            (spec_dir / "tasks" / "todo.md").write_text(
                "# Todo\nStatus: pending\n", encoding="utf-8")

            spec = workboard.scan_toolkit_specs(Path(tmp))[0]

            self.assertEqual(spec["tasks_total"], 2)
            self.assertEqual(spec["tasks_unparseable"], 2)
            self.assertEqual(len(spec["tasks"]), 2)  # still parsed, not dropped

    def test_mixed_prefixed_and_unprefixed_counts_only_the_unprefixed(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec_dir = Path(tmp) / "specs" / "demo"
            (spec_dir / "tasks").mkdir(parents=True)
            (spec_dir / "SPEC.md").write_text("# Demo\n", encoding="utf-8")
            (spec_dir / "tasks" / "01-a.md").write_text(
                "# A\nStatus: done\n", encoding="utf-8")
            (spec_dir / "tasks" / "notes.md").write_text(
                "# Notes\nStatus: pending\n", encoding="utf-8")

            spec = workboard.scan_toolkit_specs(Path(tmp))[0]

            self.assertEqual(spec["tasks_total"], 2)
            self.assertEqual(spec["tasks_unparseable"], 1)


class TestSourceHealthMarkers(unittest.TestCase):
    """R4: sources that are present but yield zero parseable records show a
    visible "source check"/"liveness unknown" marker instead of rendering
    silently empty."""

    def _data(self, repos=None, orphan_sessions=None, liveness_unknown=False):
        return {
            "totals": {"repos": len(repos or []), "specs_open": 0, "tasks_open": 0,
                       "sessions_active": 0, "attention": 0},
            "generated_at": "now", "stale_days": 7,
            "inbox": [], "ready": {"items": [], "blocked_unresolved": []},
            "repos": repos or [],
            "antigravity": [], "todos": [], "orphan_sessions": orphan_sessions or [],
            "liveness_unknown": liveness_unknown,
        }

    def _session(self, state="active"):
        return {"id": "s1", "cwd": "/r/demo", "branch": "main",
                "prompt": "do the thing", "last_ts": 100.0, "start_ts": 1.0,
                "end_ts": 100.0, "bytes": 10, "state": state}

    def test_spec_with_all_unparseable_tasks_renders_source_check_marker(self):
        repo = make_repo_record()
        repo["specs"] = [{"kind": "toolkit", "slug": "demo", "title": "Demo",
                          "path": "specs/demo/SPEC.md", "tasks_total": 2,
                          "tasks_done": 0, "tasks_doing": 0, "tasks_blocked": [],
                          "tasks": [
                              {"file": "specs/demo/tasks/notes.md",
                               "abs": "/x/notes.md", "title": "Notes",
                               "status": "pending", "deps": []},
                              {"file": "specs/demo/tasks/todo.md",
                               "abs": "/x/todo.md", "title": "Todo",
                               "status": "pending", "deps": []},
                          ],
                          "tasks_unparseable": 2, "last_touched": 1.0}]

        html = workboard.render_html(self._data(repos=[repo]))

        self.assertIn("source check", html)
        self.assertNotIn("no specs", html)  # task section still renders, not empty

    def test_spec_with_some_parseable_tasks_renders_no_marker(self):
        repo = make_repo_record()
        repo["specs"] = [{"kind": "toolkit", "slug": "demo", "title": "Demo",
                          "path": "specs/demo/SPEC.md", "tasks_total": 2,
                          "tasks_done": 1, "tasks_doing": 0, "tasks_blocked": [],
                          "tasks": [
                              {"file": "specs/demo/tasks/01-a.md",
                               "abs": "/x/01-a.md", "title": "A",
                               "status": "done", "deps": []},
                              {"file": "specs/demo/tasks/notes.md",
                               "abs": "/x/notes.md", "title": "Notes",
                               "status": "pending", "deps": []},
                          ],
                          "tasks_unparseable": 1, "last_touched": 1.0}]

        html = workboard.render_html(self._data(repos=[repo]))

        self.assertNotIn("source check", html)

    def test_liveness_unknown_renders_marker_adjacent_to_timeline(self):
        repo = make_repo_record()
        repo["sessions"] = [self._session()]

        html = workboard.render_html(self._data(repos=[repo], liveness_unknown=True))

        self.assertIn("liveness unknown", html)
        self.assertIn("viz-bar", html)  # session rows still render, unaffected

    def test_liveness_unknown_false_renders_no_marker(self):
        repo = make_repo_record()
        repo["sessions"] = [self._session()]

        html = workboard.render_html(self._data(repos=[repo], liveness_unknown=False))

        self.assertNotIn("liveness unknown", html)

    def test_liveness_unknown_marks_orphan_sessions_section_too(self):
        html = workboard.render_html(self._data(
            orphan_sessions=[self._session(state="stale")], liveness_unknown=True))

        self.assertIn("Sessions outside scanned repos", html)
        self.assertIn("liveness unknown", html)


if __name__ == "__main__":
    unittest.main()
