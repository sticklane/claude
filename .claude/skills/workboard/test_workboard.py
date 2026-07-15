"""Tests for workboard's Antigravity abandon mechanism.

Run: python3 -m unittest discover -s .claude/skills/workboard
Stdlib-only, like the scanner. Each test builds a throwaway HOME with a
fake ~/.gemini/antigravity/brain store — the real one is never touched.
"""

import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import workboard  # noqa: E402

OLD_TS = "2020-01-01T00:00:00Z"  # far past --stale-days
FRESH_TS = None  # filled per-test from now


def make_conv(brain, conv_id, boxes="", updated_at=OLD_TS, summary="s"):
    conv = brain / conv_id
    conv.mkdir(parents=True)
    if boxes:
        (conv / "task.md").write_text(boxes, encoding="utf-8")
    (conv / "task.md.metadata.json").write_text(
        json.dumps({"summary": summary, "updatedAt": updated_at}), encoding="utf-8"
    )
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
        stale_open = make_conv(
            self.brain, "stale-open", boxes="- [ ] a\n- [x] b\n", updated_at=OLD_TS
        )
        fresh_open = make_conv(
            self.brain, "fresh-open", boxes="- [ ] a\n", updated_at=fresh
        )
        stale_done = make_conv(
            self.brain, "stale-done", boxes="- [x] a\n", updated_at=OLD_TS
        )

        marked = workboard.abandon_stale(stale_days=7)

        self.assertEqual(marked, ["stale-open"])
        self.assertTrue((stale_open / workboard.ABANDON_MARKER).is_file())
        self.assertFalse((fresh_open / workboard.ABANDON_MARKER).is_file())
        self.assertFalse((stale_done / workboard.ABANDON_MARKER).is_file())

    def test_stale_antigravity_inbox_item_carries_runnable_abandon_command(self):
        make_conv(self.brain, "stale-open", boxes="- [ ] a\n", updated_at=OLD_TS)

        inbox = workboard.attention_items(
            repos=[],
            sessions=[],
            antigravity=workboard.scan_antigravity(),
            stale_days=7,
        )

        self.assertEqual(len(inbox), 1)
        self.assertIn("--abandon stale-open", inbox[0].get("cmd", ""))

    def test_abandoned_conversations_leave_the_attention_inbox(self):
        make_conv(self.brain, "stale-open", boxes="- [ ] a\n", updated_at=OLD_TS)
        workboard.abandon_stale(stale_days=7)

        inbox = workboard.attention_items(
            repos=[],
            sessions=[],
            antigravity=workboard.scan_antigravity(),
            stale_days=7,
        )

        self.assertEqual(inbox, [])


def make_repo_record(path="/r/demo", **git):
    g = {
        "branch": "main",
        "dirty": 0,
        "ahead": 0,
        "behind": 0,
        "worktrees": [],
        "last_commit_ts": 1.0,
    }
    g.update(git)
    return {
        "path": path,
        "name": Path(path).name,
        "git": g,
        "specs": [],
        "handoffs": [],
        "sessions": [],
    }


class TestOpenStatusNotBlocked(unittest.TestCase):
    def test_status_open_counts_as_open_not_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "specs" / "demo"
            (spec / "tasks").mkdir(parents=True)
            (spec / "SPEC.md").write_text("# Demo\n", encoding="utf-8")
            (spec / "tasks" / "01-a.md").write_text(
                "# A\nStatus: open\n", encoding="utf-8"
            )

            specs = workboard.scan_toolkit_specs(Path(tmp))

            self.assertEqual(specs[0]["tasks_blocked"], [])

    def test_needs_verification_is_open_not_blocked(self):
        # Formal status for completed-but-unverified work: agent-bounded
        # (the verifier proceeds), so it is open — never a blocked flag.
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "specs" / "demo"
            (spec / "tasks").mkdir(parents=True)
            (spec / "SPEC.md").write_text("# Demo\n", encoding="utf-8")
            (spec / "tasks" / "01-a.md").write_text(
                "# A\nStatus: needs-verification\n", encoding="utf-8"
            )

            specs = workboard.scan_toolkit_specs(Path(tmp))

            self.assertEqual(specs[0]["tasks_blocked"], [])
            self.assertEqual(specs[0]["tasks_done"], 0)

    def test_status_failed_still_flags_as_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "specs" / "demo"
            (spec / "tasks").mkdir(parents=True)
            (spec / "SPEC.md").write_text("# Demo\n", encoding="utf-8")
            (spec / "tasks" / "01-a.md").write_text(
                "# A\nStatus: failed\n", encoding="utf-8"
            )

            specs = workboard.scan_toolkit_specs(Path(tmp))

            self.assertEqual(len(specs[0]["tasks_blocked"]), 1)


class TestPriorityRegexRange(unittest.TestCase):
    """The shared PRIORITY_RE reads `Priority: [P1]` as P1 (bracket-tolerant)
    and rejects out-of-range values like P7 (falls through to no match),
    pinning the same reading /prioritize uses (specs/codequality-shared-header-parsing)."""

    def test_bracketed_priority_reads_as_that_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "specs" / "demo"
            (spec / "tasks").mkdir(parents=True)
            (spec / "SPEC.md").write_text("# Demo\nPriority: [P1]\n", encoding="utf-8")

            specs = workboard.scan_toolkit_specs(Path(tmp))

            self.assertEqual(specs[0]["priority"], "P1")

    def test_out_of_range_priority_does_not_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "specs" / "demo"
            (spec / "tasks").mkdir(parents=True)
            (spec / "SPEC.md").write_text("# Demo\nPriority: P7\n", encoding="utf-8")

            specs = workboard.scan_toolkit_specs(Path(tmp))

            self.assertEqual(specs[0]["priority"], "")


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

    def test_all_tasks_done_spec_is_not_an_inbox_item(self):
        # Agent-bounded: verification proceeds (verifier agent / card button),
        # it is not the human's attention item.
        repo = make_repo_record()
        repo["specs"] = [
            {
                "kind": "toolkit",
                "slug": "demo",
                "title": "Demo",
                "path": "specs/demo/SPEC.md",
                "tasks_total": 2,
                "tasks_done": 2,
                "tasks_doing": 0,
                "tasks_blocked": [],
                "tasks": [],
                "last_touched": 1.0,
            }
        ]

        inbox = workboard.attention_items([repo], [], [], stale_days=7)

        self.assertEqual(inbox, [])


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


def _baton_with_relaunch(relaunch_cmd):
    """A DRAIN-BATON.md body whose Relaunch fenced block is `relaunch_cmd`."""
    return (
        "# Drain baton: demo\n\nGeneration: 4\n\n"
        f"## Relaunch\n```bash\n{relaunch_cmd}\n```\n\n"
        "## Needs attention\n- none\n"
    )


def _write_repo_baton(root, runtime_name, relaunch_cmd, slug="demo"):
    """Build a scratch repo: .claude/runtime.md naming `runtime_name` (or none
    when it is None) plus specs/<slug>/DRAIN-BATON.md carrying `relaunch_cmd`."""
    root = Path(root)
    if runtime_name is not None:
        (root / ".claude").mkdir(parents=True, exist_ok=True)
        (root / ".claude" / "runtime.md").write_text(
            f"runtime: {runtime_name}\n", encoding="utf-8"
        )
    spec = root / "specs" / slug
    spec.mkdir(parents=True, exist_ok=True)
    (spec / "DRAIN-BATON.md").write_text(
        _baton_with_relaunch(relaunch_cmd), encoding="utf-8"
    )
    return spec / "DRAIN-BATON.md"


