# Task 05: project live activity

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: 02, 04
Priority: P0
Budget: 34 turns
Spec: ../SPEC.md (requirements R8, R10, R11, R12)
Touch: agentic/cli.py, agentic/activity.py, agentic/schema/activity-v1.json, tests/test_agentic_activity.py, tests/inventory/mardi-gras-05-activity.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-05-activity.json

## Goal

Add a bounded, read-only activity projection that joins Beads with dispatch,
run-event, session-claim, inflight, worktree, and process evidence. Every
reported state carries its source freshness and confidence; missing evidence
never becomes inferred ownership.

## Touch

This task may read existing state only. It must not append events, repair
markers, requeue work, signal processes, or add a UI-specific cache.

## Steps

1. Write failing exact/possible/unknown, stale-source, injection, and hung
   source fixtures first.
2. Implement concurrent or equivalently bounded source reads with individual
   and overall deadlines, echoed request sequence, capped strings, and
   stable error codes.
3. Join dispatch to run only when dispatch ID, supervisor PID, and process
   start all match the immutable lifecycle record; forbid issue/time and
   branch-prefix ownership inference.
4. Preserve closed tracker state separately from live or stale process
   evidence and expose last-good-friendly per-source envelopes.
5. Add the activity schema and unique inventory fragments.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_activity.py -q` → exact, possible, unknown, stale, malformed, closed-versus-live, and UI-loses/direct-wins fixtures produce the specified evidence grades (L3).
- [ ] `python3 -m pytest tests/test_agentic_activity.py -q -k 'deadline or sequence or read_only or terminal_injection'` → each source and total request are bounded, request sequence is echoed, no source mutates state, and controls/ANSI/OSC or oversized strings never reach output (L3).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json` → activity command/schema/test surfaces are inventoried (L2).
- [ ] `bash scripts/check.sh` → the repository gate remains green with activity projection enabled (L3).
