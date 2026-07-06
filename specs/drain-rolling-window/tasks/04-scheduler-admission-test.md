# Task 04: Model-free scheduler admission test

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P0
Budget: 22 turns
Spec: ../SPEC.md (requirements R1, R4, R8a, R9)
Touch: tests/test_drain_scheduler_window.sh

## Goal

A new shell script, `tests/test_drain_scheduler_window.sh`, simulates the
rolling-window admission function purely mechanically (no LLM, no
`claude` invocation) — mirroring `tests/test_drain_owner_protocol.sh`'s
style (plain shell, custom assert helpers, throwaway fixture task files
in a temp dir, one `report_case`/pass-fail line per scenario). It proves
R9's termination properties hold given the requirements text this SPEC
already pins, independent of how task 01 phrases the prose. Running it
is this spec's cheapest defense against a deadlocking or livelocking
scheduler.

## Touch

In scope: the single new test file only.

Out of scope: `.claude/skills/drain/SKILL.md` / `reference.md` (task 01
owns those; this test targets the requirements text in SPEC.md, not any
particular prose file, so it has no dependency on task 01 landing first).

## Steps

1. Read `tests/test_drain_owner_protocol.sh` in full to match its
   fixture-construction and assertion style (temp-dir git repos, header-
   only task-file fixtures, `assert`/`assert_not`/`assert_eq`/
   `report_case`/`note_pass`/`note_fail` helpers).
2. Write a pure-bash (or awk-assisted) admission function that takes: a
   set of task headers (Status, Depends on, Touch, and which `Group:`
   line(s) each task's number appears on), a window size W, and the set
   of currently in-flight task numbers — and returns the next admissible
   task, per R1: `Status: pending`, all deps `done`, Touch disjoint from
   the claim set (Touch of every committed `in-progress` task, zombie or
   not), and co-admissible (shares a `Group:` line with every in-flight
   task, or the window is empty and this task is on no `Group:` line).
3. Write fixture scenarios and one test case per scenario, in the style
   of test_drain_owner_protocol.sh's five cases:
   a. **Admission order under W=3**: three pending tasks with disjoint
      Touch and a `- Group:` line naming all three admit together;
      window fills to 3, not fewer.
   b. **Touch-overlap refusal**: two pending tasks sharing a path in
      Touch — only one admits even though both are otherwise eligible.
   c. **No-group task runs solo**: a pending task named on no `Group:`
      line is refused admission while the window is non-empty, and
      admitted once the window is empty; nothing else admits alongside
      it.
   d. **`Depends on:` cycle terminates with a report, not a hang**: two
      tasks depending on each other, admission returns empty, and the
      unsatisfiable-remainder check (R9.3) fires rather than looping.
   e. **Zombie-claimed Touch blocks, doesn't starve**: a task with
      committed `Status: in-progress` but no live window slot (a
      simulated zombie) whose Touch overlaps a pending task — the
      pending task is refused with a "blocked by suspected zombie
      `<task>`"-shaped message; a Touch-disjoint pending task admits
      normally (not starved by the zombie).
   f. **Admission held during a simulated tournament (R8a)**: with a
      tournament flagged open, no new admissions occur even though the
      window has free slots; admission resumes once the tournament flag
      clears.
   g. **Merge-time Touch violation is rejected (R4)**: simulate a
      landing branch whose actual changed paths (a fixture file list,
      not the task's declared Touch:) include a path outside its task's
      `Touch:` list plus its own task file — the merge step (a
      function separate from admission) refuses it as a merge failure /
      slot-machine trigger, not a silent merge. This is the spec's
      headline safety requirement (closing the plan-time-only
      enforcement gap) and must have a case here, since admission-time
      Touch checks (case b) don't exercise it.
4. Each case prints a clear PASS/FAIL line; the script exits non-zero if
   any case fails, matching test_drain_owner_protocol.sh's exit-code
   contract.
5. Run the script locally and confirm all cases pass before marking this
   task done.

## Acceptance

- [x] `bash tests/test_drain_scheduler_window.sh` → exit 0
      (verifier: exit 0, output `pass: 21 fail: 0`; evidence/04-scheduler-admission-test.md)
- [x] `bash tests/test_drain_scheduler_window.sh 2>&1 | grep -ic pass` → ≥ 7
      (verifier: got 8, one per scenario 3a–3g; evidence/04-scheduler-admission-test.md)
- [x] `bash tests/test_drain_scheduler_window.sh 2>&1 | grep -c FAIL` → 0
      (verifier: got 0; mutation check confirmed non-vacuous; evidence/04-scheduler-admission-test.md)

## Discovered

- This task file's own `Spec:` header lists requirements "R1, R5, R8a, R9", but the Goal, Step 3g, and SPEC.md's acceptance criterion all key the merge-time Touch case to R4, not R5 — a pre-existing header typo (behavior unaffected; the test correctly implements R4). See specs/drain-rolling-window/tasks/08-fix-task-04-header-typo.md.
