# Task 05: Fixture T2 — `notes-api` (Python stdlib HTTP additive feature) + reference

Status: done
Depends on: 01
Priority: P2
Budget: 20 turns
Rigor: prototype
Spec: ../SPEC.md (corpus T2; acceptance criterion 5 partial)
Touch: evals/headtohead/tasks/notes-api/

## Goal

The T2 fixture exists: a small JSON notes service (`router.py` / `handlers.py` /
`store.py` / `validation.py` / `API.md` + tests), stdlib HTTP only, whose list
endpoint returns everything at once. Ships with a green suite at the snapshot,
the ≤6-sentence brief from the spec, a HIDDEN `assert.sh` (out of mount per task
01's layout), and a COMMITTED reference solution (out of mount) that adds
limit/offset pagination + optional tag filter with HTTP 400 validation in the
standard error shape. The hidden script FAILS against the untouched snapshot and
PASSES against the reference solution.

## Touch

Owns `tasks/notes-api/` only. Snapshot + brief inside the arm mount; `assert.sh`
and reference solution OUTSIDE both mounts at the layout task 01 dictates. Do NOT
edit the runner, other fixtures, or `calibrate.sh`.

## Steps

1. Build the snapshot: `router.py`, `handlers.py`, `store.py`, `validation.py`,
   `API.md`, tests; suite green; GET /notes returns all notes.
2. Write the brief verbatim from the spec's T2 brief; confirm ≤6 sentences.
3. Write the hidden `assert.sh`: full suite; black-box HTTP sequences against the
   running server — page math on a seeded store, tag filter alone and combined,
   `limit=0`/negative/non-numeric → 400 in the standard shape, offset past end →
   empty page with metadata; API.md names both parameters. Store out of mount.
4. Write and commit the reference solution (pagination + tag filter + 400
   validation + metadata for full paging + API.md update + new tests), out of
   mount.
5. Verify RED and GREEN.

## Acceptance

- [x] `cd evals/headtohead/tasks/notes-api/<snapshot> && python3 -m pytest` (or the fixture's test command) → suite green at the snapshot — verified: `repo/` suite 9 passed.
- [x] running the hidden `assert.sh` against the UNTOUCHED snapshot → exits non-zero (RED) — verified: `assert.sh repo` exits 1 (suite green, black-box paging/tag/400 checks fail).
- [x] running the hidden `assert.sh` against the committed reference solution → exits 0 (GREEN) — verified: `assert.sh reference` prints `BLACKBOX OK` / `PASS`, exit 0 (reference suite 17 passed).
- [x] the T2 brief is ≤6 sentences (sentence-count check) — verified: 5 sentences.