class TestRuntimeAgnosticBatonParsing(unittest.TestCase):
    """R3/R4/R5/R9/R11: scan_batons resolves the repo's active runtime and
    parses the relaunch command with that runtime's shape, falling back
    through the other known runtimes."""

    def test_gemini_baton_command_extracted_not_empty(self):
        # R3/R4: a gemini -p-shaped baton in a gemini-cli repo extracts, where
        # the old hardcoded claude-only regex would have produced "".
        cmd = 'gemini -p "/drain specs/demo (generation 5, baton: x)" --approval-mode yolo'
        with tempfile.TemporaryDirectory() as tmp:
            _write_repo_baton(tmp, "gemini-cli", cmd)

            batons = workboard.scan_batons(Path(tmp))

            self.assertEqual(len(batons), 1)
            self.assertIn("gemini -p", batons[0]["command"])
            self.assertIn("/drain specs/demo", batons[0]["command"])
            self.assertFalse(batons[0].get("manual_relaunch"))
            self.assertFalse(batons[0].get("parse_warning"))

    def test_no_headless_runtime_sets_manual_relaunch_not_blank_command(self):
        # R5: a runtime with no scriptable headless template → manual_relaunch
        # set, command stays "", no regex attempted. antigravity left this
        # class 2026-07-12 when `agy -p` proved scriptable (runtimes/
        # antigravity.md); the synthetic no-headless profile is the fixture.
        cmd = 'claude -p "/drain specs/demo (generation 5)"'  # ignored: manual runtime
        with tempfile.TemporaryDirectory() as tmp:
            _write_repo_baton(tmp, "fake-runtime-no-headless", cmd)

            batons = workboard.scan_batons(Path(tmp))

            self.assertEqual(len(batons), 1)
            self.assertEqual(batons[0]["command"], "")
            self.assertTrue(batons[0].get("manual_relaunch"))
            self.assertIn(
                "fake-runtime-no-headless", batons[0]["manual_relaunch"].lower()
            )

    def test_antigravity_baton_command_extracted_since_agy_headless(self):
        # antigravity gained a real scriptable headless template (agy -p,
        # confirmed live 2026-07-12) — its batons now extract like any other
        # scriptable runtime instead of falling to manual_relaunch.
        cmd = (
            '/opt/homebrew/bin/agy -p "/drain specs/demo (generation 6, baton: y)" '
            "--new-project --mode accept-edits --sandbox"
        )
        with tempfile.TemporaryDirectory() as tmp:
            _write_repo_baton(tmp, "antigravity", cmd)

            batons = workboard.scan_batons(Path(tmp))

            self.assertEqual(len(batons), 1)
            self.assertIn("agy -p", batons[0]["command"])
            self.assertIn("/drain specs/demo", batons[0]["command"])
            self.assertFalse(batons[0].get("manual_relaunch"))
            self.assertFalse(batons[0].get("parse_warning"))

    def test_unrecognized_shape_sets_parse_warning_and_surfaces_in_inbox(self):
        # R9: a relaunch command matching no known runtime → command "",
        # parse_warning set, promoted into the needs-attention inbox.
        cmd = 'someothercli --go "do the thing"'
        with tempfile.TemporaryDirectory() as tmp:
            _write_repo_baton(tmp, None, cmd)  # no runtime.md → claude-code

            batons = workboard.scan_batons(Path(tmp))
            self.assertEqual(len(batons), 1)
            self.assertEqual(batons[0]["command"], "")
            self.assertTrue(batons[0].get("parse_warning"))

            repo = make_repo_record(path=tmp)
            repo["batons"] = batons
            inbox = workboard.attention_items([repo], [], [], stale_days=7)
            warn_items = [
                i
                for i in inbox
                if "baton" in i["what"].lower() and "relaunch" in i["what"].lower()
            ]
            self.assertEqual(len(warn_items), 1)

    def test_unresolvable_runtime_falls_back_to_claude_code_no_exception(self):
        # R11: a runtime.md naming a nonexistent profile falls back to
        # claude-code's regex; a claude -p baton still extracts, no raise.
        cmd = 'claude -p "/drain specs/demo (generation 5, baton: x)"'
        with tempfile.TemporaryDirectory() as tmp:
            _write_repo_baton(tmp, "no-such-runtime-xyz", cmd)

            batons = workboard.scan_batons(Path(tmp))

            self.assertEqual(len(batons), 1)
            self.assertIn("claude -p", batons[0]["command"])
            self.assertIn("/drain specs/demo", batons[0]["command"])
            self.assertFalse(batons[0].get("parse_warning"))

    def test_fake_runtime_extracted_with_no_parsing_logic_changes(self):
        # R9/R10: a brand-new runtimes/fake-runtime.md profile (a distinct
        # `fakecli run "..."` shape) parses purely from the profile — this
        # test adds only a fixture, touching no parsing logic.
        cmd = 'fakecli run "/drain specs/demo (generation 5, baton: x)"'
        with tempfile.TemporaryDirectory() as tmp:
            _write_repo_baton(tmp, "fake-runtime", cmd)

            batons = workboard.scan_batons(Path(tmp))

            self.assertEqual(len(batons), 1)
            self.assertIn("fakecli run", batons[0]["command"])
            self.assertIn("/drain specs/demo", batons[0]["command"])








def make_session(toplevel, state="active"):
    """A session record as attention_items reads it: state + git toplevel."""
    return {"state": state, "toplevel": toplevel, "cwd": toplevel}


def task_worktree(activity_ts, path="/r/demo/.claude/worktrees/01", branch="task/01-x"):
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
            [repo], [make_session("/r/demo")], [], stale_days=7
        )

        self.assertEqual(len(inbox), 2)  # dirty + unpushed
        self.assertEqual(set(self._states(inbox)), {"in-progress"})
        self.assertTrue(all(i["category"] == "active" for i in inbox))
        self.assertFalse(any(i["state"] == "needs-review" for i in inbox))

    def test_live_drain_worktree_reclassifies_active_without_matching_session(self):
        # the case that misfired: drain live, orchestrator session cwd NOT under
        # the repo — coverage must come from the task/* worktree activity window.
        repo = make_repo_record(
            path="/r/demo", dirty=1, worktrees=[task_worktree(workboard.now_ts())]
        )
        inbox = workboard.attention_items([repo], [], [], stale_days=7)

        self.assertEqual(self._states(inbox), ["in-progress"])
        self.assertEqual(inbox[0]["category"], "active")

    def test_stale_task_worktree_still_flags_needs_review(self):
        # identical to the live-drain fixture EXCEPT activity mtime is older than
        # the drain window → stranded work, must still flag.
        stale_act = workboard.now_ts() - (workboard.DRAIN_WINDOW_DEFAULT + 600)
        repo = make_repo_record(
            path="/r/demo", dirty=1, worktrees=[task_worktree(stale_act)]
        )
        inbox = workboard.attention_items([repo], [], [], stale_days=7)

        self.assertEqual(self._states(inbox), ["needs-review"])

    def test_live_and_stale_differ_only_by_worktree_activity(self):
        live = make_repo_record(
            path="/r/demo", dirty=1, worktrees=[task_worktree(workboard.now_ts())]
        )
        stale = make_repo_record(
            path="/r/demo",
            dirty=1,
            worktrees=[
                task_worktree(
                    workboard.now_ts() - (workboard.DRAIN_WINDOW_DEFAULT + 600)
                )
            ],
        )
        live_states = self._states(
            workboard.attention_items([live], [], [], stale_days=7)
        )
        stale_states = self._states(
            workboard.attention_items([stale], [], [], stale_days=7)
        )

        self.assertEqual(live_states, ["in-progress"])
        self.assertEqual(stale_states, ["needs-review"])

    def test_decay_session_gone_returns_to_needs_review(self):
        repo = make_repo_record(path="/r/demo", ahead=1)
        covered = workboard.attention_items(
            [repo], [make_session("/r/demo")], [], stale_days=7
        )
        uncovered = workboard.attention_items([repo], [], [], stale_days=7)

        self.assertEqual(self._states(covered), ["in-progress"])
        self.assertEqual(self._states(uncovered), ["needs-review"])

    def test_decay_worktree_ages_past_window_returns_to_needs_review(self):
        fresh = make_repo_record(
            path="/r/demo", dirty=1, worktrees=[task_worktree(workboard.now_ts())]
        )
        aged = make_repo_record(
            path="/r/demo",
            dirty=1,
            worktrees=[
                task_worktree(workboard.now_ts() - (workboard.DRAIN_WINDOW_DEFAULT + 1))
            ],
        )

        self.assertEqual(
            self._states(workboard.attention_items([fresh], [], [], stale_days=7)),
            ["in-progress"],
        )
        self.assertEqual(
            self._states(workboard.attention_items([aged], [], [], stale_days=7)),
            ["needs-review"],
        )

    def test_nested_session_toplevel_does_not_cover_parent(self):
        # defect 3: a session inside a nested child repo (its toplevel is the
        # child, not the parent) must NOT mark the parent covered.
        parent = make_repo_record(path="/r/parent", dirty=1)
        inbox = workboard.attention_items(
            [parent], [make_session("/r/parent/child")], [], stale_days=7
        )

        self.assertEqual(self._states(inbox), ["needs-review"])

    def test_parked_baton_does_not_suppress_git_state(self):
        # a baton is a paused generation, not proof of a live drain.
        repo = make_repo_record(path="/r/demo", dirty=1)
        repo["batons"] = [
            {
                "path": "specs/x/DRAIN-BATON.md",
                "generation": 2,
                "command": "",
                "needs_attention": "",
                "mtime": 1.0,
            }
        ]
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
        return {
            "path": "specs/x/DRAIN-BATON.md",
            "generation": 3,
            "command": command,
            "needs_attention": needs_attention,
            "mtime": 5.0,
        }

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




