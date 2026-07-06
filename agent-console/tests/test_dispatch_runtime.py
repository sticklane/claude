"""Tests for the generic dispatch runtime: claude-binary resolution, detached
`start_dispatch`, per-cwd lock, on-disk record store + liveness reload, and the
`GET /dispatches` + `GET /dispatch/<id>/log` pages.

Every test that actually spawns a dispatch uses a STUB claude binary (a tiny
shell script written to a tempdir that records its argv + cwd and sleeps) —
never the real `claude` CLI. The record/log dir is redirected with
`AGENT_CONSOLE_DISPATCH_DIR` so nothing touches the real logs.

Import-by-path mirrors test_actions_registry.py (agent-console.py has a hyphen).
"""

import importlib.util
import json
import os
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


def _headers(mapping):
    msg = Message()
    for k, v in mapping.items():
        msg[k] = v
    return msg


def _get(path, host="127.0.0.1:8899"):
    h = ac.Handler.__new__(ac.Handler)
    h.path = path
    h.headers = _headers({"Host": host})
    captured = {}

    def _send(b, ctype="text/html; charset=utf-8", code=200):
        captured.update(body=b, ctype=ctype, code=code)

    h._send = _send
    return h, captured


def _write_stub(dirpath, record_path, sleep=2):
    """A fake `claude` that dumps `$PWD` then its argv (NUL-separated) to
    `record_path`, then sleeps so the dispatch stays 'running' for the lock
    test. Returns the executable path."""
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


