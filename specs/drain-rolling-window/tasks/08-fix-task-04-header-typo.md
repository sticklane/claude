Status: pending
Depends on: none
Priority: P3
Budget: 4 turns
Discovered-from: specs/drain-rolling-window/tasks/04-scheduler-admission-test.md
Spec: ../SPEC.md
Touch: specs/drain-rolling-window/tasks/04-scheduler-admission-test.md
Blocking: no

# Task 04's Spec: header lists R5 instead of R4

`specs/drain-rolling-window/tasks/04-scheduler-admission-test.md`'s `Spec:` header line reads "requirements R1, R5, R8a, R9", but the task's own Goal, Step 3g, and SPEC.md's acceptance criterion all key the merge-time Touch violation case (Step 3g / test case (g)) to R4, not R5. The test itself correctly implements R4 — this is a header-text typo only, no behavior change needed. One-line fix: `R5` → `R4` in the header.

## Steps

1. In `specs/drain-rolling-window/tasks/04-scheduler-admission-test.md`'s `Spec:` header line, change "R5" to "R4" (the only change — task 04 is already `done`; this is a header-text-only correction, not a reopening of its work).

## Acceptance

- [ ] `grep -n '^Spec:' specs/drain-rolling-window/tasks/04-scheduler-admission-test.md` → contains "R4", not "R5"

Note for drain: this task's Touch is a header line in ANOTHER task file (04, already done), not this task's own file — the merge-time whitelist check should treat that Touch-declared edit as in-scope, not as unexpected cross-file drift.