def write_session(projects_dir, proj="proj1", sid="sess1", records=None):
    """A session transcript .jsonl with the given records (dicts), oldest first."""
    d = projects_dir / proj
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{sid}.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    return p


class TestSessionStartTs(unittest.TestCase):
    """R6 (workboard half): scan_sessions resolves a start_ts per session,
    keeping the existing last-activity as end_ts."""

    def test_scan_sessions_uses_earliest_transcript_record_as_start_ts(self):
        with tempfile.TemporaryDirectory() as tmp:
            claude_home = Path(tmp)
            write_session(
                claude_home / "projects",
                records=[
                    {
                        "type": "user",
                        "message": {"content": "hi"},
                        "cwd": "/r/demo",
                        "gitBranch": "main",
                        "timestamp": "2020-01-01T00:00:00Z",
                    },
                    {
                        "type": "assistant",
                        "message": {"content": "ok"},
                        "timestamp": "2020-01-01T01:00:00Z",
                    },
                ],
            )

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
            write_session(
                claude_home / "projects",
                records=[
                    {"type": "user", "message": {"content": "hi"}, "cwd": "/r/demo"},
                ],
            )

            sessions = workboard.scan_sessions(claude_home, stale_days=7)

            s = sessions[0]
            self.assertIsNotNone(s["start_ts"])
            self.assertLessEqual(s["start_ts"], s["end_ts"])










class TestLiveSessionIdsCliAndFallback(unittest.TestCase):
    """R1: live_session_ids() sources liveness from the `claude agents --json`
    shim, falling back to the PID-record scan when the shim is absent/invalid,
    and returns the 2-tuple (live, liveness_unknown) in both paths."""

    def _patch_cli(self, result):
        orig = workboard._claude_agents_json
        workboard._claude_agents_json = lambda: result
        self.addCleanup(setattr, workboard, "_claude_agents_json", orig)

    def test_valid_cli_list_yields_liveness_map_ignoring_status(self):
        self._patch_cli(
            [
                {"sessionId": "s1", "pid": 111, "status": "running"},
                {"sessionId": "s2", "pid": 222, "status": "idle"},  # status ignored
                {"pid": 333},  # missing sessionId -> not live
            ]
        )

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
                json.dumps({"sessionId": "s1", "pid": os.getpid()})
            )

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


class TestPruneStaleSessionPids(unittest.TestCase):
    """~/.claude/sessions/*.json PID records accumulate forever once their
    process dies — nothing today ever deletes them. prune_stale_session_pids()
    is the explicit, --flag-gated cleanup (mirrors --abandon-stale's
    explicit-action shape; never runs implicitly during a scan)."""

    def test_prune_removes_dead_pid_keeps_live_pid(self):
        with tempfile.TemporaryDirectory() as tmp:
            claude_home = Path(tmp)
            sess_dir = claude_home / "sessions"
            sess_dir.mkdir()
            (sess_dir / "dead.json").write_text(
                json.dumps({"sessionId": "dead-sid", "pid": 999999})
            )
            (sess_dir / "alive.json").write_text(
                json.dumps({"sessionId": "alive-sid", "pid": os.getpid()})
            )

            removed, kept = workboard.prune_stale_session_pids(claude_home)

            self.assertEqual(removed, ["dead-sid"])
            self.assertEqual(kept, 1)
            self.assertFalse((sess_dir / "dead.json").exists())
            self.assertTrue((sess_dir / "alive.json").exists())

    def test_prune_leaves_malformed_records_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            claude_home = Path(tmp)
            sess_dir = claude_home / "sessions"
            sess_dir.mkdir()
            (sess_dir / "no-pid.json").write_text(json.dumps({"sessionId": "x"}))
            (sess_dir / "bad-json.json").write_text("{not json")

            removed, kept = workboard.prune_stale_session_pids(claude_home)

            self.assertEqual(removed, [])
            self.assertEqual(kept, 2)
            self.assertTrue((sess_dir / "no-pid.json").exists())
            self.assertTrue((sess_dir / "bad-json.json").exists())

    def test_prune_missing_sessions_dir_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            removed, kept = workboard.prune_stale_session_pids(Path(tmp))

        self.assertEqual((removed, kept), ([], 0))


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
        sessions = [{"id": "s1", "cwd": "/r/demo/sub"}, {"id": "s2", "cwd": "/other"}]

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
                "# Notes\nStatus: pending\n", encoding="utf-8"
            )
            (spec_dir / "tasks" / "todo.md").write_text(
                "# Todo\nStatus: pending\n", encoding="utf-8"
            )

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
                "# A\nStatus: done\n", encoding="utf-8"
            )
            (spec_dir / "tasks" / "notes.md").write_text(
                "# Notes\nStatus: pending\n", encoding="utf-8"
            )

            spec = workboard.scan_toolkit_specs(Path(tmp))[0]

            self.assertEqual(spec["tasks_total"], 2)
            self.assertEqual(spec["tasks_unparseable"], 1)




def make_agentprof_stub(tmpdir, stdout_payload, argv_out=None, exit_code=0):
    """Write an executable stub standing in for the agentprof binary.

    It prints `stdout_payload` verbatim (so callers can emit invalid JSON),
    optionally records its argv (one arg per line) to `argv_out`, and exits
    with `exit_code`.
    """
    p = Path(tmpdir) / "agentprof_stub.py"
    lines = ["#!/usr/bin/env python3", "import sys"]
    if argv_out:
        lines.append("open(%r, 'w').write(chr(10).join(sys.argv[1:]))" % str(argv_out))
    lines.append("sys.stdout.write(%r)" % stdout_payload)
    lines.append("sys.exit(%d)" % exit_code)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    p.chmod(0o755)
    return str(p)


