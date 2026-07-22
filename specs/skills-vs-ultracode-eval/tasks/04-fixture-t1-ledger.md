# Task 04: Fixture T1 — `ledger` (Python coupled bug-fix) + reference solution

Status: in-progress
Depends on: 01
Priority: P2
Budget: 20 turns
Rigor: prototype
Spec: ../SPEC.md (corpus T1; acceptance criterion 5 partial)
Touch: evals/headtohead/tasks/ledger/

## Goal

The T1 fixture exists: a small expense-tracker CLI (`storage.py` / `report.py` /
`cli.py` + tests) whose monthly totals drift by cents on some ledgers because
amounts flow as binary floats across all three modules. Ships with a green test
suite at the snapshot, the ≤6-sentence brief from the spec, a HIDDEN `assert.sh`
stored per the harness's out-of-mount layout (task 01), and a COMMITTED reference
solution (also out of mount). The hidden script FAILS against the untouched
snapshot and PASSES against the reference solution — proving the instrument
before any arm runs.

## Touch

Owns `tasks/ledger/` only. Place the snapshot repo + brief inside the arm mount;
place `assert.sh` and the reference solution OUTSIDE both arms' mounts at the
paths task 01's manifest/layout dictates. Do NOT edit the runner, other fixtures,
or `calibrate.sh` (task 07 wires calibration across all three).

## Steps

1. Build the snapshot: `storage.py`, `report.py`, `cli.py`, tests; suite green;
   the float-drift bug present (amounts as binary floats end to end).
2. Write the brief verbatim from the spec's T1 brief; confirm ≤6 sentences.
3. Write the hidden `assert.sh`: run full suite; three held-out ledgers
   (including float-pathological amounts) whose report totals must match exact
   expected values; the shipped repro ledger now exact. Store it out of mount.
4. Write and commit the reference solution (exact-to-the-cent fix, e.g. integer
   cents / Decimal; regression coverage added; CLI output format unchanged),
   stored out of mount.
5. Verify RED (assert fails on untouched snapshot) and GREEN (passes on
   reference).

## Acceptance

- [ ] `cd evals/headtohead/tasks/ledger/<snapshot> && python3 -m pytest` (or the fixture's test command) → suite green at the snapshot
- [ ] running the hidden `assert.sh` against the UNTOUCHED snapshot → exits non-zero (RED)
- [ ] running the hidden `assert.sh` against the committed reference solution → exits 0 (GREEN)
- [ ] the T1 brief is ≤6 sentences (sentence-count check)
