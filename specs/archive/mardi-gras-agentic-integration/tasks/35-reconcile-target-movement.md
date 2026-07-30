# Task 35: reconcile target movement

<!-- Registration fields are frozen authoring-time inputs; bd owns live task state. -->
<!-- Status is always the initial display value `pending` and is never updated in this file. -->
<!-- Task definitions are immutable after registration. Workers report progress and discoveries through the orchestrator. -->

Status: pending
Depends on: 01, 34
Priority: P0
Budget: 36 turns
Spec: ../SPEC.md (requirement R20)
Touch: agentic/integration/model.py, agentic/integration/publication.py, agentic/integration/reconciliation.py, tests/test_drain_worktree_integration.py, tests/mardi-integration-task-tests-v1.json

## Goal

Reconcile one concurrent target movement without minting a successor cohort,
owner, claim, or unbounded generation. The same cohort must deterministically
merge, review, test, gate, and republish generation 1 or emit exact
closing-ineligible evidence.

## Touch

This task owns generation-1 target reconciliation, its exact ref/object
recipe, target-movement recovery, and the typed terminal intent for conflict,
second movement, dirt, or reproduction mismatch. It does not conditionally
close Beads, clean final markers/refs/worktrees, clear A, release Q, or expose
the quarantine command.

The shared integration test and partition manifest intentionally overlap with
adjacent tasks. Touch overlap is not an execution mutex: dependency-ready
work may run concurrently in isolated Git worktrees; only deterministic merge
and publication are serialized.

## Steps

1. Write failing clean-reconciliation, merge-conflict, second-movement,
   dirty-target, prune, and crash tests before implementation.
2. Create only `refs/agentic/integration/<cohort>/reconcile/1/head`, seeded at
   the moved target, under fresh A/current-credential authority.
3. Implement the exact aggregate merge-tree/commit-tree identities, parents,
   date, message, prepared record, ref CAS, and prune reconstruction.
4. Repeat independent diff review, affected tests, canonical gate, workset
   barriers, and checked-out-target-aware publication before producing a new
   closing-eligible receipt linked to generation 0.
5. Convert conflict, second movement/generation, dirt, and reproduction
   mismatch into one closing-ineligible reconciliation intent for Task 37,
   without closing a member or retaining writer capacity indefinitely.
6. Advance the partition manifest to `complete_through:35` with `final:false`
   only after the real Task 35 family is collected and owned exactly.

## Acceptance

- [ ] `python3 -m pytest tests/test_mardi_integration_task_partition.py -q` → the stage-35 manifest exactly and exclusively owns every collected node and each required nonempty Task 28–35 family, while every Task 36–37 marker or entry is absent (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task35 -k target_reconciliation` → clean generation-1 reconciliation is deterministic and every conflict, second movement, dirt, prune, and crash boundary fails to the exact non-closing state (L2).