class TestSpend(unittest.TestCase):
    """R5/R8/R9: shell out to agentprof, join summary rows to assembled
    sessions, expose under a `spend` key. Failures never raise."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self._old_bin = os.environ.get("AGENTPROF_BIN")

    def tearDown(self):
        if self._old_bin is None:
            os.environ.pop("AGENTPROF_BIN", None)
        else:
            os.environ["AGENTPROF_BIN"] = self._old_bin
        self._tmp.cleanup()

    def _two_session_rows(self):
        return [
            {
                "session": "s1",
                "model": "claude-haiku-4-5-20251001",
                "input_tokens": 100,
                "output_tokens": 10,
                "cache_read_tokens": 5,
                "cache_write_tokens": 2,
                "cost_microusd": 1000,
                "priced": True,
            },
            {
                "session": "s1",
                "model": "claude-sonnet-4-5-20250929",
                "input_tokens": 200,
                "output_tokens": 20,
                "cache_read_tokens": 6,
                "cache_write_tokens": 3,
                "cost_microusd": 5000,
                "priced": True,
            },
            {
                "session": "s2",
                "model": "claude-haiku-4-5-20251001",
                "input_tokens": 50,
                "output_tokens": 5,
                "cache_read_tokens": 1,
                "cache_write_tokens": 1,
                "cost_microusd": 500,
                "priced": True,
            },
            {
                "session": "s2",
                "model": "custom-model",
                "input_tokens": 30,
                "output_tokens": 3,
                "cache_read_tokens": 0,
                "cache_write_tokens": 0,
                "cost_microusd": 0,
                "priced": False,
            },
        ]

    def test_joins_per_session_and_per_model_with_summed_totals(self):
        os.environ["AGENTPROF_BIN"] = make_agentprof_stub(
            self.tmp, json.dumps(self._two_session_rows())
        )

        spend = workboard.compute_spend(self.tmp, {"s1", "s2"})

        self.assertIs(spend["available"], True)
        self.assertIsNone(spend["reason"])

        # per-session: session total is the sum of its model costs
        self.assertEqual(spend["by_session"]["s1"]["cost_microusd"], 6000)
        haiku_s1 = spend["by_session"]["s1"]["models"]["claude-haiku-4-5-20251001"]
        self.assertEqual(haiku_s1["input_tokens"], 100)
        self.assertIs(haiku_s1["priced"], True)
        unpriced = spend["by_session"]["s2"]["models"]["custom-model"]
        self.assertIs(unpriced["priced"], False)
        self.assertEqual(unpriced["cost_microusd"], 0)

        # per-model: aggregated over every joined session
        by_model = {m["model"]: m for m in spend["by_model"]}
        self.assertEqual(by_model["claude-haiku-4-5-20251001"]["input_tokens"], 150)
        self.assertEqual(by_model["claude-haiku-4-5-20251001"]["output_tokens"], 15)
        self.assertEqual(by_model["claude-haiku-4-5-20251001"]["cost_microusd"], 1500)
        self.assertIs(by_model["claude-haiku-4-5-20251001"]["priced"], True)
        self.assertIs(by_model["custom-model"]["priced"], False)

    def test_priced_true_if_any_contributing_row_priced(self):
        rows = [
            {
                "session": "s1",
                "model": "m",
                "input_tokens": 1,
                "output_tokens": 1,
                "cache_read_tokens": 0,
                "cache_write_tokens": 0,
                "cost_microusd": 0,
                "priced": False,
            },
            {
                "session": "s2",
                "model": "m",
                "input_tokens": 1,
                "output_tokens": 1,
                "cache_read_tokens": 0,
                "cache_write_tokens": 0,
                "cost_microusd": 7,
                "priced": True,
            },
        ]
        os.environ["AGENTPROF_BIN"] = make_agentprof_stub(self.tmp, json.dumps(rows))

        spend = workboard.compute_spend(self.tmp, {"s1", "s2"})

        by_model = {m["model"]: m for m in spend["by_model"]}
        self.assertIs(by_model["m"]["priced"], True)

    def test_rows_for_unassembled_sessions_are_dropped(self):
        rows = self._two_session_rows() + [
            {
                "session": "s3",
                "model": "claude-haiku-4-5-20251001",
                "input_tokens": 9999,
                "output_tokens": 9999,
                "cache_read_tokens": 0,
                "cache_write_tokens": 0,
                "cost_microusd": 9999,
                "priced": True,
            },
        ]
        os.environ["AGENTPROF_BIN"] = make_agentprof_stub(self.tmp, json.dumps(rows))

        spend = workboard.compute_spend(self.tmp, {"s1", "s2"})

        self.assertNotIn("s3", spend["by_session"])
        by_model = {m["model"]: m for m in spend["by_model"]}
        # s3's 9999 must not leak into the haiku aggregate
        self.assertEqual(by_model["claude-haiku-4-5-20251001"]["cost_microusd"], 1500)

    def test_missing_binary_yields_unavailable_without_exception(self):
        os.environ["AGENTPROF_BIN"] = "/nonexistent/agentprof"

        spend = workboard.compute_spend(self.tmp, {"s1"})

        self.assertIs(spend["available"], False)
        self.assertTrue(spend["reason"])
        self.assertEqual(spend["by_model"], [])
        self.assertEqual(spend["by_session"], {})

    def test_invalid_json_yields_unavailable(self):
        os.environ["AGENTPROF_BIN"] = make_agentprof_stub(
            self.tmp, "this is not json {"
        )

        spend = workboard.compute_spend(self.tmp, {"s1"})

        self.assertIs(spend["available"], False)
        self.assertTrue(spend["reason"])
        self.assertEqual(spend["by_model"], [])

    def test_invokes_binary_with_pinned_argv(self):
        argv_out = self.tmp / "argv.txt"
        os.environ["AGENTPROF_BIN"] = make_agentprof_stub(
            self.tmp, json.dumps([]), argv_out=argv_out
        )
        claude_dir = self.tmp / "claude-home"

        workboard.compute_spend(claude_dir, {"s1"})

        argv = argv_out.read_text().splitlines()
        self.assertEqual(
            argv,
            [
                "claude",
                "-o",
                "summary",
                "--days",
                "3650",
                "--claude-dir",
                str(claude_dir),
            ],
        )


class TestAntigravitySpend(unittest.TestCase):
    """R4: shell out to `agentprof antigravity`, filter its summary rows by the
    Antigravity cascade ids (a DIFFERENT id-space than Claude session ids), and
    expose them for the merged rollup. Failures never raise."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self._old_bin = os.environ.get("AGENTPROF_BIN")

    def tearDown(self):
        if self._old_bin is None:
            os.environ.pop("AGENTPROF_BIN", None)
        else:
            os.environ["AGENTPROF_BIN"] = self._old_bin
        self._tmp.cleanup()

    def _cascade_rows(self):
        return [
            {
                "session": "cascade-abc",
                "model": "gemini-3-pro",
                "input_tokens": 100,
                "output_tokens": 10,
                "cache_read_tokens": 5,
                "cache_write_tokens": 2,
                "cost_microusd": 4000,
                "priced": True,
            },
            {
                "session": "other-cascade",
                "model": "gemini-3-pro",
                "input_tokens": 9999,
                "output_tokens": 9999,
                "cache_read_tokens": 0,
                "cache_write_tokens": 0,
                "cost_microusd": 9999,
                "priced": True,
            },
        ]

    def test_cascade_id_row_contributes_nonzero_spend(self):
        # A row whose `session` IS a member of the passed cascade_ids must
        # contribute — this is the id-space bug R4 fixes: filtering by the
        # Claude-only session_ids would zero this out.
        os.environ["AGENTPROF_BIN"] = make_agentprof_stub(
            self.tmp, json.dumps(self._cascade_rows())
        )

        spend = workboard.compute_antigravity_spend(self.tmp, {"cascade-abc"})

        self.assertIs(spend["available"], True)
        self.assertEqual(spend["by_session"]["cascade-abc"]["cost_microusd"], 4000)
        by_model = {m["model"]: m for m in spend["by_model"]}
        self.assertEqual(by_model["gemini-3-pro"]["cost_microusd"], 4000)

    def test_rows_outside_cascade_ids_are_dropped(self):
        os.environ["AGENTPROF_BIN"] = make_agentprof_stub(
            self.tmp, json.dumps(self._cascade_rows())
        )

        spend = workboard.compute_antigravity_spend(self.tmp, {"cascade-abc"})

        self.assertNotIn("other-cascade", spend["by_session"])
        by_model = {m["model"]: m for m in spend["by_model"]}
        # other-cascade's 9999 must not leak into the aggregate
        self.assertEqual(by_model["gemini-3-pro"]["cost_microusd"], 4000)

    def test_invokes_binary_with_antigravity_argv(self):
        argv_out = self.tmp / "argv.txt"
        os.environ["AGENTPROF_BIN"] = make_agentprof_stub(
            self.tmp, json.dumps([]), argv_out=argv_out
        )
        ag_dir = self.tmp / "ag-home"

        workboard.compute_antigravity_spend(ag_dir, {"cascade-abc"})

        argv = argv_out.read_text().splitlines()
        self.assertEqual(
            argv,
            [
                "antigravity",
                "-o",
                "summary",
                "--antigravity-dir",
                str(ag_dir),
                "--days",
                "3650",
            ],
        )

    def test_missing_binary_yields_unavailable_without_exception(self):
        os.environ["AGENTPROF_BIN"] = "/nonexistent/agentprof"

        spend = workboard.compute_antigravity_spend(self.tmp, {"cascade-abc"})

        self.assertIs(spend["available"], False)
        self.assertTrue(spend["reason"])
        self.assertEqual(spend["by_model"], [])
        self.assertEqual(spend["by_session"], {})


