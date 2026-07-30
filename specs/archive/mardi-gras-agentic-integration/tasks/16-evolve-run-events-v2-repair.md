# Task 16: repair the run-event version 2 evolution

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: 01, 14, 37
Priority: P0
Budget: 32 turns
Spec: ../SPEC.md (requirements R5, R10, R11, R12, R17)
Touch: agentic/events.py, agentic/schema/run-event-v2.json, tests/test_agentic_events_v2.py, tests/inventory/mardi-gras-16-events-v2.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-16-events-v2.json

## Goal

Evolve the shipped run-event substrate without breaking strict version-1
packages that share the repository. Version 2 adds validated
dispatch/process correlation and normalized toolkit-child lifecycle records;
new readers merge both partitions under one retention policy, while legacy
readers never open the new partition.

## Touch

This task owns only the additive v2 schema, partition, append/read/normalize
logic, and event tests. It consumes Task 14's process identity fixture
unchanged and provides record types for later façade instrumentation; it must
not edit the retained `tests/test_agentic_events.py`, instrument skills,
project activity state, authorize work, or add an independent trace store.

## Steps

1. Write failing coexistence, malformed-correlation, child-lifecycle,
   interrupted-tail, linked-worktree, and retention fixtures first.
2. Add a separate v2 log partition while preserving the exact version-1
   schema/path and strict legacy reader behavior.
3. Add optional UUIDv7 `dispatch_id`, positive `process_pid`, canonical
   `process_start`, and canonical `process_boot` fields by consuming the
   shared Task 14 fixture and validators.
4. Add append-only `agent_queued`, `agent_started`, `agent_completed`, and
   `agent_failed` records with R10's bounded IDs, parent/root relationships,
   role/kind, worktree/branch, instants, and typed summaries.
5. Extend new readers to validate, normalize, deterministically merge, and
   retain v1/v2 records under existing repository identity rules, downgrading
   malformed or incomplete correlation without granting event authority.
6. Add unique surface inventory entries without changing the retained v1
   test or making event emission affect claim/workflow outcomes.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_events_v2.py -q` → strict v1 readers ignore v2; new readers merge both partitions across linked worktrees; all correlation fixture boundaries and child lifecycle transitions validate; malformed tails/evidence fail safely; and one retention policy applies (L3).
- [ ] `python3 -m pytest tests/test_agentic_events_corrections.py tests/test_agentic_events_v2.py -q` → the additive evolution preserves every shipped append/read correction without editing the retained v1 test (L3).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json` → v2 event schema, tests, and new public surfaces are uniquely classified while retained content remains pinned (L2).
- [ ] `bash scripts/check.sh` → the repository gate remains green after the repaired event evolution (L3).
