# Task 06: Fixture T3 — `sitegen` (Node breadth-first refactor) + reference

Status: in-progress
Depends on: 01
Priority: P2
Budget: 20 turns
Rigor: prototype
Spec: ../SPEC.md (corpus T3; acceptance criterion 5 partial)
Touch: evals/headtohead/tasks/sitegen/

## Goal

The T3 fixture exists: a small static-site generator (`render.js`, `feed.js`,
`archive.js`, `meta.js`) using Node stdlib + `node:test`, whose date-formatting
logic is duplicated with drift across modules, one copy wrong for certain dates.
Ships with a green suite at the snapshot, the ≤6-sentence brief from the spec, a
HIDDEN `assert.sh` (out of mount per task 01's layout), and a COMMITTED reference
solution (out of mount) that unifies the duplicates into one shared module,
migrates every call site, keeps rendered output identical except the corrected
buggy dates. The hidden script FAILS against the untouched snapshot and PASSES
against the reference solution.

## Touch

Owns `tasks/sitegen/` only. Snapshot + brief inside the arm mount; `assert.sh`
and reference solution OUTSIDE both mounts at the layout task 01 dictates. Do NOT
edit the runner, other fixtures, or `calibrate.sh`.

## Steps

1. Build the snapshot: `render.js`, `feed.js`, `archive.js`, `meta.js`, sample
   site, `node:test` suite green; date-format logic duplicated with drift, one
   copy wrong for certain dates.
2. Write the brief verbatim from the spec's T3 brief; confirm ≤6 sentences.
3. Write the hidden `assert.sh`: full suite; build the sample site and diff
   against a golden output tree (correct dates baked in); assert exactly one
   date-format definition remains across `src/` (structural count); known-bad
   dates now render correctly. Store out of mount.
4. Write and commit the reference solution (single shared date module + all call
   sites migrated + corrected dates + coverage pinning corrected behavior), out
   of mount.
5. Verify RED and GREEN.

## Acceptance

- [ ] `cd evals/headtohead/tasks/sitegen/<snapshot> && node --test` (or the fixture's test command) → suite green at the snapshot
- [ ] running the hidden `assert.sh` against the UNTOUCHED snapshot → exits non-zero (RED)
- [ ] running the hidden `assert.sh` against the committed reference solution → exits 0 (GREEN)
- [ ] the T3 brief is ≤6 sentences (sentence-count check)
