# Task 02: Test set_priority's real file-edit + commit wrapper

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: in-progress
Depends on: none
Priority: P2
Budget: 16 turns
Spec: ../SPEC.md (Approach step 2; Acceptance criterion 2)
Touch: agent-console/tests/test_set_priority.py

## Goal

`agent-console.py`'s `set_priority()` wrapper — which edits a spec file's
`Priority:` header and commits — gains direct test coverage using a real
temp git repo fixture (not a mock), asserting the file actually changed
and a commit actually exists. Today only the pure `apply_priority`
transform is tested, not this wrapper.

## Touch

New file only: `agent-console/tests/test_set_priority.py`. Do not edit
`agent-console/agent-console.py` or any sibling test file another task in
this spec touches.

## Steps

1. Read `set_priority()` in `agent-console/agent-console.py` (find it by
   name) and its route registration for `/api/priority`, plus
   `apply_priority` (the pure transform it wraps) and however the
   existing tests already exercise `apply_priority` / registry rejection
   (read the existing coverage first so this task adds direct wrapper
   coverage, not a duplicate of what's already tested).
2. Write the failing tests first (`unittest.TestCase` subclasses): set up
   a temp git repo fixture (real `git`, local and fast — no mocking git
   itself) containing a spec file with a `Priority:` header, call
   `set_priority()` (or drive it through the real handler) with a new
   priority value, and assert:
   - the file's `Priority:` header actually changed to the new value
     (read the file back, not a mock-called check).
   - a git commit actually exists recording the change (via `git log` or
     equivalent, not `assert_called_once()` on a git-invocation mock).
3. Run `bash agent-console/scripts/check.sh` and confirm it exits 0 with
   the new tests included.
4. Commit.

## Acceptance

- [ ] `grep -rln "set_priority" agent-console/tests/` is non-empty
- [ ] The new test(s) drive `set_priority` (or its route) directly — not only `apply_priority` or registry-rejection paths (state in your final message which existing tests cover `apply_priority`/rejection, confirming this task adds NEW wrapper-level coverage rather than duplicating them)
- [ ] Every new test is a `unittest.TestCase` subclass: `grep -c "unittest.TestCase" agent-console/tests/test_set_priority.py` → at least 1
- [ ] `bash agent-console/scripts/check.sh` → exit 0
- [ ] The new test(s) assert observable state (file content post-edit, `git log` showing a commit) — no bare `assert_called_once()`-style assertion without an accompanying behavioral check
