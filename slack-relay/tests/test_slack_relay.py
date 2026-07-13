"""Tests for slack_relay's pure logic: new-question diffing, reply
eligibility filtering, the compare-and-swap answer write, and the
owner-lease relaunch guard.

No real network or subprocess calls: Slack HTTP is a fake object passed in,
git repos are real throwaway tempdirs, and the relaunch decision is tested
separately from the (thin, untested-by-unit-test) subprocess invocation —
mirroring test_dispatch_runtime.py's stub-binary philosophy of keeping I/O
shells thin enough that only the decision logic needs coverage.

Import-by-path mirrors test_dispatch_runtime.py (agent-console.py has a
hyphen, so slack_relay.py — its sibling — is loaded the same way here for
consistency, even though its own name has no hyphen).
"""

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "slack_relay", str(Path(__file__).resolve().parent.parent / "slack_relay.py")
)
sr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sr)


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _init_repo(repo):
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")


def _write_task(repo, spec, task_name, status, questions=None, extra=""):
    task_dir = repo / "specs" / spec / "tasks"
    task_dir.mkdir(parents=True, exist_ok=True)
    body = f"Status: {status}\n\n# {task_name}\n{extra}\n"
    if questions:
        body += "\n## Deferred questions\n\n"
        for q in questions:
            body += f"- {q}\n"
    (task_dir / task_name).write_text(body, encoding="utf-8")
    (repo / "specs" / spec / "SPEC.md").write_text(f"# {spec}\n", encoding="utf-8")
    return task_dir / task_name


class TestFindDeferredTasks(unittest.TestCase):
    def test_finds_deferred_task_with_questions_ignores_others(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            _init_repo(repo)
            _write_task(repo, "spec-a", "01-x.md", "deferred", ["what channel?"])
            _write_task(repo, "spec-a", "02-y.md", "pending")

            found = sr.find_deferred_tasks([repo])

            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]["questions"], ["what channel?"])
            self.assertEqual(found[0]["spec_slug"], "spec-a")

    def test_deferred_task_without_questions_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            _init_repo(repo)
            _write_task(repo, "spec-a", "01-x.md", "deferred")

            self.assertEqual(sr.find_deferred_tasks([repo]), [])


class TestDiffNewQuestions(unittest.TestCase):
    def test_new_question_not_in_state_is_returned(self):
        found = [
            {"repo": "/r", "task_rel": "specs/a/tasks/01-x.md", "questions": ["q1"]}
        ]
        state = {"posted": {}}

        new = sr.diff_new_questions(found, state)

        self.assertEqual(len(new), 1)

    def test_same_question_already_posted_is_not_returned(self):
        item = {"repo": "/r", "task_rel": "specs/a/tasks/01-x.md", "questions": ["q1"]}
        key = sr.question_key(item)
        state = {"posted": {key: {"ts": "123.456"}}}

        self.assertEqual(sr.diff_new_questions([item], state), [])

    def test_task_redeferred_with_new_question_text_posts_again(self):
        old = {"repo": "/r", "task_rel": "specs/a/tasks/01-x.md", "questions": ["q1"]}
        state = {"posted": {sr.question_key(old): {"ts": "123.456"}}}
        new_item = {
            "repo": "/r",
            "task_rel": "specs/a/tasks/01-x.md",
            "questions": ["q2 (new)"],
        }

        self.assertEqual(len(sr.diff_new_questions([new_item], state)), 1)


