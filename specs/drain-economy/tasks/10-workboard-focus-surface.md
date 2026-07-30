# Task 10: the workboard's focus surface

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->

Status: pending
Depends on: 09
Priority: P2
Budget: 30 turns
Spec: ../SPEC.md (requirement EP14 workboard half, decision D8)
Touch: .claude/skills/workboard/workboard.py, .claude/skills/workboard/test_workboard.py, .claude/skills/workboard/reference.md, tests/inventory/drain-economy-10.json

## Goal

`/workboard` leads with the focus. NOW.md renders at the top with the current
focus named, specs blocked on a human badge strictly first regardless of any
other sort field, and each spec shows a burnup — admitted versus closed,
cumulative — so a feature's real trajectory is visible next to its inventory.

## Touch

Rendering only. Every number comes from `bin/spec-status --json` (task 09);
this task must NOT re-derive thrash, acceptance counts, or burnup inputs, and
must NOT edit `bin/spec-status`. It also must not touch the agent-console
server's launchd wiring — the dashboard reloads on refresh, so no service
restart belongs in this task's acceptance.

`docs/memory/workboard-mirror-verbatim.md` governs how workboard mirrors
underlying state; follow it rather than restating it.

## Steps

1. Write the failing test first in `.claude/skills/workboard/test_workboard.py`,
   following the file's existing style: two fixture specs, one blocked on a
   human, asserting the JSON the view is built from — the blocked spec sorts
   first regardless of the other's acceptance count, recency, or slug order,
   and NOW.md order heads the listing.
2. Add a burnup case: a fixture with known admitted and closed counts across
   two passes exposes both cumulative series.
3. Implement the rendering: NOW.md block at the top naming the current focus,
   blocked-on-human badge first, per-spec burnup. Read `bin/spec-status --json`
   for every value.
4. Note the new surface in `.claude/skills/workboard/reference.md` where the
   existing view sections are described.
5. Register the touched surfaces in the test inventory.

## Acceptance

- [ ] `python3 -m pytest .claude/skills/workboard/test_workboard.py -q` →
      passes with the new cases included. **L2**
- [ ] The blocked-first assertion passes with the fixture pair *swapped* in
      input order — asserted in the test, proving the sort is on
      blocked-on-human and not on input order. **L2**
- [ ] The burnup fixture exposes both cumulative series with the hand-computed
      values — asserted in the test. **L2**
- [ ] `grep -c 'spec-status' .claude/skills/workboard/workboard.py` → ≥ 1 and
      `grep -c 'thrash' .claude/skills/workboard/workboard.py` → 0, proving the
      view consumes the derivation rather than duplicating it. **L1**
- [ ] `bash scripts/check.sh` → `check.sh: green`. **L2**
