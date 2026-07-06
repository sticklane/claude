"""Tests for the three dispatch action kinds — `dispatch-drain`,
`dispatch-verify`, `dispatch-resume-handoff` — generated in the action
registry (task 01 seam) and executed through the dispatch runtime (task 02
seam: `start_dispatch`, per-cwd lock, records).

Every test that actually spawns a dispatch uses a STUB claude binary (a tiny
shell script that records its argv + cwd and sleeps) — never the real `claude`
CLI. The record/log dir is redirected with `AGENT_CONSOLE_DISPATCH_DIR`.

Import-by-path mirrors test_dispatch_runtime.py (agent-console.py has a hyphen).
"""

import importlib.util
import io
import json
import os
import shlex
import signal
import stat
import tempfile
import time
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch

_spec = importlib.util.spec_from_file_location(
    "ac", str(Path(__file__).resolve().parent.parent / "agent-console.py")
)
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)


# --------------------------------------------------------------------------- #
# Fixture board builders — _adapt_board()-shaped dicts with only the fields the
# action registry reads. Real temp dirs back each "repo" so the git-root gate
# (R5b) can be exercised: a dir with a `.git` child is a git-repo root, one
# without mimics the non-git `~/specs` home.
# --------------------------------------------------------------------------- #
def _git_root():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, ".git"))
    return d


def _non_git_dir():
    return tempfile.mkdtemp()


def _spec_entry(slug, path, done, total):
    return {
        "id": "", "slug": slug, "title": slug, "status": None, "priority": "",
        "path": path, "done": done, "total": total, "tasks": [], "mtime": 0,
    }


def _handoff_entry(title, path):
    return {"title": title, "path": path, "mtime": 0, "id": ""}


def _repo_entry(path, name, specs=(), handoffs=(), ahead=0):
    return {
        "id": "", "name": name, "path": path,
        "git": {"branch": "main", "dirty": 0, "ahead": ahead, "behind": 0},
        "specs": list(specs), "handoffs": list(handoffs),
        "tasks": None, "sessions": [],
    }


def _cmd(repo_path, prompt):
    return f"cd {shlex.quote(repo_path)} && claude {shlex.quote(prompt)}"


def _inbox_verify(repo_name, slug, total, repo_path, prompt=None):
    if prompt is None:
        prompt = (
            f"Use the verifier agent to verify specs/{slug} "
            "against its acceptance criteria; if it passes, archive the spec dir"
        )
    return {
        "sev": "warning", "state": "needs-review",
        "item": f"Spec {slug}: all {total} task(s) done",
        "repo": repo_name, "why": "run the verifier", "age": 0,
        "cmd": _cmd(repo_path, prompt),
    }


def _inbox_resume(repo_name, title, path, repo_path, prompt=None):
    if prompt is None:
        prompt = f"Resume the parked handoff in {path}; delete the file once fully resumed"
    return {
        "sev": "serious", "state": "blocked",
        "item": f"Handoff parked: {title}",
        "repo": repo_name, "why": "resume it", "age": 0,
        "cmd": _cmd(repo_path, prompt),
    }


def _board(repos, inbox=()):
    return {"repos": list(repos), "inbox": list(inbox)}


def _of_kind(reg, kind):
    return [a for a in reg.values() if a["kind"] == kind]


class TestDrainGeneration(unittest.TestCase):
    def test_pending_task_spec_in_git_root_yields_drain(self):
        repo = _git_root()
        sp = os.path.join(repo, "specs", "widget", "SPEC.md")
        reg = ac.build_action_registry(
            _board([_repo_entry(repo, "alpha", specs=[_spec_entry("widget", sp, 1, 3)])])
        )
        drains = _of_kind(reg, "dispatch-drain")
        self.assertEqual(len(drains), 1)
        act = drains[0]
        self.assertEqual(act["cwd"], repo)
        self.assertEqual(
            act["prompt"], "Run /drain for specs/widget; work only that spec's tasks"
        )
        self.assertEqual(reg[act["id"]], act)  # keyed by its own id

    def test_all_done_spec_yields_no_drain(self):
        repo = _git_root()
        sp = os.path.join(repo, "specs", "widget", "SPEC.md")
        reg = ac.build_action_registry(
            _board([_repo_entry(repo, "alpha", specs=[_spec_entry("widget", sp, 3, 3)])])
        )
        self.assertEqual(_of_kind(reg, "dispatch-drain"), [])


