# Verification: 01-test-resume-agent

Verdict: PASS

Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-a63419d6a86ace218
Branch: task/01-test-resume-agent
Base commit compared: c2391a915c8c0c0525c1d7e066acbc8c91af6752

## Scope check (Touch list)

Command: `git diff c2391a915c8c0c0525c1d7e066acbc8c91af6752 --stat`
Output:

```
 agent-console/tests/test_resume_agent.py | 108 +++++++++++++++++++++++++++++++
 1 file changed, 108 insertions(+)
```

Only the Touch-listed file changed. `agent-console/agent-console.py` is unchanged (matches task's "Do not edit" constraint). No scope creep.

## Criterion 1 — grep is non-empty

Command: `grep -rln "api/agent/resume\|resume_agent" agent-console/tests/`
Output: `agent-console/tests/test_resume_agent.py`
Result: PASS (non-empty).

## Criterion 2 — success-branch test is a real behavioral check

Read `agent-console/tests/test_resume_agent.py`. The success class
`TestResumeAgentSuccess` has two tests, both asserting `self.assertTrue(ok)`
and `self.assertEqual(msg, "resumed")` on the `(ok, msg)` tuple returned by
`resume_agent`, in addition to the dispatch-effect assertion.

Live mutation demonstration (red-first, then restored to green):

1. Copied `agent-console/agent-console.py` aside to a scratchpad path.
2. Patched the source line `return True, "resumed"` (end of `resume_agent`,
   originally at line 3152) to `return False, "x"` via a Python script that
   asserted exactly one match before replacing (no accidental multi-hit).
3. Ran: `cd agent-console && python3 -m unittest tests.test_resume_agent.TestResumeAgentSuccess -v`
   Result: **FAILED (failures=2)** — both success tests failed with
   `AssertionError: False is not true` at `self.assertTrue(ok)`.
4. Restored `agent-console/agent-console.py` from the scratchpad copy (not
   via `git checkout`, per verifier instructions — copied back byte for
   byte).
5. Confirmed restore: `git status --porcelain agent-console/agent-console.py`
   → empty output (clean); `git diff --stat agent-console/agent-console.py`
   → empty output (no diff vs HEAD).
6. Re-ran the same test command post-restore:
   `Ran 2 tests in 0.000s / OK` — both tests green again.

Result: PASS — the success test is a real behavioral check; it fails when
the success branch is stubbed to return `(False, "x")` and passes again once
restored.

## Criterion 3 — unittest.TestCase subclass count

Command: `grep -c "unittest.TestCase" agent-console/tests/test_resume_agent.py`
Output: `3`
Result: PASS (>= 1). (Three TestCase classes: TestResumeAgentUnknownSid,
TestResumeAgentSpawnFailure, TestResumeAgentSuccess — four test methods
total across them, all `unittest.TestCase` style, collectible by
`python3 -m unittest discover`.)

## Criterion 4 — scripts/check.sh exits 0

Command: `bash agent-console/scripts/check.sh` (run from `agent-console/`
directory)
Output tail:

```
py_compile: ok
render: ok (69 skills, adapter seam ok)
----------------------------------------------------------------------
Ran 179 tests in 7.364s

OK
check: PASS
```

Exit code: 0
Result: PASS.

## Criterion 5 — every assert_called_once has an accompanying behavioral assertion

Command: `grep -n "assert_called_once" agent-console/tests/test_resume_agent.py`
Output:

```
84:        run_bg.assert_called_once_with(
101:        run_bg.assert_called_once_with(
```

- Line 84 is inside `test_success_returns_resumed_and_dispatches_correct_command`
  (method body lines 71-87). Same method also asserts `self.assertTrue(ok)`
  (line 80) and `self.assertEqual(msg, "resumed")` (line 81) on the response
  tuple before the call-count assertion.
- Line 101 is inside `test_empty_prompt_defaults_to_continue_and_succeeds`
  (method body lines 89-104). Same method also asserts `self.assertTrue(ok)`
  (line 99) and `self.assertEqual(msg, "resumed")` (line 100) on the response
  tuple before the call-count assertion.

Also noted: `TestResumeAgentUnknownSid` uses `run_bg.assert_not_called()`
(line 39, not `assert_called_once`, out of this criterion's grep scope) but
it too follows behavioral assertions `assertFalse(ok)` / `assertEqual(msg, ...)`.

Result: PASS — every `assert_called_once` match is accompanied by a
behavioral (response-tuple) assertion in the same test method.

## Additional coverage inspection

The three branches required by the task Steps are all present and each
mocks only the process-boundary calls (`_claude_json`, `_claude_run_bg`):

- Unknown sid → `(False, "not a known session")`, `run_bg.assert_not_called()`.
- `_claude_run_bg` raising `RuntimeError` and `OSError` → `(False, str(e))`
  propagates for each exception type.
- Success path → `(True, "resumed")` plus exact dispatch argv/cwd asserted.
- Empty prompt → covered as a passing case (defaults to "continue"), not
  as a failure, per the task's explicit instruction.

## Gate / working-tree final state

`git status --porcelain` (full worktree, post-restore): empty — no
uncommitted changes, no stray files from this verification.