class TestMergeSpend(unittest.TestCase):
    """R4: merge Claude + Antigravity spend into one drop-in structure so
    `render_spend_section` needs no changes — concatenate-and-resort by_model,
    union by_session, OR availability, and degrade each harness independently."""

    def _model(self, model, cost, priced=True):
        return {
            "model": model,
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "cost_microusd": cost,
            "priced": priced,
        }

    def _avail(self, by_model, by_session):
        return {
            "by_model": by_model,
            "by_session": by_session,
            "available": True,
            "reason": None,
        }

    def _unavail(self, reason):
        return {
            "by_model": [],
            "by_session": {},
            "available": False,
            "reason": reason,
        }

    def test_by_model_is_concatenated_and_resorted_by_cost(self):
        # Each harness list is internally sorted, but a cheaper Claude model
        # ahead of a costlier Antigravity model must be re-sorted across the
        # merge — not left as two separately-sorted blocks.
        claude = self._avail([self._model("claude-z", 300)], {})
        antig = self._avail([self._model("gemini-a", 500)], {})

        merged = workboard.merge_spend(claude, antig)

        self.assertEqual(
            [m["model"] for m in merged["by_model"]], ["gemini-a", "claude-z"]
        )

    def test_by_session_is_union_of_both(self):
        claude = self._avail([], {"claude-s1": {"cost_microusd": 1}})
        antig = self._avail([], {"cascade-c1": {"cost_microusd": 2}})

        merged = workboard.merge_spend(claude, antig)

        self.assertIn("claude-s1", merged["by_session"])
        self.assertIn("cascade-c1", merged["by_session"])

    def test_available_is_or_of_both_harnesses(self):
        claude = self._avail([self._model("claude-z", 300)], {"s1": {}})
        antig = self._unavail("agentprof antigravity boom")

        merged = workboard.merge_spend(claude, antig)

        self.assertIs(merged["available"], True)
        self.assertIs(merged["claude_available"], True)
        self.assertIs(merged["antigravity_available"], False)
        self.assertTrue(merged["antigravity_reason"])

    def test_broken_antigravity_does_not_blank_claude_rows(self):
        claude = self._avail(
            [self._model("claude-z", 300)], {"claude-s1": {"cost_microusd": 300}}
        )
        antig = self._unavail("boom")

        merged = workboard.merge_spend(claude, antig)

        self.assertEqual([m["model"] for m in merged["by_model"]], ["claude-z"])
        self.assertIn("claude-s1", merged["by_session"])

    def test_broken_claude_does_not_blank_antigravity_rows(self):
        claude = self._unavail("boom")
        antig = self._avail(
            [self._model("gemini-a", 500)], {"cascade-c1": {"cost_microusd": 500}}
        )

        merged = workboard.merge_spend(claude, antig)

        self.assertEqual([m["model"] for m in merged["by_model"]], ["gemini-a"])
        self.assertIn("cascade-c1", merged["by_session"])

    def test_both_unavailable_reports_unavailable_with_reason(self):
        merged = workboard.merge_spend(
            self._unavail("claude down"), self._unavail("antigravity down")
        )

        self.assertIs(merged["available"], False)
        self.assertTrue(merged["reason"])

    def test_real_failed_antigravity_call_preserves_claude_spend(self):
        # End-to-end: a genuine subprocess failure on the Antigravity side must
        # not blank the rows the Claude call populated.
        tmpdir = tempfile.TemporaryDirectory()
        try:
            tmp = Path(tmpdir.name)
            old_bin = os.environ.get("AGENTPROF_BIN")
            try:
                claude_rows = [
                    {
                        "session": "s1",
                        "model": "claude-haiku-4-5-20251001",
                        "input_tokens": 1,
                        "output_tokens": 1,
                        "cache_read_tokens": 0,
                        "cache_write_tokens": 0,
                        "cost_microusd": 1000,
                        "priced": True,
                    }
                ]
                os.environ["AGENTPROF_BIN"] = make_agentprof_stub(
                    tmp, json.dumps(claude_rows)
                )
                claude = workboard.compute_spend(tmp, {"s1"})
                os.environ["AGENTPROF_BIN"] = "/nonexistent/agentprof"
                antig = workboard.compute_antigravity_spend(tmp, {"cascade-abc"})
            finally:
                if old_bin is None:
                    os.environ.pop("AGENTPROF_BIN", None)
                else:
                    os.environ["AGENTPROF_BIN"] = old_bin

            merged = workboard.merge_spend(claude, antig)

            self.assertIs(merged["available"], True)
            self.assertGreater(len(merged["by_model"]), 0)
            self.assertIn("s1", merged["by_session"])
            self.assertIs(merged["antigravity_available"], False)
        finally:
            tmpdir.cleanup()




# ---- Unblock lines + Deferred questions (unblock-next-steps task 01) -------


def _write_unblock_spec(root, slug="demo", spec_body="# Demo\n", tasks=None):
    """Write a specs/<slug>/ tree; `tasks` maps filename → body text."""
    spec = Path(root) / "specs" / slug
    (spec / "tasks").mkdir(parents=True)
    (spec / "SPEC.md").write_text(spec_body, encoding="utf-8")
    for name, body in (tasks or {}).items():
        (spec / "tasks" / name).write_text(body, encoding="utf-8")
    return spec