class _DispatchDirTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._prev_env = {
            k: os.environ.get(k)
            for k in ("AGENT_CONSOLE_DISPATCH_DIR", "AGENT_CONSOLE_CLAUDE_BIN")
        }
        os.environ["AGENT_CONSOLE_DISPATCH_DIR"] = self.tmp
        os.environ.pop("AGENT_CONSOLE_CLAUDE_BIN", None)
        self._spawned = []

    def tearDown(self):
        for pgid in self._spawned:
            try:
                os.killpg(pgid, signal.SIGKILL)
            except OSError:
                pass
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
        p = Path(self.tmp) / f"{did}.json"
        return json.loads(p.read_text()) if p.exists() else None

    def _wait_for(self, path, timeout=3.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if os.path.exists(path):
                return True
            time.sleep(0.02)
        return False


class TestResolveClaudeBin(_DispatchDirTest):
    def test_prefers_env_override(self):
        os.environ["AGENT_CONSOLE_CLAUDE_BIN"] = "/opt/stub/claude"
        self.assertEqual(ac._resolve_claude_bin(), "/opt/stub/claude")

    def test_falls_back_to_which(self):
        with patch.object(ac.shutil, "which", return_value="/usr/local/bin/claude"):
            self.assertEqual(ac._resolve_claude_bin(), "/usr/local/bin/claude")

    def test_falls_back_to_local_bin_when_not_on_path(self):
        with patch.object(ac.shutil, "which", return_value=None):
            self.assertEqual(
                ac._resolve_claude_bin(),
                str(ac.HOME / ".local" / "bin" / "claude"),
            )

    def test_resolved_at_call_time_not_import_time(self):
        os.environ["AGENT_CONSOLE_CLAUDE_BIN"] = "/first/claude"
        self.assertEqual(ac._resolve_claude_bin(), "/first/claude")
        os.environ["AGENT_CONSOLE_CLAUDE_BIN"] = "/second/claude"
        self.assertEqual(ac._resolve_claude_bin(), "/second/claude")


class TestStartDispatch(_DispatchDirTest):
    def test_writes_log_and_record_and_runs_stub_detached(self):
        cwd = tempfile.mkdtemp()
        rec_file = os.path.join(self.tmp, "argv.txt")
        os.environ["AGENT_CONSOLE_CLAUDE_BIN"] = _write_stub(self.tmp, rec_file)

        result = self._track(ac.start_dispatch("drain", cwd, "do the thing"))
        self.assertEqual(result["code"], 200)
        did = result["body"]["id"]

        log = Path(self.tmp) / f"{did}.log"
        rec_path = Path(self.tmp) / f"{did}.json"
        self.assertTrue(log.exists())
        self.assertTrue(rec_path.exists())

        rec = json.loads(rec_path.read_text())
        self.assertEqual(rec["kind"], "drain")
        self.assertEqual(rec["cwd"], os.path.realpath(cwd))
        self.assertIsInstance(rec["pgid"], int)
        self.assertTrue(rec["start_time"])
        self.assertEqual(rec["log"], str(log))
        self.assertEqual(rec["state"], "running")

        # Child ran in its own process group (start_new_session), not ours.
        pgid = rec["pgid"]
        self.assertNotEqual(pgid, os.getpgrp())
        self.assertEqual(os.getpgid(pgid), pgid)  # it leads its own group

        # The stub actually executed with the given cwd and a `-p <prompt>` argv.
        self.assertTrue(self._wait_for(rec_file))
        raw = Path(rec_file).read_text()
        first_nl = raw.index("\n")
        self.assertEqual(raw[:first_nl], os.path.realpath(cwd))
        argv = [a for a in raw[first_nl + 1 :].split("\0") if a]
        self.assertIn("-p", argv)
        self.assertIn("do the thing", argv)

    def test_extra_args_reach_the_stub_argv(self):
        cwd = tempfile.mkdtemp()
        rec_file = os.path.join(self.tmp, "argv2.txt")
        os.environ["AGENT_CONSOLE_CLAUDE_BIN"] = _write_stub(self.tmp, rec_file)

        self._track(
            ac.start_dispatch("verify", cwd, "go", extra_args=["--max-turns", "5"])
        )
        self.assertTrue(self._wait_for(rec_file))
        raw = Path(rec_file).read_text()
        argv = [a for a in raw[raw.index("\n") + 1 :].split("\0") if a]
        self.assertIn("--max-turns", argv)
        self.assertIn("5", argv)


class TestPerCwdLock(_DispatchDirTest):
    def test_second_dispatch_same_cwd_refused_other_cwd_allowed(self):
        cwd_a = tempfile.mkdtemp()
        cwd_b = tempfile.mkdtemp()
        os.environ["AGENT_CONSOLE_CLAUDE_BIN"] = _write_stub(
            self.tmp, os.path.join(self.tmp, "argv.txt")
        )

        first = self._track(ac.start_dispatch("drain", cwd_a, "one"))
        self.assertEqual(first["code"], 200)

        blocked = ac.start_dispatch("drain", cwd_a, "two")
        self.assertEqual(blocked["code"], 409)
        self.assertIn(first["body"]["id"], blocked["body"]["message"])

        other = self._track(ac.start_dispatch("drain", cwd_b, "three"))
        self.assertEqual(other["code"], 200)


class TestRecordReloadLiveness(_DispatchDirTest):
    def _write_record(self, did, pgid, start_time, cwd="/some/cwd"):
        rec = {
            "id": did, "kind": "drain", "cwd": cwd, "pgid": pgid,
            "start_time": start_time, "started_at": time.time(),
            "log": str(Path(self.tmp) / f"{did}.log"), "state": "running",
            "exit_code": None,
        }
        (Path(self.tmp) / f"{did}.json").write_text(json.dumps(rec))
        return rec

    def test_alive_pgid_matching_start_time_reloads_running(self):
        own = os.getpgrp()
        self._write_record("live1", own, ac._proc_start_time(own))
        recs = {r["id"]: r for r in ac._load_records()}
        self.assertTrue(recs["live1"]["running"])

    def test_recycled_pgid_start_time_mismatch_reloads_exited(self):
        own = os.getpgrp()
        self._write_record(
            "recycled1", own, "Wed Jan  1 00:00:00 2020", cwd="/locked/cwd"
        )
        recs = {r["id"]: r for r in ac._load_records()}
        self.assertFalse(recs["recycled1"]["running"])
        # ...and the per-cwd lock does not hold for a stale record.
        self.assertIsNone(ac._running_dispatch_for_cwd("/locked/cwd"))

    def test_dead_pgid_reloads_exited(self):
        self._write_record("dead1", 999999, "Wed Jan  1 00:00:00 2020")
        recs = {r["id"]: r for r in ac._load_records()}
        self.assertFalse(recs["dead1"]["running"])


class TestDispatchRoutes(_DispatchDirTest):
    def _write_record(self, did, kind="drain", cwd="/a/repo", log_lines=None):
        log = Path(self.tmp) / f"{did}.log"
        if log_lines is not None:
            log.write_text("".join(log_lines))
        rec = {
            "id": did, "kind": kind, "cwd": cwd, "pgid": 999999,
            "start_time": "", "started_at": time.time(),
            "log": str(log), "state": "exited", "exit_code": None,
        }
        (Path(self.tmp) / f"{did}.json").write_text(json.dumps(rec))

    def test_dispatches_page_lists_records_with_log_links(self):
        self._write_record("aaa", cwd="/repo/one")
        self._write_record("bbb", cwd="/repo/two")
        h, cap = _get("/dispatches")
        h.do_GET()
        self.assertEqual(cap["code"], 200)
        body = cap["body"].decode("utf-8")
        self.assertIn("/dispatch/aaa/log", body)
        self.assertIn("/dispatch/bbb/log", body)
        self.assertIn("/repo/one", body)

    def test_dispatch_log_serves_tail(self):
        lines = [f"line{i:04d}\n" for i in range(1, 301)]
        self._write_record("tail1", log_lines=lines)
        h, cap = _get("/dispatch/tail1/log")
        h.do_GET()
        self.assertEqual(cap["code"], 200)
        body = cap["body"].decode("utf-8")
        self.assertIn("line0300", body)      # last line present
        self.assertNotIn("line0001", body)   # first line trimmed by the ~200 tail

    def test_dispatch_log_unknown_id_404(self):
        h, cap = _get("/dispatch/nope/log")
        h.do_GET()
        self.assertEqual(cap["code"], 404)

    def test_dispatches_host_checked(self):
        h, cap = _get("/dispatches", host="evil.example:8899")
        h.do_GET()
        self.assertEqual(cap["code"], 400)


if __name__ == "__main__":
    unittest.main()