class TestReplyEligibility(unittest.TestCase):
    """Only a thread-scoped reply, from the exact authorized user, not
    already processed, and within the staleness window counts as an
    answer."""

    def _posted(self, ts="1000.0"):
        return {"ts": ts, "channel": "C1", "posted_ts": 1000.0}

    def test_eligible_reply_from_authorized_user_in_thread(self):
        reply = {"ts": "1005.0", "thread_ts": "1000.0", "user": "U-ME", "text": "yes"}

        ok = sr.is_eligible_reply(
            reply,
            self._posted(),
            authorized_user_id="U-ME",
            now_ts=1005.0,
            max_reply_age_days=14,
        )
        self.assertTrue(ok)

    def test_reply_from_other_user_is_ignored(self):
        reply = {
            "ts": "1005.0",
            "thread_ts": "1000.0",
            "user": "U-OTHER",
            "text": "yes",
        }

        ok = sr.is_eligible_reply(
            reply,
            self._posted(),
            authorized_user_id="U-ME",
            now_ts=1005.0,
            max_reply_age_days=14,
        )
        self.assertFalse(ok)

    def test_bare_channel_message_not_in_thread_is_ignored(self):
        reply = {"ts": "1005.0", "thread_ts": "999.0", "user": "U-ME", "text": "yes"}

        ok = sr.is_eligible_reply(
            reply,
            self._posted(),
            authorized_user_id="U-ME",
            now_ts=1005.0,
            max_reply_age_days=14,
        )
        self.assertFalse(ok)

    def test_reply_older_than_max_age_from_posting_is_ignored(self):
        posted = self._posted()  # posted_ts = 1000.0
        stale_reply_ts = 1000.0 + (15 * 86400)  # 15 days later
        reply = {
            "ts": str(stale_reply_ts),
            "thread_ts": "1000.0",
            "user": "U-ME",
            "text": "yes",
        }

        ok = sr.is_eligible_reply(
            reply,
            posted,
            authorized_user_id="U-ME",
            now_ts=stale_reply_ts,
            max_reply_age_days=14,
        )
        self.assertFalse(ok)

    def test_already_processed_reply_ts_is_ignored(self):
        posted = self._posted()
        posted["processed_reply_ts"] = ["1005.0"]
        reply = {"ts": "1005.0", "thread_ts": "1000.0", "user": "U-ME", "text": "yes"}

        ok = sr.is_eligible_reply(
            reply,
            posted,
            authorized_user_id="U-ME",
            now_ts=1005.0,
            max_reply_age_days=14,
        )
        self.assertFalse(ok)


class TestWriteAnswer(unittest.TestCase):
    """The compare-and-swap write: only proceeds if Status is still
    `deferred` at write time, appends under ## Answers, flips Status, and
    commits path-scoped to that one file."""

    def test_writes_answer_flips_status_and_commits(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            _init_repo(repo)
            task_file = _write_task(repo, "spec-a", "01-x.md", "deferred", ["q1"])
            _git(repo, "add", "-A")
            _git(repo, "commit", "-q", "-m", "init")

            ok = sr.write_answer(
                repo, task_file, "the answer text", source="slack-relay"
            )

            self.assertTrue(ok)
            text = task_file.read_text(encoding="utf-8")
            self.assertIn("## Answers", text)
            self.assertIn("the answer text", text)
            self.assertRegex(text, r"(?m)^Status: pending$")
            log = subprocess.run(
                ["git", "log", "-1", "--name-only", "--format=%s"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            self.assertIn(str(task_file.relative_to(repo)), log)

    def test_refuses_when_status_already_moved_on(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            _init_repo(repo)
            task_file = _write_task(repo, "spec-a", "01-x.md", "pending", ["q1"])
            _git(repo, "add", "-A")
            _git(repo, "commit", "-q", "-m", "init")

            ok = sr.write_answer(
                repo, task_file, "the answer text", source="slack-relay"
            )

            self.assertFalse(ok)
            self.assertNotIn("## Answers", task_file.read_text(encoding="utf-8"))


class TestOwnerLeaseFresh(unittest.TestCase):
    """A best-effort advisory guard, not a safety-critical one — drain's own
    compare-and-swap owner claim is what actually prevents double-dispatch;
    this only avoids an unnecessary relaunch in the common case."""

    def test_no_owner_file_means_not_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec_dir = Path(tmp) / "specs" / "a"
            spec_dir.mkdir(parents=True)

            self.assertFalse(sr.is_owner_lease_fresh(spec_dir, window_seconds=900))

    def test_owner_file_present_with_recent_mtime_is_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec_dir = Path(tmp) / "specs" / "a"
            spec_dir.mkdir(parents=True)
            (spec_dir / "DRAIN-OWNER.md").write_text("Run-token: x\n", encoding="utf-8")

            self.assertTrue(sr.is_owner_lease_fresh(spec_dir, window_seconds=900))

    def test_owner_file_present_but_stale_mtime_is_not_fresh(self):
        import os
        import time

        with tempfile.TemporaryDirectory() as tmp:
            spec_dir = Path(tmp) / "specs" / "a"
            spec_dir.mkdir(parents=True)
            owner = spec_dir / "DRAIN-OWNER.md"
            owner.write_text("Run-token: x\n", encoding="utf-8")
            old = time.time() - 3600
            os.utime(owner, (old, old))

            self.assertFalse(sr.is_owner_lease_fresh(spec_dir, window_seconds=900))


if __name__ == "__main__":
    unittest.main()
