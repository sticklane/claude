Status: draft
Priority: P3
Discovered-from: specs/drain-rolling-window/tasks/04-scheduler-admission-test.md
Spec: ../SPEC.md
Blocking: no

# Task 04's Spec: header lists R5 instead of R4

`specs/drain-rolling-window/tasks/04-scheduler-admission-test.md`'s `Spec:` header line reads "requirements R1, R5, R8a, R9", but the task's own Goal, Step 3g, and SPEC.md's acceptance criterion all key the merge-time Touch violation case (Step 3g / test case (g)) to R4, not R5. The test itself correctly implements R4 — this is a header-text typo only, no behavior change needed. One-line fix: `R5` → `R4` in the header.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
