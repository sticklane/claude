# Task 06: bin/drain-watch — the live in-flight view

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->

Status: pending
Depends on: 04
Priority: P2
Budget: 30 turns
Spec: ../SPEC.md (requirements EP8, decision D4)
Touch: bin/drain-watch, tests/test_drain_watch.sh, tests/inventory/drain-economy.json, specs/toolkit-core-simplification/surface-inventory/drain-economy.json

## Goal

`bin/drain-watch [run-bead-id]` tails the run log and the native workflow
progress stream and renders one row per in-flight agent, grouped by bd id:
label, tier, state, attempt, tokens, elapsed. A header row names the current
focus. It is read-only, and it degrades to run-log-only when no workflow stream
exists. A `--once` mode renders a single frame and exits, so the view is
testable without a live run.

## Touch

Read-only by construction: no bd writes, no file edits, no dispatch. It shares
task 04's run-log grammar with `bin/drain-report` (task 05) but neither script
imports the other — if the parse logic wants sharing, extract it only when both
exist and a third caller appears. Per D4 this viewer retires into `agentic watch`
if that spec ever unparks; it does not unpark it here.

## Steps

1. Write the failing test first: `tests/test_drain_watch.sh` over `mktemp -d`
   fixtures — one with both a run log and a synthetic workflow progress stream,
   one with a run log only. Assert on parsed rows (one per in-flight bd id,
   with the six documented fields) and on the focus header, never on exact
   column formatting.
2. Assert the degradation path explicitly: the run-log-only fixture exits 0 and
   still renders rows, rather than erroring on the missing stream.
3. Assert read-only-ness by observation: the fixture directory's file set and
   the bd export's sha256 are unchanged after a `--once` run.
4. Implement `bin/drain-watch` with `--once` and the default tail mode, matching
   the existing `bin/` scripts' language and conventions.
5. Register the new script and test in the surface and test inventories.

## Acceptance

- [ ] `bash tests/test_drain_watch.sh` → exits 0, reports 0 failures. **L2**
- [ ] `bin/drain-watch --once <both-sources-fixture> | head -1 | grep -c 'focus'`
      → 1, and the row count equals the fixture's in-flight agent count as
      asserted in the test. **L2**
- [ ] `bin/drain-watch --once <run-log-only-fixture>; echo $?` → 0 with rows
      rendered, proving graceful degradation. **L2**
- [ ] The read-only assertion in the test passes: fixture sha256 and file count
      unchanged after a `--once` run. **L2**
- [ ] `python3 scripts/inventory-core-surface.py --root . --check specs/toolkit-core-simplification/BASELINE.json 2>&1 | grep -c 'unclassified\|drift'` → 0. **L2**
- [ ] `bash scripts/check.sh` → `check.sh: green`. **L2**
