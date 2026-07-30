# Task 18: project repository activity without replacing fleet

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status is always the frozen initial display value `pending`; workers and orchestrators update bd, never this line. -->
<!-- Task definitions are immutable after registration. Workers report progress, decisions, and deferred questions to the orchestrator; they do not rewrite task files. -->

Status: pending
Depends on: 01, 15, 38, 37
Priority: P0
Budget: 38 turns
Spec: ../SPEC.md (requirements R8, R10, R11, R12, R16, R17)
Touch: agentic/cli.py, agentic/activity.py, agentic/schema/activity-v1.json, agentic/schema/public-json-surfaces-v1.json, tests/test_agentic_activity.py, tests/test_agentic_public_json_contract.py, tests/inventory/mardi-gras-18-activity.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-18-activity.json

## Goal

Add the bounded, read-only `agentic activity` projection over Beads,
dispatches, run and child events, session markers, registered worktrees, and
runtime liveness. It reports repository-scoped toolkit runs and children with
evidence grades while preserving `fleet` as the separate session-wide native
inventory for ad-hoc and cross-repository agents.

## Touch

`agentic.cli.build_parser` gains the activity command, while the implementation
consumes Task 16's `agentic.events.read_events` and
`agentic.events.monthly_log_path` contracts without changing their storage.
This task may not edit either fleet entrypoint, read transcripts or arbitrary
output tails, append or repair state, signal processes, infer ownership from
branch names, or project ad-hoc native agents into repository activity.

## Steps

1. Write failing source-deadline, exact/possible/unknown correlation,
   process-identity, stale-source, injection, repository-boundary, child
   lifecycle, and read-only fixtures first.
2. Implement the closed `agentic.activity/v1` schema, R12 canonical
   serialization, echoed request sequence, per-source 1.5-second deadlines,
   three-second total deadline, stable source errors, and bounded public
   strings and arrays.
3. Join a UI dispatch to a canonical run only on exact dispatch, PID,
   process-start, boot, and current-boot evidence; keep closed tracker state
   separate from live or stale process evidence and downgrade every incomplete
   bridge rather than guessing.
4. Normalize Task 38's repository child events into deterministic agent rows
   with typed bounded outcomes. Treat a child whose terminal event is missing
   after exact parent/process death as `unknown`.
5. Prove that session-local ad-hoc and cross-repository native agents remain
   exclusively fleet-visible and add the new public surface to the closed
   schema and inventory registries.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_activity.py tests/test_agentic_events_v2.py tests/test_agentic_child_activity.py -q` → exact/possible/unknown joins, stale and hung sources, process reboot/PID reuse, direct and UI races, normalized child rows, and read-only behavior pass (L3).
- [ ] `python3 -m pytest tests/test_agentic_activity.py tests/test_agentic_child_activity.py -q -k 'deadline or sequence or read_only or fleet_scope or cross_repository or terminal_injection'` → deadlines and sequence ordering are enforced, hostile output is bounded, and agents outside the selected repository remain absent from activity rather than being stolen from fleet (L3).
- [ ] `python3 -m pytest tests/test_agentic_public_json_contract.py -q` → the activity envelope, every child row and error, all string/numeric leaves, and canonical byte bounds are registered and exercised (L2).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json && bash scripts/check.sh` → the activity surface is classified and the full toolkit gate passes without fleet edits (L3).
