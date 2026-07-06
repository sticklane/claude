Verdict: PASS

Task: specs/drain-rolling-window/tasks/08-fix-task-04-header-typo.md
Base for diff check: fc7f5dd96363ea4aee419d866132a641e09c05a7

## Criterion 1: grep on task 04's Spec header

Command:
    grep -n '^Spec:' specs/drain-rolling-window/tasks/04-scheduler-admission-test.md

Output:
    11:Spec: ../SPEC.md (requirements R1, R4, R8a, R9)

Result: contains "R4", does not contain "R5". PASS.

## Criterion 2: append-only task-file diff check

Command:
    git diff fc7f5dd96363ea4aee419d866132a641e09c05a7 -- specs/drain-rolling-window/tasks/

Output (full):
    diff --git a/specs/drain-rolling-window/tasks/04-scheduler-admission-test.md b/specs/drain-rolling-window/tasks/04-scheduler-admission-test.md
    index cc9c200..8c508c2 100644
    --- a/specs/drain-rolling-window/tasks/04-scheduler-admission-test.md
    +++ b/specs/drain-rolling-window/tasks/04-scheduler-admission-test.md
    @@ -8,7 +8,7 @@ Status: done
     Depends on: none
     Priority: P0
     Budget: 22 turns
    -Spec: ../SPEC.md (requirements R1, R5, R8a, R9)
    +Spec: ../SPEC.md (requirements R1, R4, R8a, R9)
     Touch: tests/test_drain_scheduler_window.sh

     ## Goal
    diff --git a/specs/drain-rolling-window/tasks/08-fix-task-04-header-typo.md b/specs/drain-rolling-window/tasks/08-fix-task-04-header-typo.md
    index a1a9134..9de8a46 100644
    --- a/specs/drain-rolling-window/tasks/08-fix-task-04-header-typo.md
    +++ b/specs/drain-rolling-window/tasks/08-fix-task-04-header-typo.md
    @@ -1,4 +1,4 @@
    -Status: in-progress
    +Status: done
     Depends on: none
     Priority: P3
     Budget: 4 turns
    @@ -17,6 +17,6 @@ Blocking: no
     ## Acceptance

    -- [ ] `grep -n '^Spec:' specs/drain-rolling-window/tasks/04-scheduler-admission-test.md` → contains "R4", not "R5"
    +- [x] `grep -n '^Spec:' specs/drain-rolling-window/tasks/04-scheduler-admission-test.md` → contains "R4", not "R5" — line 11 now reads `Spec: ../SPEC.md (requirements R1, R4, R8a, R9)`

     Note for drain: this task's Touch is a header line in ANOTHER task file (04, already done), not this task's own file — the merge-time whitelist check should treat that Touch-declared edit as in-scope, not as unexpected cross-file drift.

Analysis: Exactly two files changed, exactly the two authorized edits:
  1. task 04's Spec header: R5 -> R4 (single line, header only, no other
     content in task 04 touched) — explicitly authorized by task 08's
     Touch: header naming this file.
  2. task 08's own file: Status in-progress -> done, acceptance checkbox
     ticked with an evidence citation (line 11 content quoted inline).

No other tasks/ files touched. No scope creep. No behavior change to
task 04's test content, Goal, or Steps — only the Spec header line.

## Gates

This is a documentation/header-only one-line text fix across two markdown
task files; no source code, tests, lint, or build config were touched, so
no project build/lint/test gate applies beyond the grep check above.

## Scope creep

None found. Touch list (task 08's own Touch header names
specs/drain-rolling-window/tasks/04-scheduler-admission-test.md) matches
the sole cross-file edit made.

## Verdict

PASS — both criteria hold, diff contains only the two authorized edits.
