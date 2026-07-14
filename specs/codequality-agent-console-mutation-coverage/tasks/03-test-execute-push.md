# Task 03: Test execute_push's three real branches (rc-0, rc-nonzero, timeout)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: done
Depends on: none
Priority: P2
Budget: 18 turns
Spec: ../SPEC.md (Approach step 3; Acceptance criterion 3)
Touch: agent-console/tests/test_execute_push.py

## Goal

`agent-console.py`'s `execute_push()` — dispatched via the `"push"`
action-kind table — gains direct test coverage of all three of its real
branches (no dirty-check or ahead/behind logic exists, so these three are
the complete surface): `returncode==0` success, `returncode!=0` failure,
and `subprocess.TimeoutExpired`. Today it is exercised only via
403-rejection (the handler returns before execution) or with
`subprocess.run` fully mocked — never on a real success path.

## Touch

New file only: `agent-console/tests/test_execute_push.py`. Do not edit
`agent-console/agent-console.py` or any sibling test file another task in
this spec touches.

## Steps

1. Read `execute_push()` in `agent-console/agent-console.py` (find it by
   name) and the `"push"` action-kind dispatch table entry that reaches
   it, plus `_invalidate_board()` and `_board_cache["ts"]` (what the rc-0
   branch is supposed to invalidate).
2. Write the failing tests first (`unittest.TestCase` subclasses), driving
   `execute_push(action)` directly with `action["argv"]` pointed at a real
   `git push` against a bare "remote" fixture (a temp bare git repo — real
   git, no mocking of the push mechanics themselves):
   - **rc 0** (push succeeds): assert the response has `ok:true`,
     `exit:0`, AND that `_board_cache["ts"]` was actually invalidated —
     read `_board_cache["ts"]` before the call, call, read it again after,
     and assert it changed (stale-then-fresh read), not a
     mock-called-once check on `_invalidate_board`.
   - **rc non-zero** (push to an unreachable or rejecting remote): assert
     `ok:false`, `exit:<code>`, and the response message contains the
     exit code.
   - **`subprocess.TimeoutExpired`** (mock ONLY `subprocess.run` to raise
     this, since a real timeout isn't practical to trigger deterministically):
     assert `exit:None` and the response message states the timeout.
3. Run `bash agent-console/scripts/check.sh` and confirm it exits 0 with
   the new tests included.
4. Commit.

## Acceptance

- [x] `grep -rln "execute_push" agent-console/tests/` is non-empty — returns `agent-console/tests/test_execute_push.py` (evidence/03-test-execute-push.md)
- [x] The new tests cover all three branches directly (rc-0, rc-nonzero, timeout) — not only registry rejection with `subprocess.run` fully mocked (state in your final message which test method covers which branch) — `test_rc0_push_succeeds_and_invalidates_board_cache` (rc-0, real bare-remote push), `test_rc_nonzero_push_reports_exit_code_in_message` (rc-nonzero, real push to repointed missing remote), `test_timeout_reports_none_exit_and_timeout_message` (timeout, only `subprocess.run` mocked) (evidence/03-test-execute-push.md)
- [x] The rc-0 test asserts `_board_cache["ts"]` actually changed via a stale-then-fresh read — not a `_invalidate_board` mock-called-once check — seeds `ts=1234.5`, reads before/after, asserts `assertNotEqual` + `assertEqual(after, 0.0)` (evidence/03-test-execute-push.md)
- [x] Every new test is a `unittest.TestCase` subclass: `grep -c "unittest.TestCase" agent-console/tests/test_execute_push.py` → at least 1 — returns `3` (evidence/03-test-execute-push.md)
- [x] `bash agent-console/scripts/check.sh` → exit 0 — "Ran 185 tests ... OK", `check: PASS` (evidence/03-test-execute-push.md)
- [x] New tests assert observable behavior (response payloads, cache state) — no bare `assert_called_once()`-style assertion without an accompanying behavioral check — no `assert_called`/`Mock`/`MagicMock` in file; all assertions hit response payload or cache state (evidence/03-test-execute-push.md)
