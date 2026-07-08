"""Tests for the stop actions (task 04): `stop-dispatch` (terminate a dispatch
this server started) and the hardening of `stop-session` (`stop_agent`).

R7: SIGTERM then SIGKILL after a grace, only if still alive; signal only when
the recorded pgid/pid is alive AND its process start time still matches — a
recycled pid/pgid is never signaled. R8: effectful stop buttons render with the
two-step confirm pattern; the stop endpoints require the token and a confirm
flag.

Every process signalled here is a stub this test spawned itself (a tiny Python
sleeper in its own session) — never a real `claude` session or the live
service. The dispatch record dir and the session-record dir are redirected to a
tempdir so nothing touches the real logs or `~/.claude/sessions`.
"""

import importlib.util
import io
import json
import os
import signal
import subprocess
import sys
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


class _StopTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._prev_env = {
            k: os.environ.get(k)
            for k in ("AGENT_CONSOLE_DISPATCH_DIR", "AGENT_CONSOLE_STOP_GRACE")
        }
        os.environ["AGENT_CONSOLE_DISPATCH_DIR"] = self.tmp
        os.environ["AGENT_CONSOLE_STOP_GRACE"] = "0.3"
        self._prev_pid_dir = ac.PID_DIR
        ac.PID_DIR = Path(self.tmp) / "sessions"
        ac.PID_DIR.mkdir(parents=True, exist_ok=True)
        self._procs = []

    def tearDown(self):
        for t in list(ac._escalation_timers):
            t.join(timeout=3)
        for p in self._procs:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except OSError:
                pass
            try:
                p.wait(timeout=2)
            except Exception:
                pass
        for p in list(ac._dispatch_procs):
            try:
                p.wait(timeout=2)
            except Exception:
                pass
        ac._dispatch_procs.clear()
        ac.PID_DIR = self._prev_pid_dir
        for k, v in self._prev_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    # --- process + record fixtures ---------------------------------------- #
    def _spawn(self, fname="sleeper.py", ignore_term=False):
        """A stub process in its own session (pid == pgid). `ignore_term` makes
        it install SIG_IGN for SIGTERM so only SIGKILL can end it — the
        escalation fixture. `fname` lets a caller put 'claude' in the command
        line for the session-command check."""
        script = Path(self.tmp) / fname
        body = "import signal, time\n"
        if ignore_term:
            body += "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        body += "while True:\n    time.sleep(0.05)\n"
        script.write_text(body)
        proc = subprocess.Popen(
            [sys.executable, str(script)],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._procs.append(proc)
        time.sleep(0.25)  # let it install the signal handler / start
        return proc

    def _write_dispatch(
        self, did, pgid, start_time, kind="drain", cwd="/a/repo", state="running"
    ):
        rec = {
            "id": did,
            "kind": kind,
            "cwd": cwd,
            "pgid": pgid,
            "start_time": start_time,
            "started_at": time.time(),
            "log": str(Path(self.tmp) / f"{did}.log"),
            "state": state,
            "exit_code": None,
        }
        (Path(self.tmp) / f"{did}.json").write_text(json.dumps(rec))
        return rec

    def _write_session(self, pid, proc_start=None):
        if proc_start is None:
            proc_start = ac._proc_start_time(pid)
        (ac.PID_DIR / f"{pid}.json").write_text(
            json.dumps(
                {
                    "pid": pid,
                    "sessionId": f"sess-{pid}",
                    "procStart": proc_start,
                    "cwd": "/tmp",
                    "startedAt": time.time(),
                }
            )
        )

    def _join_timers(self):
        for t in list(ac._escalation_timers):
            t.join(timeout=3)


# ------------------------------------------------------------------------- #
# The SIGTERM -> SIGKILL escalation mechanism itself.
# ------------------------------------------------------------------------- #
class TestSignalWithGrace(_StopTest):
    def test_escalates_to_sigkill_when_sigterm_ignored(self):
        proc = self._spawn("stubborn.py", ignore_term=True)
        pgid = proc.pid
        on_dead = {"ran": False}
        t = ac._signal_with_grace(
            term_fn=lambda: os.killpg(pgid, signal.SIGTERM),
            kill_fn=lambda: os.killpg(pgid, signal.SIGKILL),
            alive_fn=lambda: ac._pgid_alive(pgid),
            grace=0.3,
            on_dead=lambda: on_dead.update(ran=True),
        )
        # SIGTERM is ignored, so it must still be alive right after term.
        self.assertTrue(ac._pgid_alive(pgid))
        t.join(timeout=3)
        proc.wait(timeout=2)
        self.assertIsNotNone(proc.poll())  # SIGKILL ended it
        self.assertTrue(on_dead["ran"])

    def test_does_not_block_the_caller_for_the_grace(self):
        proc = self._spawn("stubborn2.py", ignore_term=True)
        pgid = proc.pid
        start = time.monotonic()
        ac._signal_with_grace(
            term_fn=lambda: os.killpg(pgid, signal.SIGTERM),
            kill_fn=lambda: os.killpg(pgid, signal.SIGKILL),
            alive_fn=lambda: ac._pgid_alive(pgid),
            grace=0.3,
        )
        # Returns immediately — the 0.3s grace runs on the background timer.
        self.assertLess(time.monotonic() - start, 0.2)
        self._join_timers()


# ------------------------------------------------------------------------- #
# stop-dispatch: terminate a dispatch this server started (R7).
# ------------------------------------------------------------------------- #
class TestStopDispatch(_StopTest):
    def test_stops_live_dispatch_and_records_stopped_state(self):
        proc = self._spawn("live_disp.py")
        pgid = proc.pid
        self._write_dispatch("d1", pgid, ac._proc_start_time(pgid))

        ok, msg = ac.stop_dispatch("d1")
        self.assertTrue(ok, msg)
        self._join_timers()
        proc.wait(timeout=2)
        self.assertIsNotNone(proc.poll())  # process group gone

        rec = json.loads((Path(self.tmp) / "d1.json").read_text())
        self.assertEqual(rec["state"], "stopped")  # exit state recorded

    def test_recycled_pgid_is_never_signaled(self):
        # pgid is alive (our own group) but the recorded start time does not
        # match — i.e. the pgid was recycled to another process. It must not be
        # signaled (R7 recycled-pid guard).
        own = os.getpgrp()
        self._write_dispatch("recycled", own, "Wed Jan  1 00:00:00 2020")
        with patch.object(ac.os, "killpg", wraps=os.killpg) as killpg:
            ok, msg = ac.stop_dispatch("recycled")
        self.assertFalse(ok)
        sent = [c.args[1] for c in killpg.call_args_list]
        self.assertNotIn(signal.SIGTERM, sent)
        self.assertNotIn(signal.SIGKILL, sent)

    def test_escalates_to_sigkill_for_stubborn_dispatch(self):
        proc = self._spawn("stubborn_disp.py", ignore_term=True)
        pgid = proc.pid
        self._write_dispatch("d2", pgid, ac._proc_start_time(pgid))

        ok, _ = ac.stop_dispatch("d2")
        self.assertTrue(ok)
        self._join_timers()
        proc.wait(timeout=2)
        self.assertIsNotNone(proc.poll())  # only SIGKILL could have ended it

    def test_unknown_dispatch_id_refused(self):
        ok, _ = ac.stop_dispatch("does-not-exist")
        self.assertFalse(ok)


# ------------------------------------------------------------------------- #
# stop-session hardening: start-time + command verification (R7).
# ------------------------------------------------------------------------- #
class TestStopAgentHardening(_StopTest):
    def test_signals_verified_claude_pid(self):
        proc = self._spawn("claude-session.py")  # 'claude' in the command line
        self._write_session(proc.pid)  # procStart matches the live process
        with patch.object(ac, "_claude_json", return_value=[{"pid": proc.pid}]):
            ok, msg = ac.stop_agent(proc.pid, confirm=True)
        self.assertTrue(ok, msg)
        self._join_timers()
        proc.wait(timeout=2)
        self.assertIsNotNone(proc.poll())

    def test_refuses_start_time_mismatch(self):
        proc = self._spawn("claude-recycled.py")
        self._write_session(proc.pid, proc_start="Wed Jan  1 00:00:00 2020")
        with patch.object(ac, "_claude_json", return_value=[{"pid": proc.pid}]):
            ok, _ = ac.stop_agent(proc.pid, confirm=True)
        self.assertFalse(ok)
        self.assertIsNone(proc.poll())  # still alive — never signaled

    def test_refuses_non_claude_command(self):
        proc = self._spawn("sleeper.py")  # command has no 'claude'
        self._write_session(proc.pid)
        with patch.object(ac, "_claude_json", return_value=[{"pid": proc.pid}]):
            ok, _ = ac.stop_agent(proc.pid, confirm=True)
        self.assertFalse(ok)
        self.assertIsNone(proc.poll())

    def test_requires_confirm_flag(self):
        proc = self._spawn("claude-noconfirm.py")
        self._write_session(proc.pid)
        with patch.object(ac, "_claude_json", return_value=[{"pid": proc.pid}]):
            ok, _ = ac.stop_agent(proc.pid, confirm=False)
        self.assertFalse(ok)
        self.assertIsNone(proc.poll())  # unconfirmed -> never signaled

    def test_unknown_pid_rejected(self):
        ok, _ = ac.stop_agent(999999, confirm=True)
        self.assertFalse(ok)


# ------------------------------------------------------------------------- #
# Registry generation + UI confirm rendering (R8).
# ------------------------------------------------------------------------- #
class TestStopDispatchRegistry(_StopTest):
    def test_running_record_yields_stop_dispatch_action(self):
        own = os.getpgrp()
        self._write_dispatch("run1", own, ac._proc_start_time(own))
        reg = ac.build_action_registry({"repos": []})
        stops = [a for a in reg.values() if a["kind"] == "stop-dispatch"]
        self.assertEqual(len(stops), 1)
        self.assertEqual(stops[0]["dispatch_id"], "run1")

    def test_exited_record_yields_no_stop_action(self):
        self._write_dispatch("dead1", 999999, "Wed Jan  1 00:00:00 2020")
        reg = ac.build_action_registry({"repos": []})
        self.assertEqual([a for a in reg.values() if a["kind"] == "stop-dispatch"], [])


class TestStopUIConfirm(_StopTest):
    def _running_record(self, did="ui1"):
        rec = self._write_dispatch(did, 999999, "x")
        rec["running"] = True
        return rec

    def _exited_record(self, did="ui2"):
        rec = self._write_dispatch(did, 999999, "x")
        rec["running"] = False
        return rec

    def test_running_dispatch_renders_confirm_stop_button(self):
        html = ac.render_dispatches([self._running_record()])
        self.assertIn('data-act="stop-dispatch"', html)
        self.assertIn("data-confirm=", html)

    def test_exited_dispatch_has_no_stop_button(self):
        html = ac.render_dispatches([self._exited_record()])
        self.assertNotIn('data-act="stop-dispatch"', html)


# ------------------------------------------------------------------------- #
# Endpoint: token + confirm-flag required for stop actions (R8/R9).
# ------------------------------------------------------------------------- #
class TestStopEndpointSecurity(_StopTest):
    def _stop_registry(self):
        aid = ac._entity_id("stop-dispatch", "/x/log")
        return {
            aid: {
                "id": aid,
                "kind": "stop-dispatch",
                "label": "stop drain",
                "repo": "/a/repo",
                "dispatch_id": "d9",
            }
        }, aid

    def test_post_stop_without_token_is_403(self):
        reg, aid = self._stop_registry()
        with (
            patch.object(ac, "get_actions", return_value=reg),
            patch.object(ac, "stop_dispatch") as sd,
        ):
            h, cap = _post(
                "/action/" + aid,
                {"Host": "127.0.0.1:8899"},
                json.dumps({"confirm": True}).encode(),
            )
            h.do_POST()
        self.assertEqual(cap["code"], 403)
        sd.assert_not_called()

    def test_post_stop_without_confirm_flag_rejected(self):
        reg, aid = self._stop_registry()
        with (
            patch.object(ac, "get_actions", return_value=reg),
            patch.object(ac, "stop_dispatch") as sd,
        ):
            h, cap = _post("/action/" + aid, _good_headers(), b"{}")
            h.do_POST()
        self.assertNotEqual(cap["code"], 200)
        sd.assert_not_called()

    def test_post_stop_with_token_and_confirm_executes(self):
        reg, aid = self._stop_registry()
        with (
            patch.object(ac, "get_actions", return_value=reg),
            patch.object(ac, "stop_dispatch", return_value=(True, "stopping")) as sd,
        ):
            h, cap = _post(
                "/action/" + aid,
                _good_headers(),
                json.dumps({"confirm": True}).encode(),
            )
            h.do_POST()
        self.assertEqual(cap["code"], 200)
        sd.assert_called_once_with("d9")


if __name__ == "__main__":
    unittest.main()
