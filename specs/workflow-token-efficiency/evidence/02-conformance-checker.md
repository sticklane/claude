# Verification: Task 02 — bin/check-token-discipline + fixture tests (R6)

Verdict: **PASS**

Verified against acceptance criteria in
`specs/workflow-token-efficiency/tasks/02-conformance-checker.md` and SPEC R6.
Base commit for append-only task-file diff: `e995e361f7df561e95799ad0cd224be2022b211e`.

## Criterion 1 — fixture tests exit 0, cover the required cases, assert real behavior
✓ Command: `bash tests/test_check_token_discipline.sh`
Output tail:
```
pass: 23 fail: 0
exit=0
```
- 23 assertions, 0 failures.
- Tests assert per-check markers (`assert_marker` greps for literal `[loop]`/
  `[dispatch]`/`[budget]` present/absent), not "runs without error". Exit-code
  and file-naming assertions present too.
- Coverage confirmed by reading fixtures:
  - drain retry paragraph ("relaunch once") → loop marker ABSENT (line 72).
  - drain max-generations ("max-generations cap of 10") → loop ABSENT (line 89).
  - four must-NOT-flag lines: tournament-cleanup (loop absent), "no relaunch"
    (loop absent), "relaunch clean" (loop absent), "3× the tokens" (budget
    marker PRESENT i.e. does not satisfy budget) — lines 102/111/120/132.
  - two wrapped dispatches (drain launch…agent; design launching…agent) →
    dispatch marker PRESENT i.e. SEEN — lines 148/159.
  - negative controls fire (bare retry→loop, un-tiered dispatch→dispatch,
    no-budget→budget) and clean file exits 0.

## Criterion 2 — checker on current tree exits 1 with per-file, per-check report
✓ Command: `bin/check-token-discipline`
- Exit 1.
- 25 report lines naming all 9 in-scope files. Marker histogram:
  `[budget] 7, [dispatch] 14, [loop] 3, [missing] 1`.
- `.claude/workflows/deep-research.js` reported `[missing] file not found`
  and is genuinely absent/untracked in this worktree (git ls-files empty;
  the file is created by task 04). Reporting missing in-scope files + exit 1
  is correct per the checker's design comment.

## Criterion 3 — bash -n passes and file is executable
✓ `bash -n bin/check-token-discipline` → exit 0.
✓ `test -x bin/check-token-discipline` → executable YES.

## Scope check — PASS (no violations)
`git status --porcelain`:
```
 M specs/workflow-token-efficiency/tasks/02-conformance-checker.md
?? bin/check-token-discipline
```
- Task-file diff since base: only `Status: pending→in-progress` and an added
  `<!-- PLAN -->` comment (append-only; acceptance ticks still `[ ]`, not
  falsely checked).
- `tests/test_check_token_discipline.sh` committed at `c2064de` ("test:
  fixture contract … RED") — TDD test-first order confirmed.
- NO edits to any SKILL.md, `.claude/rules/`, `.claude/workflows/`, or
  `plugin.json`. Exactly the two new files + task-file bookkeeping.
- No overfitting: checker uses general regex vocabulary; no fixture-literal
  strings hardcoded (grep for tournament/three_x/drain_retry → none).

## Independent semantics probe vs SPEC R6 (edge cases via CHECK_TD_FILES)
- `verdict + evidence` literal → satisfies budget (exit 0). ✓
- `relaunch-with-evidence` hyphenated → not a loop trigger (exit 0). ✓
- `Task( … )` literal, no tier → dispatch flagged (exit 1). ✓
- `dispatchable` adjectival → not a dispatch (exit 0). ✓
- `cycle` repeat trigger, unbounded → loop flagged (exit 1, e5b/e5d). ✓

### Finding (non-blocking semantic imprecision)
The bounded-loop check treats ANY digit 1–4 anywhere in the paragraph (or an
adjacent paragraph) as a stated loop bound. A paragraph with an unbounded
`cycle`/`retry` trigger escapes the loop check if it merely contains a `1`–`4`
in unrelated text, e.g. a budget figure "no more than 2k tokens":
```
Repeatedly cycle the reviewer over the draft.
Output budget: no more than 2k tokens.   # the '2' spuriously counts as a bound
```
→ exit 0 (not flagged). SPEC R6 defines the bound as "a numeral 1–4 or a
spelled-out cap" meaning a repeat count, so this is a gap between prose intent
and implementation (over-broad LBOUND `(^|[^0-9])[1-4]([^0-9]|$)`). It is a
FALSE-NEGATIVE risk for the task-03 retrofit if an unbounded loop paragraph
happens to carry a 1–4 digit. NOT an acceptance failure: SPEC states "the
tests are the contract … the spec does not freeze regex syntax," all required
fixtures pass, and none of the criteria exercise this path. Recommend noting
as a follow-up refinement, not blocking this task.

All acceptance criteria exercised and met.
