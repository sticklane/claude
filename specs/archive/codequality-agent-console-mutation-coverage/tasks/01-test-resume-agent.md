# Task 01: Test resume_agent's real failure and success branches

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: done
Depends on: none
Priority: P2
Budget: 14 turns
Spec: ../SPEC.md (Approach step 1; Acceptance criterion 1)
Touch: agent-console/tests/test_resume_agent.py

## Goal

`agent-console.py`'s `resume_agent()` and its route `/api/agent/resume`
gain direct test coverage for both of its real failure branches and its
success branch — currently zero tests reference it. The tests mock only
the process-boundary edge (`subprocess`/spawn), driving the real handler
end to end and asserting the response JSON plus the observable dispatch
effect.

## Touch

New file only: `agent-console/tests/test_resume_agent.py`. Do not edit
`agent-console/agent-console.py` (test-only task; no source change is
required or in scope) or any sibling test file another task in this spec
touches.

## Steps

1. Read `resume_agent()` in `agent-console/agent-console.py` (find it by
   name — the spec's line numbers are snapshots, not a contract) and its
   route registration for `/api/agent/resume`, plus `_claude_run_bg` (the
   spawn boundary it calls).
2. Write the failing tests first (`unittest.TestCase` subclasses, per
   `agent-console`'s `scripts/check.sh` which runs
   `python3 -m unittest discover` — bare pytest-style `def test_...`
   functions are never collected):
   - Unknown sid → asserts the handler returns `(False, "not a known
session")` (or the equivalent JSON/response shape the real handler
     produces for this branch).
   - `_claude_run_bg` raising `OSError`/`RuntimeError` (mock only this
     process-boundary call to raise, e.g. simulating `claude` not on
     PATH) → asserts `(False, str(e))` propagates to the response.
   - Success path (known sid, `_claude_run_bg` succeeds) → asserts the
     response indicates success and the observable dispatch effect (what
     command/cwd was launched) is correct.
   - Do NOT test an empty/whitespace prompt as a failure — `resume_agent`
     defaults it to `"continue"` and succeeds; if you cover this input,
     assert it as a passing case, not a failure case.
3. Confirm each new test fails before any fix (there is no fix needed —
   confirm instead that a test asserting the success branch fails if
   `resume_agent`'s success path is stubbed to return `(False, "x")"`,
   proving the test is a real behavioral check, not a vacuous pass).
4. Run `bash agent-console/scripts/check.sh` and confirm it exits 0 with
   the new tests included.
5. Commit.

## Acceptance

- [x] `grep -rln "api/agent/resume\|resume_agent" agent-console/tests/` is non-empty — returns `agent-console/tests/test_resume_agent.py` (verifier PASS; evidence/01-test-resume-agent.md)
- [x] The new resume_agent success-branch test fails when `resume_agent`'s success branch is manually stubbed to return `(False, "x")` — demonstrated: stub → success test `FAILED (AssertionError: False is not true` on `assertTrue(ok)`), restored → green; source left clean (verifier reproduced independently; evidence/01-test-resume-agent.md)
- [x] Every new test is a `unittest.TestCase` subclass: `grep -c "unittest.TestCase" agent-console/tests/test_resume_agent.py` → 3 (verifier PASS)
- [x] `bash agent-console/scripts/check.sh` → exit 0 — `check: PASS`, 179 tests (verifier PASS; evidence/01-test-resume-agent.md)
- [x] No `assert_called_once()`-style assertion appears without an accompanying behavioral assertion in the same test: matches at lines 84 and 101, each inside a test that also asserts `assertTrue(ok)` and `assertEqual(msg, "resumed")` on the response tuple (verifier PASS; evidence/01-test-resume-agent.md)
