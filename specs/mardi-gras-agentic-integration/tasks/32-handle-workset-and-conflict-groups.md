# Task 32: handle workset and conflict groups

<!-- Registration fields are frozen authoring-time inputs; bd owns live task state. -->
<!-- Status is always the initial display value `pending` and is never updated in this file. -->
<!-- Task definitions are immutable after registration. Workers report progress and discoveries through the orchestrator. -->

Status: pending
Depends on: 01, 31
Priority: P0
Budget: 42 turns
Spec: ../SPEC.md (requirement R20)
Touch: agentic/integration/model.py, agentic/integration/landing.py, agentic/integration/groups.py, agentic/integration/workset.py, tests/test_drain_worktree_integration.py, tests/mardi-integration-task-tests-v1.json

## Goal

Keep the sealed cohort safe while the live Beads workset changes, and make
conflict reconciliation produce an ordered, exact partition of indivisible
landing groups. Multi-member exclusion must be one conditional tracker
transaction with a recoverable prepared/committed group-disposition record.
Mandatory scope discovered beyond a registered definition becomes a typed
new-dependent-definition action for a later wave, never an in-place amendment.

## Touch

This task owns scheduling fingerprints, pre-publication rescheduling,
typed workset-extension action construction, conflict-worktree results, group
transitions, and final member dispositions. It does not mutate a registered
task definition, create the new Bead, expand sealed membership, implement
canonical gate execution, publish the target, reconcile target movement,
close Beads, or release capacity. Task 37 consumes the action through Task
00D's guarded complete create-plus-initial-edge transaction.

The shared integration test and partition manifest intentionally overlap with
adjacent tasks. Touch overlap is not an execution mutex: dependency-ready
work may run concurrently in isolated Git worktrees; only deterministic merge
and publication are serialized.

## Steps

1. Write failing workset-change and conflict-group tests first, including
   changes before claim, after landing, during integration, in composite
   groups, and mandatory new scope discovered for an affected downstream
   issue.
2. Compute the R20 scheduling fingerprint and compare it at each owned
   pre-publication barrier without treating registered definition count as a
   frozen workset.
3. Emit canonical `agentic.workset-extension/v1` only from an explicit
   critique, discovery, or human mandatory-scope decision. Bind the new
   canonical authored task path and definition hash, complete issue envelope,
   affected downstream issue/revision, and intended blocking edge; leave the
   registered definition and sealed cohort byte-for-byte unchanged.
4. Implement the prepared/conditional-batch/committed group-disposition
   protocol so partial member mutation is impossible and recovery sees only
   all-before or all-after state.
5. Implement designated conflict-worktree reconciliation with independent
   review/affected tests and atomic replacement of every embedded prefix
   group; never auto-select ours or theirs.
6. Enforce the closed landed, blocked, deferred, rescheduled, skipped, and
   contended dispositions and prove the current committed groups always
   exactly partition landed members.
7. Advance the partition manifest to `complete_through:32` with `final:false`
   only after both real Task 32 families are collected and owned exactly.

## Acceptance

- [ ] `python3 -m pytest tests/test_mardi_integration_task_partition.py -q` → the stage-32 manifest exactly and exclusively owns every collected node and each required nonempty Task 28–32 family, while every Task 33–37 marker or entry is absent (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task32 -k workset_change` → live field/dependency/acceptance changes reschedule owned work, and mandatory new scope emits the exact guarded new-dependent-definition action without mutating a registered definition, expanding the sealed cohort, or publishing stale output (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task32 -k conflict_group` → conflict reconciliation preserves one ordered exact group partition and makes reconciled prefixes indivisible (L2).
