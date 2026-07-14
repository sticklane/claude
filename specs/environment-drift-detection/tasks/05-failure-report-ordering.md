# Task 05: surface failing-stage output first in check reporting

Status: in-progress
Depends on: 01, 04
Priority: P3
Budget: 12 turns
Spec: ../SPEC.md (requirement R5)
Touch: templates/check.sh.tmpl, tests/test_install_gates.sh

## Goal

When a check invocation's failing stage's output is currently buried after
other stages' passing output, reorder the reporting so the failing stage's
output is surfaced first/prominently. `templates/check.sh.tmpl`'s own
`run_stage` helper already exits on first failure and prints only that
stage's output (confirmed in SPEC.md's R5 body) — so this requirement is
about the CALLING context: a multi-workspace wrapper stage that itself runs
several sub-checks and currently prints all of them before the failing one.

**This requirement may resolve to DEFERRED.** SPEC.md's Open Questions
section flags that no such live wrapper was located during spec research —
if this task finds no multi-sub-check wrapper anywhere in this toolkit's
own `templates/`, `bin/`, or a repo it manages, record verdict DEFERRED
with the locations checked, rather than inventing a wrapper to fix. Do not
mark this task done without either (a) a located wrapper with its ordering
fixed and tested, or (b) an explicit DEFERRED verdict recording where you
looked.

## Touch

This task depends on Task 01 because both edit `templates/check.sh.tmpl` —
rebase onto Task 01's merged change before starting. This task also
depends on Task 04 because both may extend `tests/test_install_gates.sh` —
rebase onto Task 04's merged change too, so there is no collision on that
shared test file (Tasks 04 and 05 run solo, never concurrently, even
though each only depends on Task 01). Do not touch `templates/
stop-gate.sh` or `bin/install-gates`'s docs-only-diff logic (Task 04 owns
those).

## Steps

1. Read `templates/check.sh.tmpl` in full (short) and confirm for yourself
   that `run_stage` already exits on first failure and prints only that
   stage's output — this is the documented baseline, not the bug.
2. Search this repo for any wrapper stage that itself runs multiple
   sub-checks and prints all of them before a failure surfaces — e.g. a
   `run_stage` line whose command is itself a multi-step script (a
   workspace-iterating loop, a `pnpm -r` fan-out, or similar). Check
   `bin/install-gates`'s stack detection for any such generated line, and
   check whether any consuming repo's generated `check.sh` (if one is
   checked into this repo, e.g. under a fixture or test directory) has
   this shape.
3. If found: write a failing test in `tests/test_install_gates.sh`
   reproducing the "failing sub-check's output appears after passing
   sub-checks' output" symptom, then reorder the wrapper's reporting so the
   failing sub-check's output prints first/prominently. Make the test
   green.
4. If not found anywhere in scope: do not implement a speculative fix.
   Record verdict DEFERRED in this task file's own status area, listing
   exactly what was searched (per SPEC.md's Open Questions instruction),
   and stop — this is a legitimate, spec-anticipated outcome, not a
   failure.
5. Either way, run this repo's own check command before committing (a
   DEFERRED verdict with no code change still needs the repo left green).

## Acceptance

- [ ] EITHER: a located wrapper's failure-reporting is fixed, with a new
      regression test in `tests/test_install_gates.sh` that exits 0 and
      exercises the "failing sub-check surfaces first" behavior
- [ ] OR: verdict DEFERRED is recorded with the specific locations checked
      (per SPEC.md's Open Questions self-scoping instruction for R5)
- [ ] `bash tests/test_install_gates.sh` exits 0 either way (no regression)