class TestUnblockParsing(unittest.TestCase):
    def _scan_task(self, body, name="01-a.md"):
        with tempfile.TemporaryDirectory() as tmp:
            _write_unblock_spec(tmp, tasks={name: body})
            specs = workboard.scan_toolkit_specs(Path(tmp))
        return specs[0]["tasks"][0]

    def test_blocked_task_with_ask_unblock_parses_type_and_step(self):
        t = self._scan_task("# A\nStatus: blocked\nUnblock: ask: which creds?\n")
        self.assertEqual(t["unblock"], {"type": "ask", "step": "which creds?"})

    def test_blocked_task_with_run_unblock_parses(self):
        t = self._scan_task("# A\nStatus: blocked\nUnblock: run: make deploy\n")
        self.assertEqual(t["unblock"], {"type": "run", "step": "make deploy"})

    def test_blocked_task_with_agent_unblock_parses(self):
        t = self._scan_task("# A\nStatus: blocked\nUnblock: agent: check the deploy\n")
        self.assertEqual(t["unblock"], {"type": "agent", "step": "check the deploy"})

    def test_malformed_unblock_line_yields_no_unblock_key(self):
        t = self._scan_task("# A\nStatus: blocked\nUnblock: someday soon\n")
        self.assertNotIn("unblock", t)

    def test_unblock_line_on_non_blocked_task_is_ignored(self):
        t = self._scan_task("# A\nStatus: pending\nUnblock: ask: which creds?\n")
        self.assertNotIn("unblock", t)

    def test_deferred_questions_section_appears_in_task_json(self):
        body = (
            "# A\nStatus: blocked\n\n"
            "## Deferred questions\n\n"
            "- which auth provider?\n- what is the base URL?\n"
        )
        t = self._scan_task(body)
        self.assertEqual(len(t["deferred_questions"]), 2)
        self.assertIn("what is the base URL?", t["deferred_questions"])


class TestWaitingSpecUnblock(unittest.TestCase):
    def test_waiting_spec_header_surfaces_unblock_and_counts_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_unblock_spec(
                tmp,
                spec_body="# Demo\nStatus: waiting\nUnblock: agent: check the deploy\n",
            )
            specs = workboard.scan_toolkit_specs(Path(tmp))
        s = specs[0]
        self.assertEqual(s["unblock"], {"type": "agent", "step": "check the deploy"})
        self.assertEqual(s["status"], "waiting")
        # a waiting spec (no completed tasks) still counts among open specs
        self.assertTrue(s["tasks_total"] == 0 or s["tasks_done"] < s["tasks_total"])

    def test_spec_without_status_header_has_no_unblock_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_unblock_spec(tmp, spec_body="# Demo\n")
            specs = workboard.scan_toolkit_specs(Path(tmp))
        self.assertNotIn("unblock", specs[0])


def _unblock_task(status="blocked", unblock=None, deferred=None, name="01-a.md"):
    t = {
        "file": f"specs/demo/tasks/{name}",
        "abs": f"/x/{name}",
        "title": name,
        "status": status,
        "deps": [],
    }
    if unblock:
        t["unblock"] = unblock
    if deferred:
        t["deferred_questions"] = deferred
    return t


def _unblock_spec(tasks, status=None, unblock=None):
    s = {
        "kind": "toolkit",
        "slug": "demo",
        "title": "Demo",
        "priority": "",
        "path": "specs/demo/SPEC.md",
        "tasks_total": len(tasks) or 1,
        "tasks_done": 0,
        "tasks_doing": 0,
        "tasks_blocked": [
            t["file"] for t in tasks if workboard._task_is_blocked(t["status"])
        ],
        "tasks": tasks,
        "tasks_unparseable": 0,
        # fresh, so the stale branch never fires in these fixtures
        "last_touched": workboard.now_ts(),
    }
    if status:
        s["status"] = status
    if unblock:
        s["unblock"] = unblock
    return s




class TestNeedsAnswerInbox(unittest.TestCase):
    def _repo(self, spec):
        repo = make_repo_record(path="/r/demo")
        repo["specs"] = [spec]
        return repo

    def _inbox(self, spec):
        return workboard.attention_items([self._repo(spec)], [], [], stale_days=7)

    def test_ask_unblock_becomes_needs_answer_item_without_cmd(self):
        spec = _unblock_spec(
            [_unblock_task(unblock={"type": "ask", "step": "which creds?"})]
        )
        answer = [i for i in self._inbox(spec) if i["state"] == "needs-answer"]
        self.assertEqual(len(answer), 1)
        self.assertIn("which creds?", answer[0]["why"])
        self.assertNotIn("cmd", answer[0])

    def test_deferred_question_becomes_needs_answer_item_without_cmd(self):
        spec = _unblock_spec([_unblock_task(deferred=["which provider?"])])
        answer = [i for i in self._inbox(spec) if i["state"] == "needs-answer"]
        self.assertEqual(len(answer), 1)
        self.assertIn("which provider?", answer[0]["why"])
        self.assertNotIn("cmd", answer[0])

    def test_run_unblock_is_not_a_needs_answer_item(self):
        spec = _unblock_spec([_unblock_task(unblock={"type": "run", "step": "make x"})])
        self.assertEqual(
            [i for i in self._inbox(spec) if i["state"] == "needs-answer"], []
        )

    def test_run_unblock_task_is_not_an_inbox_item(self):
        # Agent-bounded: a recorded run:/agent: unblock step means the work
        # proceeds (recheck/dispatch), it is not the human's attention item.
        spec = _unblock_spec(
            [_unblock_task(unblock={"type": "run", "step": "make deploy"})]
        )
        self.assertEqual(self._inbox(spec), [])

    def test_agent_unblock_task_is_not_an_inbox_item(self):
        spec = _unblock_spec(
            [_unblock_task(unblock={"type": "agent", "step": "recheck deploy"})]
        )
        self.assertEqual(self._inbox(spec), [])

    def test_draft_task_is_not_an_inbox_item(self):
        # Drafts are queue state (intake promotes them); decision-shaped
        # drafts surface via HUMAN.md entries, not the spec-blocked row.
        spec = _unblock_spec([_unblock_task(status="draft")])
        self.assertEqual(self._inbox(spec), [])

    def test_blocked_task_without_unblock_still_flags(self):
        # Unknown-bounded: no recorded unblock step — surface it.
        spec = _unblock_spec([_unblock_task()])
        blocked = [i for i in self._inbox(spec) if i["state"] == "blocked"]
        self.assertEqual(len(blocked), 1)
        self.assertIn("no unblock step recorded", blocked[0]["why"])

    def test_ask_unblock_task_does_not_duplicate_spec_blocked_row(self):
        # The ask task already has its own needs-answer row; the spec-level
        # blocked row must not repeat it.
        spec = _unblock_spec(
            [_unblock_task(unblock={"type": "ask", "step": "which creds?"})]
        )
        inbox = self._inbox(spec)
        self.assertEqual([i["state"] for i in inbox], ["needs-answer"])

    def test_waiting_spec_ask_unblock_becomes_needs_answer(self):
        spec = _unblock_spec(
            [], status="waiting", unblock={"type": "ask", "step": "sign in at URL?"}
        )
        answer = [i for i in self._inbox(spec) if i["state"] == "needs-answer"]
        self.assertEqual(len(answer), 1)
        self.assertIn("sign in at URL?", answer[0]["why"])
        self.assertNotIn("cmd", answer[0])

    def test_waiting_spec_agent_unblock_is_not_an_inbox_item(self):
        # Agent-bounded: the recheck step proceeds; not an attention item.
        spec = _unblock_spec(
            [], status="waiting", unblock={"type": "agent", "step": "check deploy"}
        )
        self.assertEqual(self._inbox(spec), [])

    def test_waiting_spec_without_unblock_still_flags(self):
        spec = _unblock_spec([], status="waiting")
        blocked = [i for i in self._inbox(spec) if i["state"] == "blocked"]
        self.assertEqual(len(blocked), 1)
        self.assertIn("no unblock step recorded", blocked[0]["why"])



