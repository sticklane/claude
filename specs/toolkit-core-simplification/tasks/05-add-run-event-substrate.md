# Task 05: add the joined run-event substrate

<!-- Task state is canonical in bd. The Status line is frozen display and is not edited by workers. -->

Status: pending
Depends on: 02
Priority: P1
Budget: 36 turns
Spec: ../SPEC.md (requirement R5)
Touch: agentic/cli.py, agentic/events.py, agentic/schema/run-event.json, tests/test_agentic_events.py, tests/inventory/05-run-events.json, specs/toolkit-core-simplification/surface-inventory/05-run-events.json

## Goal

Provide a cross-worktree, append-only event writer and reader with the exact R5
schema, run/attempt/reopen semantics, locking, durability, and explicit
unknown handling. Expose narrow CLI event operations that native
orchestrators can call without giving the module scheduling authority.

## Touch

The event module may append and validate records only. It must not select
issues, launch agents, schedule retries, merge, choose models, or change bd
state.

## Steps

1. Write failing tests for UUIDv7 propagation, common-dir resolution,
   concurrent writers, size limit, one-write append plus fsync, malformed
   interior/final records, retention boundaries, and event-write failure.
2. Implement the schema, writer, reader, run/retry/reopen helpers, and minimal
   CLI surface.
3. Verify that linked worktrees append to the same monthly log and that
   telemetry failure cannot change tracker state.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_events.py -q` → passes concurrent cross-process and linked-worktree fixtures plus every named failure path (L3).
- [ ] `python3 -m json.tool agentic/schema/run-event.json >/dev/null` → schema parses, while the pytest suite proves behavioral validation (L1 complemented by the L3 fixture).
- [ ] `bash scripts/check.sh` → the updated inventoried suite is green (L3).