class TestVerifyGeneration(unittest.TestCase):
    def test_all_done_spec_yields_verify(self):
        repo = _git_root()
        sp = os.path.join(repo, "specs", "widget", "SPEC.md")
        reg = ac.build_action_registry(
            _board(
                [_repo_entry(repo, "alpha", specs=[_spec_entry("widget", sp, 3, 3)])],
                inbox=[_inbox_verify("alpha", "widget", 3, repo)],
            )
        )
        verifies = _of_kind(reg, "dispatch-verify")
        self.assertEqual(len(verifies), 1)
        self.assertEqual(verifies[0]["cwd"], repo)
        # The scanner's verify prompt, reused verbatim from the inbox item.
        self.assertIn("verify specs/widget", verifies[0]["prompt"])
        self.assertIn("acceptance criteria", verifies[0]["prompt"])

    def test_verify_prompt_reused_from_inbox_not_duplicated(self):
        # A distinctive inbox prompt must flow through to the action prompt —
        # proving the text comes from the scanner's item, not a local copy.
        repo = _git_root()
        sp = os.path.join(repo, "specs", "widget", "SPEC.md")
        reg = ac.build_action_registry(
            _board(
                [_repo_entry(repo, "alpha", specs=[_spec_entry("widget", sp, 2, 2)])],
                inbox=[
                    _inbox_verify("alpha", "widget", 2, repo, prompt="SENTINEL-VERIFY-x")
                ],
            )
        )
        (v,) = _of_kind(reg, "dispatch-verify")
        self.assertEqual(v["prompt"], "SENTINEL-VERIFY-x")

    def test_all_done_spec_without_inbox_item_yields_no_verify(self):
        # No scanner prompt to reuse -> no verify action (never fabricated).
        repo = _git_root()
        sp = os.path.join(repo, "specs", "widget", "SPEC.md")
        reg = ac.build_action_registry(
            _board([_repo_entry(repo, "alpha", specs=[_spec_entry("widget", sp, 2, 2)])])
        )
        self.assertEqual(_of_kind(reg, "dispatch-verify"), [])


class TestResumeHandoffGeneration(unittest.TestCase):
    def test_parked_handoff_yields_resume(self):
        repo = _git_root()
        hp = os.path.join(repo, "HANDOFF.md")
        reg = ac.build_action_registry(
            _board(
                [_repo_entry(repo, "alpha", handoffs=[_handoff_entry("Ship it", hp)])],
                inbox=[_inbox_resume("alpha", "Ship it", hp, repo)],
            )
        )
        resumes = _of_kind(reg, "dispatch-resume-handoff")
        self.assertEqual(len(resumes), 1)
        self.assertEqual(resumes[0]["cwd"], repo)
        self.assertIn("Resume the parked handoff", resumes[0]["prompt"])
        self.assertIn(hp, resumes[0]["prompt"])

    def test_resume_prompt_reused_from_inbox(self):
        repo = _git_root()
        hp = os.path.join(repo, "HANDOFF.md")
        reg = ac.build_action_registry(
            _board(
                [_repo_entry(repo, "alpha", handoffs=[_handoff_entry("Ship it", hp)])],
                inbox=[_inbox_resume("alpha", "Ship it", hp, repo, prompt="SENTINEL-RESUME")],
            )
        )
        (r,) = _of_kind(reg, "dispatch-resume-handoff")
        self.assertEqual(r["prompt"], "SENTINEL-RESUME")


class TestGitRootGate(unittest.TestCase):
    def test_non_git_home_spec_yields_no_dispatch_actions(self):
        # R5b: a spec whose home is not a git-repo root (mimics ~/specs) gets
        # NO dispatch actions — there is no repo cwd for a dispatch to run in.
        home = _non_git_dir()
        sp = os.path.join(home, "specs", "widget", "SPEC.md")
        hp = os.path.join(home, "HANDOFF.md")
        reg = ac.build_action_registry(
            _board(
                [_repo_entry(home, "specs", specs=[_spec_entry("widget", sp, 1, 3)],
                             handoffs=[_handoff_entry("h", hp)])],
                inbox=[_inbox_verify("specs", "widget", 3, home),
                       _inbox_resume("specs", "h", hp, home)],
            )
        )
        self.assertEqual([a for a in reg.values() if a["kind"].startswith("dispatch-")], [])

    def test_git_root_spec_yields_dispatch_actions(self):
        repo = _git_root()
        sp = os.path.join(repo, "specs", "widget", "SPEC.md")
        reg = ac.build_action_registry(
            _board([_repo_entry(repo, "alpha", specs=[_spec_entry("widget", sp, 1, 3)])])
        )
        self.assertTrue([a for a in reg.values() if a["kind"].startswith("dispatch-")])


class TestActionIdStability(unittest.TestCase):
    def test_dispatch_ids_stable_across_two_builds(self):
        repo = _git_root()
        sp = os.path.join(repo, "specs", "widget", "SPEC.md")
        board = _board([_repo_entry(repo, "alpha", specs=[_spec_entry("widget", sp, 1, 3)])])
        first = ac.build_action_registry(board)
        second = ac.build_action_registry(board)
        self.assertEqual(sorted(first), sorted(second))
        self.assertTrue(_of_kind(first, "dispatch-drain"))


# --------------------------------------------------------------------------- #
# Execution — POST/run_action -> start_dispatch with a stub binary.
# --------------------------------------------------------------------------- #
def _headers(mapping):
    msg = Message()
    for k, v in mapping.items():
        msg[k] = v
    return msg


def _good_headers():
    return {"Host": "127.0.0.1:8899", "X-CSRF": ac.CSRF_TOKEN}