def _agent_tool_use(tool_use_id, subagent_type="scout", desc="do the thing", ts=OLD_TS):
    """An assistant record spawning a sub-agent (real transcript shape:
    message.content holds a tool_use block named "Agent")."""
    return {
        "type": "assistant",
        "timestamp": ts,
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "name": "Agent",
                    "id": tool_use_id,
                    "input": {"description": desc, "subagent_type": subagent_type},
                }
            ]
        },
    }


def _agent_tool_result(
    tool_use_id, agent_id, status="completed", ts="2020-01-01T00:05:00Z"
):
    """A user record returning a sub-agent result. The terminal outcome the
    harness records lives in the top-level `toolUseResult.status`, alongside
    the spawned `agentId` — mirrors real transcripts."""
    return {
        "type": "user",
        "timestamp": ts,
        "toolUseResult": {"status": status, "agentId": agent_id},
        "message": {
            "content": [
                {"type": "tool_result", "tool_use_id": tool_use_id, "content": "ok"}
            ]
        },
    }


def write_spawn_fixture(root, session_id, session_records, subagents):
    """Build a session transcript + its `subagents/` sibling dir, matching the
    real on-disk layout: `<root>/<session_id>.jsonl` is the parent transcript;
    `<root>/<session_id>/subagents/agent-<id>.{jsonl,meta.json}` are the
    spawned sub-agents. `subagents` is a list of (agent_id, meta, records).
    The subagents dir is only created when there is at least one sub-agent."""
    proj = Path(root)
    proj.mkdir(parents=True, exist_ok=True)
    session_path = proj / f"{session_id}.jsonl"
    session_path.write_text(
        "\n".join(json.dumps(r) for r in session_records) + "\n", encoding="utf-8"
    )
    if subagents:
        subdir = proj / session_id / "subagents"
        subdir.mkdir(parents=True)
        for aid, meta, recs in subagents:
            (subdir / f"agent-{aid}.meta.json").write_text(
                json.dumps(meta), encoding="utf-8"
            )
            body = "\n".join(json.dumps(r) for r in recs)
            (subdir / f"agent-{aid}.jsonl").write_text(
                (body + "\n") if body else "", encoding="utf-8"
            )
    return session_path


class TestExtractAgentTree(unittest.TestCase):
    """R1-R4: extract_agent_tree parses a session transcript's Agent/Task
    spawns into a nested tree, recursing through each sub-agent's own
    transcript so grandchildren nest under their parent."""

    def test_extract_agent_tree_nests_grandchild_under_parent(self):
        # Session spawns A (depth 1); A's own transcript spawns B (depth 2).
        with tempfile.TemporaryDirectory() as tmp:
            session_records = [
                _agent_tool_use("TU_A", subagent_type="implementation-worker"),
                _agent_tool_result("TU_A", "A"),
            ]
            meta_a = {
                "agentType": "implementation-worker",
                "description": "parent work",
                "toolUseId": "TU_A",
                "spawnDepth": 1,
            }
            agent_a_records = [
                _agent_tool_use("TU_B", subagent_type="scout"),
                _agent_tool_result("TU_B", "B"),
            ]
            meta_b = {
                "agentType": "scout",
                "description": "child work",
                "toolUseId": "TU_B",
                "spawnDepth": 2,
            }
            session_path = write_spawn_fixture(
                tmp,
                "sess-nest",
                session_records,
                [("A", meta_a, agent_a_records), ("B", meta_b, [])],
            )

            tree = workboard.extract_agent_tree(session_path)

            root_ids = [n["agentId"] for n in tree]
            self.assertEqual(root_ids, ["A"])  # B is NOT a root
            child_ids = [c["agentId"] for c in tree[0]["children"]]
            self.assertEqual(child_ids, ["B"])  # B nested under A
            self.assertEqual(tree[0]["children"][0]["spawnDepth"], 2)

    def test_extract_agent_tree_empty_for_no_agent_calls(self):
        # A session that never spawned a sub-agent -> empty tree, no exception.
        with tempfile.TemporaryDirectory() as tmp:
            session_records = [
                {
                    "type": "user",
                    "timestamp": OLD_TS,
                    "message": {"content": "hi"},
                },
                {
                    "type": "assistant",
                    "timestamp": OLD_TS,
                    "message": {"content": [{"type": "text", "text": "ok"}]},
                },
            ]
            session_path = write_spawn_fixture(tmp, "sess-empty", session_records, [])

            self.assertEqual(workboard.extract_agent_tree(session_path), [])

    def test_extract_agent_tree_node_fields(self):
        # Every node exposes the R2 minimum field set, with derived values.
        with tempfile.TemporaryDirectory() as tmp:
            session_records = [
                _agent_tool_use("TU_A", desc="verify it", ts="2020-01-01T00:00:00Z"),
                _agent_tool_result("TU_A", "A", status="completed"),
            ]
            meta_a = {
                "agentType": "verifier",
                "description": "verify it",
                "toolUseId": "TU_A",
                "spawnDepth": 1,
            }
            session_path = write_spawn_fixture(
                tmp, "sess-fields", session_records, [("A", meta_a, [])]
            )

            tree = workboard.extract_agent_tree(session_path)

            self.assertEqual(len(tree), 1)
            node = tree[0]
            for field in (
                "agentId",
                "agentType",
                "description",
                "status",
                "spawnDepth",
                "started_ts",
            ):
                self.assertIn(field, node)
            self.assertEqual(node["agentId"], "A")
            self.assertEqual(node["agentType"], "verifier")
            self.assertEqual(node["description"], "verify it")
            self.assertEqual(node["status"], "completed")
            self.assertEqual(node["spawnDepth"], 1)
            self.assertEqual(
                node["started_ts"], workboard.iso_to_ts("2020-01-01T00:00:00Z")
            )

    def test_extract_agent_tree_maps_error_status_to_failed(self):
        # A sub-agent whose recorded outcome is an error reads as "failed"
        # (fleet's status vocabulary), distinguishing a broken branch (R2/R7).
        with tempfile.TemporaryDirectory() as tmp:
            session_records = [
                _agent_tool_use("TU_A"),
                _agent_tool_result("TU_A", "A", status="error"),
            ]
            meta_a = {
                "agentType": "scout",
                "description": "broke",
                "toolUseId": "TU_A",
                "spawnDepth": 1,
            }
            session_path = write_spawn_fixture(
                tmp, "sess-fail", session_records, [("A", meta_a, [])]
            )

            tree = workboard.extract_agent_tree(session_path)

            self.assertEqual(tree[0]["status"], "failed")


