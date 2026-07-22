# Task 07: Calibration harness — RED/GREEN proof for all three fixtures

Status: pending
Depends on: 04, 05, 06
Priority: P1
Budget: 12 turns
Rigor: prototype
Spec: ../SPEC.md (acceptance criterion 5)
Touch: evals/headtohead/calibrate.sh

## Goal

`evals/headtohead/calibrate.sh` proves the instrument for all three real tasks in
one run: for each of `ledger` / `notes-api` / `sitegen` it prints `<task> RED OK`
(the hidden `assert.sh` fails against the untouched snapshot) and `<task> GREEN
OK` (it passes against the committed reference solution). It exits 0 only when
all six conditions hold, and non-zero (naming the failing condition) otherwise.

## Touch

Owns `calibrate.sh` only. It consumes the fixtures and reference solutions built
in tasks 04-06 via the out-of-mount layout task 01 established; it does not edit
any fixture or the runner.

## Steps

1. For each task, materialize the untouched snapshot and run its hidden
   `assert.sh` — expect non-zero → print `<task> RED OK`.
2. For each task, apply the committed reference solution and run the hidden
   `assert.sh` — expect zero → print `<task> GREEN OK`.
3. Track all six outcomes; exit 0 only if all six pass, else exit non-zero and
   name the failing `<task>`/phase.
4. Mechanical acceptance run (prototype rigor) — confirm the command below.

## Acceptance

- [ ] `bash evals/headtohead/calibrate.sh` → prints `ledger RED OK`, `ledger GREEN OK`, `notes-api RED OK`, `notes-api GREEN OK`, `sitegen RED OK`, `sitegen GREEN OK`; exits 0 only when all six hold
