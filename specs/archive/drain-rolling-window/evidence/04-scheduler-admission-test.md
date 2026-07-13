# Verification: Task 04 — Model-free scheduler admission test

Verdict: PASS

## Criterion 1 — `bash tests/test_drain_scheduler_window.sh` → exit 0

Command run:
```
bash tests/test_drain_scheduler_window.sh; echo "EXIT:$?"
```
Output tail:
```
PASS: (e) zombie-claimed Touch blocks without starving
PASS: (f) admission held during a tournament
PASS: (g) merge-time Touch violation rejected
pass: 21 fail: 0
EXIT:0
```
Result: ✓ PASS (exit code 0, all 7 case lines PASS, 21 individual assertions passed, 0 failed).

## Criterion 2 — `... | grep -ic pass` → ≥ 7

Command run:
```
bash tests/test_drain_scheduler_window.sh 2>&1 | grep -ic pass
```
Output: `8`
Result: ✓ PASS (8 ≥ 7 — one "PASS: (x) ..." line per scenario a–g, plus the summary "pass: 21 fail: 0" line which also matches `pass` case-insensitively).

## Criterion 3 — `... | grep -c FAIL` → 0

Command run:
```
bash tests/test_drain_scheduler_window.sh 2>&1 | grep -c FAIL
```
Output: `0`
Result: ✓ PASS.

## Scenario coverage (Steps 3a–3g)

Read the full test file (tests/test_drain_scheduler_window.sh, 448 lines). Confirmed each named case is present and does what Steps 3a-3g specify:

- (a) `case_a`: 4 disjoint-Touch tasks on one Group line, W=3 — asserts admission order "01 02 03", exactly 3 live, and the 4th refused while full. ✓
- (b) `case_b`: two tasks sharing `b.txt` in Touch — only 01 admits first, 02 refused while 01 in-progress, 02 admits once 01 is done (not starved). ✓
- (c) `case_c`: task 03 named on no `Group:` line — refused while window non-empty, admissible once empty, and blocks others once running solo. ✓
- (d) `case_d`: mutual `Depends on:` cycle (01↔02) — `next_admissible` returns empty and `scheduler_step` returns `REPORT` (not hang); a satisfiable-variant (`case-d2`) confirms REPORT fires only on true unsatisfiability, returning `ADMIT 01` instead. ✓
- (e) `case_e`: task 90 committed `in-progress` (simulated zombie, empty live inflight) sharing `shared.txt` with pending 01 — 01 refused, `zombie_block_report` returns the literal string `"blocked by suspected zombie 90"`, and Touch-disjoint task 02 admits (not starved). ✓
- (f) `case_f`: `scheduler_step` with `hold=1` returns `HOLD` despite a free slot and eligible task; `hold=0` then returns `ADMIT 01`. ✓
- (g) `case_g`: separate `merge_check` function (not the admission path) — a branch whose changed paths stay in Touch+taskfile+evidence dir merges (`MERGE_OK`), one with a path outside is rejected (`MERGE_REJECT:...`), and the rejection message names the offending path `src/OUTSIDE.ts`. ✓

## Assertion meaningfulness (mutation test)

To confirm assertions aren't vacuous, temporarily neutered the Touch-overlap check inside `admissible()` (`sed` replacing the `touch_blocker` guard with `true`), re-ran the suite, then restored the original file from a pre-mutation copy (not `git checkout`, since the file is untracked and that would have deleted it).

Mutated run result: cases (b) and (e) — the two cases that specifically exercise Touch-overlap refusal — failed as expected:
```
FAIL: (b) Touch-overlapping sibling refused while claim held (expected: '', got: '02')
FAIL: (b) Touch-overlap refusal
FAIL: (e) pending task overlapping a zombie's claim is refused
FAIL: (e) a Touch-disjoint task admits, not starved behind the zombie (expected: '02', got: '01')
FAIL: (e) zombie-claimed Touch blocks without starving
pass: 18 fail: 3
EXIT:1
```
Other cases (a, c, d, f, g) remained green, showing the assertions are scoped to the behavior each case targets rather than incidentally coupled. Restored file verified byte-identical to the pre-mutation copy via `diff` (no output) and confirmed exit 0 again after restore.

## Regression check — full test suite

Command run:
```
for t in tests/test_*.sh; do bash "$t"; done
```
All 9 test files in `tests/` (`test_check_token_discipline.sh`, `test_doc_links.sh`,
`test_drain_owner_protocol.sh`, `test_drain_scheduler_window.sh`,
`test_hook_templates.sh`, `test_install_gates.sh`, `test_review_skip.sh`,
`test_sync_workflows.sh`, `test_workboard_actionability.sh`,
`test_workboard_render.sh`) exited 0 with 0 failures reported in each summary
line. No regression from this change.

## Scope / diff confinement

```
git status --porcelain=v1
```
Output: `?? tests/test_drain_scheduler_window.sh` — the only change in the
working tree relative to base commit `3edad3c545b3f37aae7d30997053efdc6591434e`
is this single new, untracked file. `git diff 3edad3c545b3f37aae7d30997053efdc6591434e --stat`
produced no output (HEAD == base commit, no tracked-file changes at all).
Matches the task's `Touch:` line exactly (`tests/test_drain_scheduler_window.sh`).
No product/skill files touched.

## Append-only task-file check

```
git diff 3edad3c545b3f37aae7d30997053efdc6591434e -- '*/tasks/*.md'
```
Output: empty — no task file (this task's or any other's) has been modified at
all relative to base. The task file's `Status:` line still reads `in-progress`
and all three acceptance checkboxes are still unticked, consistent with the
statement that close-out (ticking boxes / flipping Status) happens after this
verification, not before.

## Observations (not failures)

- Minor inconsistency in the task file itself (pre-existing, not caused by
  this worker): the header line reads `Spec: ../SPEC.md (requirements R1, R5,
  R8a, R9)` while the Goal prose and Step 3g both reference R4 for the
  merge-time Touch requirement. The test file's own header comment correctly
  cites "R1, R4, R8a, R9". This is a task-file-authoring nit outside this
  task's Touch scope to fix, noted for whoever finalizes the task file.

## Overall verdict: PASS

All three acceptance commands pass exactly as specified, all seven named
scenarios are genuinely exercised with meaningful (non-vacuous, mutation-
confirmed) assertions, the change is confined to the single new test file
per Touch, the full existing test suite still passes with no regressions,
and no task file text was altered by the worker.
