# Task 36: close authority and clean markers

<!-- Registration fields are frozen authoring-time inputs; bd owns live task state. -->
<!-- Status is always the initial display value `pending` and is never updated in this file. -->
<!-- Task definitions are immutable after registration. Workers report progress and discoveries through the orchestrator. -->

Status: pending
Depends on: 01, 35
Priority: P0
Budget: 34 turns
Spec: ../SPEC.md (requirement R20)
Touch: agentic/integration/model.py, agentic/integration/reconciliation.py, agentic/integration/closure.py, tests/test_drain_worktree_integration.py, tests/mardi-integration-task-tests-v1.json

## Goal

Close only members named by a closing-eligible publication receipt, using
their exact receipt-bound authority revisions and post-close actor/history
proof. Remove each successful member's markers only after proof, and turn any
foreign event, ABA, owner change, or ambiguous mismatch into durable
publication contention.

## Touch

This task owns total-order conditional close, exact post-close recovery, the
per-member close ledger, and marker cleanup after proven close. It does not
delete integration refs/worktrees, clear A, release Q, execute quarantine
reconciliation, or run the final full integration gate.

The shared integration test and partition manifest intentionally overlap with
adjacent tasks. Touch overlap is not an execution mutex: dependency-ready
work may run concurrently in isolated Git worktrees; only deterministic merge
and publication are serialized.

## Steps

1. Write failing authority-close and marker-cleanup tests first, including
   raw older-client field, metadata, dependency, supersession, and ABA races.
2. Re-read show/history before each close and require assignee/run,
   fingerprint, and authority revision to equal the publication receipt; never
   adopt a newer cursor.
3. Invoke only the revision-conditional close with the cohort actor and
   receipt reason, then require the exact next cursor and unique actor-bound
   history suffix.
4. Recover ambiguous connections or already-closed issues only from the same
   receipt-bound transition; every mismatch emits `published_contended` and
   stops later closes.
5. Remove claim/inflight markers individually only after authoritative close
   proof and retain the contended member's authoritative markers for terminal
   quarantine handling.
6. Advance the partition manifest to `complete_through:36` with `final:false`
   only after both real Task 36 families are collected and owned exactly.

## Acceptance

- [ ] `python3 -m pytest tests/test_mardi_integration_task_partition.py -q` → the stage-36 manifest exactly and exclusively owns every collected node and each required nonempty Task 28–36 family, while every Task 37 marker or entry is absent (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task36 -k authority_close` → only receipt-equal authority closes, while cursor movement, ABA, owner changes, and ambiguous outcomes preserve external authority (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task36 -k marker_cleanup` → markers are removed only after exact close proof and remain recoverable on every crash or contention boundary (L2).
