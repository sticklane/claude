# Task 03: evolve run events to version 2

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: 01
Priority: P0
Budget: 28 turns
Spec: ../SPEC.md (requirements R11, R12, R17)
Touch: agentic/events.py, agentic/schema/run-event-v2.json, tests/test_agentic_events_v2.py, tests/inventory/mardi-gras-03-events.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-03-events.json

## Goal

Evolve the shipped run-event substrate without breaking strict version-1
packages that share the repository. New writers gain validated
dispatch/PID/start correlation fields in a version-2 partition, while new
readers normalize both versions under one retention policy.

## Touch

Do not edit the retained `tests/test_agentic_events.py`, add an independent
trace writer/store, or grant events any claim or recovery authority. Legacy
packages must never open the version-2 partition.

## Steps

1. Write failing version-coexistence, malformed-correlation, interrupted-tail,
   cross-worktree, and retention fixtures first.
2. Add a version-2 schema and partition while leaving the version-1 schema and
   strict reader behavior unchanged.
3. Extend current readers to validate, normalize, merge, and retain both
   partitions deterministically.
4. Validate optional dispatch ID, process PID, and process-start identity with
   bounded public strings and fail-safe warnings.
5. Add unique inventory fragments without changing the retained event test.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_events_v2.py -q` → old strict readers ignore the v2 partition; new readers merge v1/v2 across linked worktrees; malformed bridge fields and interrupted tails fail safely; one retention policy applies (L3).
- [ ] `python3 -m pytest tests/test_agentic_events_corrections.py tests/test_agentic_events_v2.py -q` → the additive evolution preserves every shipped append/read correction without editing the retained test (L3).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json` → version-2 event/test surfaces are classified and retained content remains pinned (L2).
- [ ] `bash scripts/check.sh` → the repository gate remains green after event evolution (L3).