class TestScanSessionSpawns(unittest.TestCase):
    """R5/R8: scan_session_spawns() runs extract_agent_tree() per session and
    returns records keyed to the scan_*() contract (last_touched/last_ts) for
    merge into each session record inside assemble(), without perturbing any
    other scan_*() function's output."""

    def _home_with_spawning_session(self, tmp, sid="sess-x"):
        """Build a claude_home/projects/<proj>/ tree holding one session that
        spawned a sub-agent. Returns (home_path, session_id)."""
        home = Path(tmp)
        proj = home / "projects" / "proj-x"
        session_records = [
            _agent_tool_use("TU_A", subagent_type="implementation-worker"),
            _agent_tool_result("TU_A", "A", status="completed"),
        ]
        meta_a = {
            "agentType": "implementation-worker",
            "description": "did the work",
            "toolUseId": "TU_A",
            "spawnDepth": 1,
        }
        write_spawn_fixture(proj, sid, session_records, [("A", meta_a, [])])
        return home, sid

    def test_scan_session_spawns_record_carries_tree_and_ts(self):
        # A spawning session's record exposes a non-empty spawn_tree plus the
        # scan_*() contract keys last_touched/last_ts.
        with tempfile.TemporaryDirectory() as tmp:
            home, sid = self._home_with_spawning_session(tmp)

            spawns = workboard.scan_session_spawns(home)

            self.assertIn(sid, spawns)
            rec = spawns[sid]
            self.assertTrue(rec["spawn_tree"])  # non-empty
            self.assertEqual(rec["spawn_tree"][0]["agentId"], "A")
            self.assertIn("last_touched", rec)
            self.assertIn("last_ts", rec)
            self.assertIsNotNone(rec["last_ts"])

    def test_scan_session_spawns_empty_tree_for_non_spawning_session(self):
        # A session that never spawned a sub-agent still gets a record, with an
        # empty spawn_tree (R3-consistent) — never an error.
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            proj = home / "projects" / "proj-y"
            records = [
                {"type": "user", "timestamp": OLD_TS, "message": {"content": "hi"}},
            ]
            write_spawn_fixture(proj, "sess-plain", records, [])

            spawns = workboard.scan_session_spawns(home)

            self.assertIn("sess-plain", spawns)
            self.assertEqual(spawns["sess-plain"]["spawn_tree"], [])

    def test_scan_session_spawns_output_is_json_serializable(self):
        # R8: the per-session tree data is JSON-serializable so --json can carry
        # it without a serialization error.
        with tempfile.TemporaryDirectory() as tmp:
            home, sid = self._home_with_spawning_session(tmp)

            spawns = workboard.scan_session_spawns(home)
            round_tripped = json.loads(json.dumps(spawns))

            self.assertTrue(round_tripped[sid]["spawn_tree"])

    def test_scan_session_spawns_leaves_other_scans_unchanged(self):
        # R5: invoking scan_session_spawns() must not perturb any other
        # scan_*() function's return value — it is read-only. Compare each
        # other scan's output taken before and after the spawn scan runs.
        with tempfile.TemporaryDirectory() as tmp:
            home, _ = self._home_with_spawning_session(tmp)
            (home / "todos").mkdir()
            (home / "todos" / "sess-x-agent-1.json").write_text(
                json.dumps({"todos": [{"status": "pending", "content": "do it"}]}),
                encoding="utf-8",
            )

            before_sessions = workboard.scan_sessions(home, 14)
            before_todos = workboard.scan_todos(home)

            workboard.scan_session_spawns(home)

            after_sessions = workboard.scan_sessions(home, 14)
            after_todos = workboard.scan_todos(home)

            self.assertEqual(before_sessions, after_sessions)
            self.assertEqual(before_todos, after_todos)


class TestFindReposDetectsJj(unittest.TestCase):
    """find_repos treats a `.jj/`-only directory as a repo root, like `.git/`.

    Antigravity's runtime prioritizes `.jj` over `.git` in colocated repos, so
    a jj-only checkout must be discovered, not misread as "not a repo".
    """

    def test_jj_only_directory_is_detected_as_repo_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "jjrepo"
            (repo / ".jj").mkdir(parents=True)
            found = {p.resolve() for p in workboard.find_repos([tmp], max_depth=5)}
            self.assertIn(repo.resolve(), found)


HUMAN_MD_FIXTURE = (
    "# Human blockers\n"
    "\n"
    "Hand-written narrative an agent must never touch.\n"
    "\n"
    "## Agent-filed blockers\n"
    "\n"
    "- [ ] 2026-07-12 · specs/foo/tasks/02.md · ask — "
    "Which auth provider should we use?\n"
    "- [ ] 2026-07-11 · scripts/deploy.sh · run — "
    "Run the prod migration manually\n"
    "- [x] 2026-07-10 · specs/bar/SPEC.md · decide — "
    "Resolved, awaiting sweep\n"
)


class TestScanHumanBlockers(unittest.TestCase):
    """R4: HUMAN.md `## Agent-filed blockers` scanner — open entries only."""

    def test_two_open_one_checked_yields_two_open_blockers(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "HUMAN.md").write_text(HUMAN_MD_FIXTURE, encoding="utf-8")
            blockers = workboard.scan_human_blockers(Path(tmp))
            self.assertEqual(len(blockers), 2)
            types = [b["type"] for b in blockers]
            self.assertIn("ask", types)
            self.assertIn("run", types)
            self.assertNotIn("decide", types)  # the checked entry is skipped

    def test_fields_are_parsed_from_the_grammar(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "HUMAN.md").write_text(HUMAN_MD_FIXTURE, encoding="utf-8")
            blockers = workboard.scan_human_blockers(Path(tmp))
            ask = next(b for b in blockers if b["type"] == "ask")
            self.assertEqual(ask["date"], "2026-07-12")
            self.assertEqual(ask["source"], "specs/foo/tasks/02.md")
            self.assertEqual(ask["ask"], "Which auth provider should we use?")

    def test_no_human_md_returns_empty_no_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(workboard.scan_human_blockers(Path(tmp)), [])

    def test_human_md_without_section_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "HUMAN.md").write_text(
                "# Human blockers\n\nJust narrative, no machine section.\n",
                encoding="utf-8",
            )
            self.assertEqual(workboard.scan_human_blockers(Path(tmp)), [])


class TestHumanBlockersInbox(unittest.TestCase):
    """R4: parsed blockers surface as inbox rows above spec/task rows."""

    def _human_rows(self, inbox):
        return [i for i in inbox if "human blocker" in i["what"].lower()]

    def test_fixture_pair_two_open_one_checked_gives_two_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "HUMAN.md").write_text(HUMAN_MD_FIXTURE, encoding="utf-8")
            repo = make_repo_record(path=tmp)
            repo["human_blockers"] = workboard.scan_human_blockers(Path(tmp))
            inbox = workboard.attention_items([repo], [], [], stale_days=7)
            rows = self._human_rows(inbox)
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(r["severity"] == "serious" for r in rows))
            self.assertTrue(any("auth provider" in r["what"] for r in rows))

    def test_repo_without_human_md_gives_no_rows_no_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo_record(path=tmp)
            repo["human_blockers"] = workboard.scan_human_blockers(Path(tmp))
            inbox = workboard.attention_items([repo], [], [], stale_days=7)
            self.assertEqual(self._human_rows(inbox), [])

    def test_human_blockers_rank_above_spec_task_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "HUMAN.md").write_text(HUMAN_MD_FIXTURE, encoding="utf-8")
            repo = make_repo_record(path=tmp)
            repo["human_blockers"] = workboard.scan_human_blockers(Path(tmp))
            repo["specs"] = [
                {
                    "slug": "demo",
                    "status": None,
                    "tasks_total": 2,
                    "tasks_done": 0,
                    "tasks_blocked": ["01-x"],
                    "tasks": [
                        {
                            "file": "specs/demo/tasks/01-x.md",
                            "abs": "/r/demo/specs/demo/tasks/01-x.md",
                            "title": "x",
                            "status": "blocked",
                            "deps": [],
                        }
                    ],
                    "last_touched": 10.0,
                }
            ]
            inbox = workboard.attention_items([repo], [], [], stale_days=7)
            first_human = next(
                idx
                for idx, i in enumerate(inbox)
                if "human blocker" in i["what"].lower()
            )
            first_spec = next(
                idx for idx, i in enumerate(inbox) if i["what"].startswith("Spec ")
            )
            self.assertLess(first_human, first_spec)


if __name__ == "__main__":
    unittest.main()
