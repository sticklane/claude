"""Tests for the `unblock` and `recheck` action kinds (unblock-next-steps task
04). BOTH are agent dispatches through the same dispatch runtime the other
`dispatch-*` kinds use — there is no raw-exec path for file-derived `Unblock:`
text.

The registry generates them for waiting-spec headers (`spec['unblock']`) and
blocked task files (`spec['blocked_tasks']`) in git-repo roots only; `ask:`
items get no dispatch affordance. Execution goes through `start_dispatch` with
a STUB claude binary — the untrusted-text property is asserted against the real
`subprocess.Popen` argv (a spy), proving hostile `Unblock:` text lands in
exactly one place: the single `-p` prompt slot, never a shell.

Import-by-path mirrors test_dispatch_kinds.py (agent-console.py has a hyphen).
"""

import importlib.util
import io
import json
import os
import signal
import stat
import tempfile
import time
import unittest
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
# is exercised: a dir with a `.git` child is a git-repo root, one without mimics
# the non-git `~/specs` home.
# --------------------------------------------------------------------------- #
def _git_root():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, ".git"))
    return d


def _non_git_dir():
    return tempfile.mkdtemp()


def _spec_entry(slug, path, done=0, total=0, status=None, unblock=None, blocked_tasks=()):
    return {
        "id": "",
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
        "id": "",
        "name": name,
        "path": path,
        "git": {"branch": "main", "dirty": 0, "ahead": 0, "behind": 0},
        "specs": list(specs),
        "handoffs": [],
        "tasks": None,
        "sessions": [],
    }


def _board(repos):
    return {"repos": list(repos), "inbox": []}


def _of_kind(reg, kind):
    return [a for a in reg.values() if a["kind"] == kind]


def _waiting_spec_board(repo, unblock):
    sp = os.path.join(repo, "specs", "w", "SPEC.md")
    return _board(
        [_repo_entry(repo, "alpha", specs=[_spec_entry("w", sp, status="waiting", unblock=unblock)])]
    )


def _blocked_task_board(repo, unblock, title="Foo"):
    tf = os.path.join(repo, "specs", "x", "tasks", "01-foo.md")
    sp = os.path.join(repo, "specs", "x", "SPEC.md")
    board = _board(
        [
            _repo_entry(
                repo,
                "alpha",
                specs=[_spec_entry("x", sp, blocked_tasks=[_blocked_task(tf, title, unblock)])],
            )
        ]
    )
    return board, tf


class TestGitRootGate(unittest.TestCase):
    def test_waiting_spec_in_git_root_gets_both_unblock_and_recheck(self):
        repo = _git_root()
        reg = ac.build_action_registry(
            _waiting_spec_board(repo, {"type": "agent", "step": "check the deploy"})
        )
        self.assertEqual(len(_of_kind(reg, "unblock")), 1)
        self.assertEqual(len(_of_kind(reg, "recheck")), 1)
        self.assertEqual(_of_kind(reg, "unblock")[0]["cwd"], repo)
        self.assertEqual(_of_kind(reg, "recheck")[0]["cwd"], repo)

    def test_waiting_spec_under_non_git_home_gets_neither(self):
        # Mimics ~/specs: no .git child -> view-only, no dispatch affordance.
        home = _non_git_dir()
        reg = ac.build_action_registry(
            _waiting_spec_board(home, {"type": "agent", "step": "check the deploy"})
        )
        self.assertEqual(_of_kind(reg, "unblock"), [])
        self.assertEqual(_of_kind(reg, "recheck"), [])

    def test_blocked_task_in_git_root_gets_both(self):
        repo = _git_root()
        board, _tf = _blocked_task_board(repo, {"type": "run", "step": "make deploy"})
        reg = ac.build_action_registry(board)
        self.assertEqual(len(_of_kind(reg, "unblock")), 1)
        self.assertEqual(len(_of_kind(reg, "recheck")), 1)


class TestAskExcluded(unittest.TestCase):
    def test_ask_typed_waiting_spec_yields_no_actions(self):
        repo = _git_root()
        reg = ac.build_action_registry(
            _waiting_spec_board(repo, {"type": "ask", "step": "which creds path?"})
        )
        self.assertEqual(_of_kind(reg, "unblock"), [])
        self.assertEqual(_of_kind(reg, "recheck"), [])

    def test_ask_typed_blocked_task_yields_no_actions(self):
        repo = _git_root()
        board, _tf = _blocked_task_board(repo, {"type": "ask", "step": "pick a base URL"})
        reg = ac.build_action_registry(board)
        self.assertEqual(_of_kind(reg, "unblock"), [])
        self.assertEqual(_of_kind(reg, "recheck"), [])


