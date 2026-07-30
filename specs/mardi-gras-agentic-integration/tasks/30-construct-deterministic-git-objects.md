# Task 30: construct deterministic Git objects

<!-- Registration fields are frozen authoring-time inputs; bd owns live task state. -->
<!-- Status is always the initial display value `pending` and is never updated in this file. -->
<!-- Task definitions are immutable after registration. Workers report progress and discoveries through the orchestrator. -->

Status: pending
Depends on: 01, 29
Priority: P0
Budget: 40 turns
Spec: ../SPEC.md (requirement R20)
Touch: agentic/integration/model.py, agentic/integration/git_objects.py, tests/test_drain_worktree_integration.py, tests/mardi-integration-task-tests-v1.json

## Goal

Provide the closed Git capability profile and private deterministic
merge-tree/commit-tree constructor used by every later landing and rebuild.
Object bytes and OIDs must be reproducible across supported object/ref formats,
configuration, environment, timezone, and crash recovery.

## Touch

This task owns capability probing, the sanitized private Git environment,
per-input attribute validation, and deterministic object bytes. It does not
advance integration or target refs, resolve content conflicts, run gates,
publish a checked-out branch, or mutate Beads.

The shared integration test and partition manifest intentionally overlap with
later tasks. Touch overlap is not an execution mutex: dependency-ready work
may run concurrently in isolated Git worktrees; only deterministic merge and
publication are serialized.

## Steps

1. Write failing capability, hostile-environment, object-format, attribute,
   and byte-reproduction tests before implementing the constructor.
2. Admit only the pinned Git command/options/object/ref-format matrix and
   reject replacements, grafts, shallow history, unsupported submodules, and
   unprofiled merge behavior.
3. Build the private bare integration environment with the canonical common
   object directory and the exact sanitized environment/configuration from
   R20.
4. Implement the exact merge-tree and unsigned commit-tree recipe, including
   parent order, identities, dates, UTF-8 message bytes, and OID validation.
5. Recheck attributes on every exact input/branch/rebuild tree so a
   worker-added custom driver or attribute drift blocks before construction.
6. Advance the partition manifest to `complete_through:30` with `final:false`
   only after both real Task 30 families are collected and owned exactly.

## Acceptance

- [ ] `python3 -m pytest tests/test_mardi_integration_task_partition.py -q` → the stage-30 manifest exactly and exclusively owns every collected node and each required nonempty Task 28–30 family, while every Task 31–37 marker or entry is absent (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task30 -k git_capability` → only the closed Git/object/ref/attribute capability set is admitted under hostile configuration and environment (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task30 -k deterministic_objects` → merge-tree and commit-tree reproduce exact trees, commit bytes, and OIDs across supported formats and restarts (L2).
