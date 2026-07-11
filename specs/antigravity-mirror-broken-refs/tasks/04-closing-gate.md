# Task 04: Closing gate — full test-suite sweep

Status: in-progress
Depends on: 01, 02, 03
Priority: P2
Budget: 3 turns
Spec: ../SPEC.md (full acceptance criteria)
Touch: none (verification only; no source edits expected)

## Goal

All of this repo's `tests/test_*.sh` gates pass together after tasks 01-03
have landed, confirming none of the three parallel fixes regressed the
existence-parity gate or each other's Python suites.

## Touch

Verification only. If this task finds a failure, it documents the failure
and stops — it does not silently patch another task's Touch scope; that
goes back to whichever task owns the failing path.

## Steps

1. Run every test script in the repo's `tests/` directory.
2. Run the four mirrored Python suites once more together (`workboard`,
   `list-specs`, `prioritize`, `_shared`) to confirm the combined 162-test
   baseline still holds (140 across the three touched by this spec, plus
   `_shared`'s untouched 22).
3. If anything fails, report exactly which command and output, and stop —
   do not attempt fixes outside this task's Touch scope.

## Acceptance

- [ ] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` → no `FAIL` lines
- [ ] `cd antigravity/.agents/skills/workboard && python3 -m pytest -q` → 93 passed
- [ ] `cd antigravity/.agents/skills/list-specs && python3 -m pytest -q` → 30 passed
- [ ] `cd antigravity/.agents/skills/prioritize && python3 -m pytest -q` → 17 passed
- [ ] `cd antigravity/.agents/skills/_shared && python3 -m pytest -q` → 22 passed