def _post(path, headers, body=b"{}"):
    h = ac.Handler.__new__(ac.Handler)
    h.path = path
    hdrs = dict(headers)
    hdrs.setdefault("Content-Length", str(len(body)))
    h.headers = _headers(hdrs)
    h.rfile = io.BytesIO(body)
    captured = {}

    def _send(b, ctype="text/html; charset=utf-8", code=200):
        captured.update(body=b, ctype=ctype, code=code)

    h._send = _send
    return h, captured


def _write_stub(dirpath, record_path, sleep=2):
    stub = os.path.join(dirpath, "claude-stub.sh")
    script = (
        "#!/bin/sh\n"
        f'{{ printf %s\\\\n "$PWD"; for a in "$@"; do printf %s\\\\0 "$a"; done; }} '
        f'> "{record_path}"\n'
        f"sleep {sleep}\n"
    )
    Path(stub).write_text(script)
    os.chmod(stub, os.stat(stub).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return stub


class _DispatchExecTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._prev_env = {
            k: os.environ.get(k)
            for k in ("AGENT_CONSOLE_DISPATCH_DIR", "AGENT_CONSOLE_CLAUDE_BIN")
        }
        os.environ["AGENT_CONSOLE_DISPATCH_DIR"] = self.tmp
        self.rec_file = os.path.join(self.tmp, "argv.txt")
        os.environ["AGENT_CONSOLE_CLAUDE_BIN"] = _write_stub(self.tmp, self.rec_file)
        self._spawned = []

    def tearDown(self):
        for pgid in self._spawned:
            try:
                os.killpg(pgid, signal.SIGKILL)
            except OSError:
                pass
        for p in list(ac._dispatch_procs):
            try:
                p.wait(timeout=2)
            except Exception:
                pass
        ac._dispatch_procs.clear()
        for k, v in self._prev_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _track(self, result):
        rec = self._record_for(result["body"].get("id"))
        if rec and isinstance(rec.get("pgid"), int):
            self._spawned.append(rec["pgid"])
        return result

    def _record_for(self, did):
        if not did:
            return None
        p = Path(self.tmp) / f"{did}.json"
        return json.loads(p.read_text()) if p.exists() else None

    def _wait_for(self, path, timeout=3.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if os.path.exists(path):
                return True
            time.sleep(0.02)
        return False

    def _recorded_argv(self):
        self.assertTrue(self._wait_for(self.rec_file))
        raw = Path(self.rec_file).read_text()
        nl = raw.index("\n")
        return raw[:nl], [a for a in raw[nl + 1 :].split("\0") if a]

    def _drain_registry(self):
        repo = _git_root()
        sp = os.path.join(repo, "specs", "widget", "SPEC.md")
        reg = ac.build_action_registry(
            _board([_repo_entry(repo, "alpha", specs=[_spec_entry("widget", sp, 1, 3)])])
        )
        (drain,) = _of_kind(reg, "dispatch-drain")
        return reg, drain["id"], repo


class TestDispatchExecution(_DispatchExecTest):
    def test_drain_dispatch_records_prompt_permission_flags_and_cwd(self):
        reg, aid, repo = self._drain_registry()
        with patch.object(ac, "get_actions", return_value=reg):
            result = self._track(ac.run_action(aid))
        self.assertEqual(result["code"], 200)

        cwd, argv = self._recorded_argv()
        self.assertEqual(cwd, os.path.realpath(repo))  # ran in the repo
        self.assertIn("-p", argv)
        self.assertIn("Run /drain for specs/widget; work only that spec's tasks", argv)
        self.assertIn("--permission-mode", argv)
        self.assertIn("--allowedTools", argv)
        self.assertIn("--max-turns", argv)

    def test_second_dispatch_same_repo_is_409(self):
        reg, aid, repo = self._drain_registry()
        with patch.object(ac, "get_actions", return_value=reg):
            first = self._track(ac.run_action(aid))
            self.assertEqual(first["code"], 200)
            blocked = ac.run_action(aid)
        self.assertEqual(blocked["code"], 409)
        self.assertIn("message", blocked["body"])
        self.assertFalse(blocked["body"]["ok"])

    def test_post_action_dispatch_ignores_client_junk(self):
        # R9: the argv is built wholly from the registry — junk POST body /
        # query fields never reach it.
        reg, aid, repo = self._drain_registry()
        junk = json.dumps(
            {"prompt": "EVIL", "cwd": "/etc", "argv": ["rm", "-rf", "/"]}
        ).encode("utf-8")
        with patch.object(ac, "get_actions", return_value=reg):
            h, cap = _post("/action/" + aid + "?prompt=EVIL", _good_headers(), junk)
            h.do_POST()
        self.assertEqual(cap["code"], 200)
        self._track({"body": json.loads(cap["body"])})  # track pgid for cleanup
        _cwd, argv = self._recorded_argv()
        self.assertIn("Run /drain for specs/widget; work only that spec's tasks", argv)
        self.assertNotIn("EVIL", argv)
        self.assertNotIn("/etc", argv)


if __name__ == "__main__":
    unittest.main()