class TestUnblockPrompt(unittest.TestCase):
    def test_run_unblock_wraps_command_in_evaluate_guard(self):
        repo = _git_root()
        reg = ac.build_action_registry(
            _waiting_spec_board(repo, {"type": "run", "step": "make deploy"})
        )
        (u,) = _of_kind(reg, "unblock")
        low = u["prompt"].lower()
        self.assertIn("make deploy", u["prompt"])
        self.assertIn("evaluate", low)
        self.assertIn("run:", low)

    def test_agent_unblock_dispatches_the_step_verbatim(self):
        repo = _git_root()
        reg = ac.build_action_registry(
            _waiting_spec_board(repo, {"type": "agent", "step": "SENTINEL-AGENT-PROMPT"})
        )
        (u,) = _of_kind(reg, "unblock")
        self.assertEqual(u["prompt"], "SENTINEL-AGENT-PROMPT")


class TestRecheckPrompt(unittest.TestCase):
    def test_recheck_prompt_documents_read_verify_flip_commit(self):
        repo = _git_root()
        board, tf = _blocked_task_board(repo, {"type": "run", "step": "make deploy"})
        reg = ac.build_action_registry(board)
        (rc,) = _of_kind(reg, "recheck")
        p = rc["prompt"]
        self.assertIn(tf, p, "the recheck prompt must name the file to read")
        self.assertIn("make deploy", p, "it must carry the current unblock step")
        low = p.lower()
        self.assertIn("verify", low)
        self.assertIn("pending", low, "cleared task file -> flip Status to pending")
        self.assertIn("--no-verify", p, "commit with --no-verify")
        self.assertIn("today", low, "still-blocked -> update with today's date")


# --------------------------------------------------------------------------- #
# Execution — the untrusted-text property, asserted against the real Popen argv.
# --------------------------------------------------------------------------- #
def _write_stub(dirpath, sleep=2):
    stub = os.path.join(dirpath, "claude-stub.sh")
    Path(stub).write_text(f"#!/bin/sh\nsleep {sleep}\n")
    os.chmod(stub, os.stat(stub).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return stub


class TestUntrustedText(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._prev_env = {
            k: os.environ.get(k)
            for k in ("AGENT_CONSOLE_DISPATCH_DIR", "AGENT_CONSOLE_CLAUDE_BIN")
        }
        os.environ["AGENT_CONSOLE_DISPATCH_DIR"] = self.tmp
        os.environ["AGENT_CONSOLE_CLAUDE_BIN"] = _write_stub(self.tmp)
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
        did = result["body"].get("id")
        if did:
            rec = json.loads((Path(self.tmp) / f"{did}.json").read_text())
            if isinstance(rec.get("pgid"), int):
                self._spawned.append(rec["pgid"])
        return result

    def test_hostile_run_text_reaches_only_the_single_p_prompt_slot(self):
        hostile = "$(rm -rf ~)"
        repo = _git_root()
        board, _tf = _blocked_task_board(repo, {"type": "run", "step": hostile})
        reg = ac.build_action_registry(board)
        (act,) = _of_kind(reg, "unblock")

        popen_calls = []
        real_popen = ac.subprocess.Popen

        def _spy(*args, **kwargs):
            popen_calls.append((args, kwargs))
            return real_popen(*args, **kwargs)

        with patch.object(ac, "get_actions", return_value=reg), patch.object(
            ac.subprocess, "Popen", side_effect=_spy
        ):
            result = self._track(ac.run_action(act["id"]))
        self.assertEqual(result["code"], 200)

        # Exactly ONE subprocess was launched (the full recorded history).
        self.assertEqual(len(popen_calls), 1, "unblock must launch exactly one subprocess")
        (pargs, pkwargs), = popen_calls
        argv = pargs[0] if pargs else pkwargs.get("args")
        self.assertIsInstance(argv, list, "argv must be a list, not a shell string")

        # shell=True is absent -> the text is never handed to a shell.
        self.assertFalse(pkwargs.get("shell"), "shell=True must be absent")

        # The hostile text appears in exactly one argv element...
        occurrences = [i for i, a in enumerate(argv) if hostile in str(a)]
        self.assertEqual(len(occurrences), 1, "hostile text must appear in exactly one argv slot")
        # ...and that element is the value immediately after the single `-p`.
        idx = occurrences[0]
        self.assertEqual(argv.count("-p"), 1, "exactly one -p flag")
        self.assertEqual(argv[idx - 1], "-p", "the hostile text is the -p prompt value")
        self.assertEqual(argv.index("-p"), idx - 1)


if __name__ == "__main__":
    unittest.main()
