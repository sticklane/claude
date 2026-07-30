# Task 09: bin/spec-status — proximity, thrash, and the bug phase pointer

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->

Status: pending
Depends on: 08
Priority: P1
Budget: 40 turns
Spec: ../SPEC.md (requirements EP13, EP14 status line, EP15, decision D6)
Touch: bin/spec-status, tests/test_spec_status.sh, tests/fixtures/spec-status, tests/inventory/drain-economy.json, specs/toolkit-core-simplification/surface-inventory/drain-economy.json

## Goal

`bin/spec-status [slug]` answers "how close is this feature" from measured
sources. With a slug it prints
`slug · acceptance g/n · open k (b blocked-on-you) · last pass +Δgreen, net±m · thrash: <ids|none> · est <p> passes`;
without one, a line per spec with open work, NOW.md order first. Thrash is
derived, not guessed: tasks with ≥2 claims from bd history, DEFERRED-then-
redispatched pairs, the `/critique` NOT-READY streak, and last pass's net
frontier delta — and the flag names the specific issues. Bug-labelled beads
carry a `phase:` pointer (`reproduced|localized|fix-proposed|fix-verified|
regressions-green`) and show that phase instead of a fraction until
`fix-verified`.

## Touch

This task owns the status line and the derivations behind it. The workboard's
rendering of the same data is task 10's, and the two must not both compute the
numbers — this script is the single derivation, and task 10 consumes its output
or its module. It reads `acceptance-status.json` (task 08) and bd history; it
never writes either.

Worker verdicts setting the bug `phase:` are drain's and build's to emit; this
task defines the metadata's vocabulary and reads it. Where a phase is absent,
print no phase rather than assuming one.

## Steps

1. Write the failing test first: `tests/test_spec_status.sh` over fixtures in
   `tests/fixtures/spec-status/` — synthetic bd exports plus
   `acceptance-status.json` files with known values. Assert on parsed fields
   from the printed line, never on its exact punctuation.
2. Cover each derivation independently and degrade gracefully per missing
   source: no `acceptance-status.json` suppresses the acceptance segment; no
   critique history suppresses the streak input; no prior pass suppresses
   `last pass` and `est`. A missing source never zeroes a number it cannot see.
3. Cover thrash: a fixture issue with 2 claims appears by id in `thrash:`; a
   fixture with none prints `thrash: none`; a DEFERRED-then-redispatched pair
   is counted once, not twice.
4. Cover the bug phase: a fixture bug bead at `phase: localized` prints that
   phase and no fraction; the same bead at `fix-verified` prints the fraction
   again.
5. Cover ordering: with no slug, specs named in NOW.md print first in NOW.md
   order, and specs with open work but no NOW.md entry follow.
6. Implement `bin/spec-status`, matching the existing `bin/` scripts' language
   and conventions, with a machine-readable `--json` mode alongside the human
   line so task 10 does not re-parse formatted text.
7. Register the new script, fixtures, and test in the surface and test
   inventories.

## Acceptance

- [ ] `bash tests/test_spec_status.sh` → exits 0, reports 0 failures. **L2**
- [ ] `bin/spec-status <fixture> --json | jq -e '.blocked_on_you >= 1 and (.thrash|length) >= 1'`
      → true on the thrash fixture, and `jq -r '.thrash|join(",")'` names the
      ≥2-claim issue id. **L2**
- [ ] `bin/spec-status <no-thrash-fixture> | grep -c 'thrash: none'` → 1. **L2**
- [ ] `bin/spec-status <bug-fixture> --json | jq -e '.phase == "localized" and (has("acceptance_fraction")|not)'`
      → true; the same fixture at `fix-verified` returns the fraction. **L2**
- [ ] `bin/spec-status --json | jq -r '.[0].slug'` → the first slug in the
      fixture NOW.md, proving NOW.md order heads the listing. **L2**
- [ ] Missing-source fixture (no `acceptance-status.json`): the acceptance
      segment is absent rather than `0/0` — asserted in the test. **L2**
- [ ] `python3 scripts/inventory-core-surface.py --root . --check specs/toolkit-core-simplification/BASELINE.json 2>&1 | grep -c 'unclassified\|drift'` → 0. **L2**
- [ ] `bash scripts/check.sh` → `check.sh: green`. **L2**
