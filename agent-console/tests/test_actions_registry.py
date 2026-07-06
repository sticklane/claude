"""Tests for the server-side action registry, POST /action/<id>, and the
`push` action kind.

Security is the point of this surface (spec R9): the browser sends only an
opaque action id + the CSRF header + a confirm flag — never a command, path,
or argv. These tests pin that: an unknown id executes nothing, a missing/wrong
token is 403, a foreign Host is rejected before routing, and the argv that
reaches subprocess is byte-identical to the registry's regardless of what junk
the POST body/query carry.

No live socket: the Handler is exercised by constructing a bare instance with a
captured _send() and a BytesIO rfile, mirroring test_drilldown_registry.py.
Import-by-path mirrors test_parsers.py (agent-console.py has a hyphen).
"""

import importlib.util
import io
import json
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch

_spec = importlib.util.spec_from_file_location(
    "ac", str(Path(__file__).resolve().parent.parent / "agent-console.py")
)
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)

_SRC = Path(__file__).resolve().parent.parent / "agent-console.py"


def _headers(mapping):
    msg = Message()
    for k, v in mapping.items():
        msg[k] = v
    return msg


def _board(ahead, path="/repo/alpha", name="alpha"):
    """An _adapt_board()-shaped dict with one repo (only the fields the action
    registry reads)."""
    return {
        "repos": [
            {"id": "x", "name": name, "path": path, "git": {"ahead": ahead}}
        ]
    }


def _post(path, headers, body=b"{}"):
    """A Handler wired to capture _send() and read `body` from rfile."""
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


def _get(path, host):
    h = ac.Handler.__new__(ac.Handler)
    h.path = path
    h.headers = _headers({"Host": host})
    captured = {}

    def _send(b, ctype="text/html; charset=utf-8", code=200):
        captured.update(body=b, ctype=ctype, code=code)

    h._send = _send
    return h, captured


def _good_headers():
    return {"Host": "127.0.0.1:8899", "X-CSRF": ac.CSRF_TOKEN}


class TestBuildActionRegistry(unittest.TestCase):
    def test_push_action_generated_for_ahead_repo(self):
        reg = ac.build_action_registry(_board(2, path="/repo/alpha", name="alpha"))
        pushes = [a for a in reg.values() if a["kind"] == "push"]
        self.assertEqual(len(pushes), 1)
        act = pushes[0]
        self.assertEqual(act["kind"], "push")
        self.assertEqual(act["repo"], "/repo/alpha")
        self.assertEqual(act["argv"], ["git", "-C", "/repo/alpha", "push"])
        self.assertIn("alpha", act["label"])
        self.assertEqual(reg[act["id"]], act)  # keyed by its own id

    def test_clean_repo_yields_no_push_action(self):
        reg = ac.build_action_registry(_board(0))
        self.assertEqual([a for a in reg.values() if a["kind"] == "push"], [])

    def test_action_ids_stable_across_two_builds(self):
        b = _board(3)
        first = ac.build_action_registry(b)
        second = ac.build_action_registry(b)
        self.assertEqual(sorted(first), sorted(second))
        self.assertTrue(first)


class TestPostActionSecurity(unittest.TestCase):
    def _registry_with_one_push(self):
        reg = ac.build_action_registry(_board(1, path="/repo/alpha"))
        (aid,) = list(reg)
        return reg, aid

    def test_post_action_without_token_is_403(self):
        reg, aid = self._registry_with_one_push()
        with patch.object(ac, "get_actions", return_value=reg), patch.object(
            ac.subprocess, "run"
        ) as run:
            h, cap = _post("/action/" + aid, {"Host": "127.0.0.1:8899"})
            h.do_POST()
        self.assertEqual(cap["code"], 403)
        run.assert_not_called()

    def test_post_action_wrong_token_is_403(self):
        reg, aid = self._registry_with_one_push()
        with patch.object(ac, "get_actions", return_value=reg), patch.object(
            ac.subprocess, "run"
        ) as run:
            h, cap = _post(
                "/action/" + aid, {"Host": "127.0.0.1:8899", "X-CSRF": "nope"}
            )
            h.do_POST()
        self.assertEqual(cap["code"], 403)
        run.assert_not_called()

    def test_post_unknown_id_is_409_and_nothing_executed(self):
        reg, _ = self._registry_with_one_push()
        with patch.object(ac, "get_actions", return_value=reg), patch.object(
            ac.subprocess, "run"
        ) as run:
            h, cap = _post("/action/deadbeef", _good_headers())
            h.do_POST()
        self.assertEqual(cap["code"], 409)
        payload = json.loads(cap["body"])
        self.assertFalse(payload["ok"])
        self.assertIn("rescan", payload["message"].lower())
        run.assert_not_called()

    def test_bad_host_rejected_on_post_action(self):
        reg, aid = self._registry_with_one_push()
        with patch.object(ac, "get_actions", return_value=reg), patch.object(
            ac.subprocess, "run"
        ) as run:
            h, cap = _post(
                "/action/" + aid,
                {"Host": "evil.example:8899", "X-CSRF": ac.CSRF_TOKEN},
            )
            h.do_POST()
        self.assertIn(cap["code"], (400, 403))
        run.assert_not_called()

    def test_bad_host_rejected_on_get_workboard(self):
        h, cap = _get("/workboard", host="evil.example:8899")
        h.do_GET()
        self.assertIn(cap["code"], (400, 403))


class TestPushExecution(unittest.TestCase):
    def test_post_push_runs_registry_argv_ignoring_junk_fields(self):
        reg = ac.build_action_registry(_board(1, path="/repo/alpha"))
        (aid,) = list(reg)
        expected_argv = list(reg[aid]["argv"])

        completed = type(
            "R", (), {"returncode": 0, "stdout": "Everything up-to-date\n", "stderr": ""}
        )()
        with patch.object(ac, "get_actions", return_value=reg), patch.object(
            ac.subprocess, "run", return_value=completed
        ) as run:
            junk = json.dumps(
                {"argv": ["rm", "-rf", "/"], "path": "/etc/passwd", "extra": 1}
            ).encode("utf-8")
            h, cap = _post("/action/" + aid + "?cmd=whoami", _good_headers(), junk)
            h.do_POST()

        self.assertEqual(cap["code"], 200)
        run.assert_called_once()
        sent_argv = run.call_args[0][0]
        self.assertEqual(sent_argv, expected_argv)  # byte-identical to registry
        self.assertNotIn("shell", run.call_args.kwargs)  # never shell=True
        payload = json.loads(cap["body"])
        self.assertIn("up-to-date", payload["output"])
        self.assertEqual(payload["exit"], 0)

    def test_push_nonzero_exit_reported_not_retried(self):
        reg = ac.build_action_registry(_board(1, path="/repo/alpha"))
        (aid,) = list(reg)
        failed = type(
            "R", (), {"returncode": 1, "stdout": "", "stderr": "rejected\n"}
        )()
        with patch.object(ac, "get_actions", return_value=reg), patch.object(
            ac.subprocess, "run", return_value=failed
        ) as run:
            h, cap = _post("/action/" + aid, _good_headers())
            h.do_POST()
        self.assertEqual(cap["code"], 200)
        self.assertEqual(run.call_count, 1)  # never retried
        payload = json.loads(cap["body"])
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["exit"], 1)
        self.assertIn("rejected", payload["output"])


class TestNoShellExec(unittest.TestCase):
    def test_source_has_no_shell_true(self):
        src = _SRC.read_text(encoding="utf-8")
        self.assertNotIn("shell=True", src)


if __name__ == "__main__":
    unittest.main()
