# Task 02: bin/check-token-discipline + fixture tests (TDD)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: pending
Depends on: none
Priority: P1
Budget: 50 turns
Spec: ../SPEC.md (requirement R6)
Touch: bin/check-token-discipline, tests/test_check_token_discipline.sh

## Goal

`bin/check-token-discipline [skills-root]` exits 0 iff every file in the
spec's exact in-scope list passes the three paragraph-level checks
(dispatch→tier, output budget, bounded loops) and exits 1 with a
per-file, per-check report otherwise. `tests/test_check_token_discipline.sh`
is the contract: fixtures encode at minimum drain's actual retry
paragraph (PASS unmodified), the four must-NOT-flag prose lines, and the
two wrapped dispatches that must be SEEN — the implementer tunes regexes
until every fixture passes. Env-override pattern per the retired
sync-skills precedent (commits 05df3ef/0629fa7) so tests never touch the
real tree destructively.

## Touch

New files only. Note the checker will (correctly) exit 1 on the current
un-retrofitted tree — that is task 03's RED state, not a failure of this
task. Must NOT touch: any SKILL.md, .claude/rules/, .claude/workflows/,
plugin.json.

## Steps

1. Write `tests/test_check_token_discipline.sh` first with the spec's
   minimum fixture set; run it against a stub checker → all failing (RED).
   Per the SPEC's 2026-07-03 amendment, include a must-PASS fixture for a
   named generation cap ("max-generations 10" phrasing, per drain's baton
   step) — a relaunch ceiling counts as a stated bound even though the
   numeral exceeds 4.
2. Implement the checker: blank-line paragraphs, frontmatter and
   table-row skipping, the three checks with the spec's trigger/exclusion
   semantics, per-file per-check report, exit codes.
3. Tune until the fixture suite passes (GREEN); refactor.
4. Record `bin/check-token-discipline` exit-1 output on the current tree
   (the pre-retrofit baseline task 03 will flip).

## Acceptance

- [ ] `bash tests/test_check_token_discipline.sh` → exit 0, covering at minimum: drain's retry paragraph passes the loop check unmodified; the four spec-named prose lines are NOT flagged; the two spec-named wrapped dispatches ARE seen as dispatches
- [ ] `bin/check-token-discipline` on the current (pre-retrofit) tree → exit 1 with a per-file, per-check report naming in-scope files
- [ ] `bash -n bin/check-token-discipline` → exit 0; file is executable
