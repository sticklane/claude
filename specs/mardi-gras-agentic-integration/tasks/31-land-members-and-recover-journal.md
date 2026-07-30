# Task 31: land members and recover journal

<!-- Registration fields are frozen authoring-time inputs; bd owns live task state. -->
<!-- Status is always the initial display value `pending` and is never updated in this file. -->
<!-- Task definitions are immutable after registration. Workers report progress and discoveries through the orchestrator. -->

Status: pending
Depends on: 01, 30
Priority: P0
Budget: 36 turns
Spec: ../SPEC.md (requirement R20)
Touch: agentic/integration/model.py, agentic/integration/git_objects.py, agentic/integration/landing.py, tests/test_drain_worktree_integration.py, tests/mardi-integration-task-tests-v1.json

## Goal

Land verified member branches in sealed order through prepared/committed
journal records and compare-and-swap advancement of the cohort main ref.
Recovery must reconstruct pruned unreferenced objects deterministically and
must never accept a third ref OID or mismatched reproduction.

## Touch

This task owns ordinary member landing, journal records, main-ref CAS, and
prune-safe recovery. It does not decide conflict resolutions or landing-group
composition, classify gate failures, publish the target, close Beads, or
release cohort capacity.

The shared integration test and partition manifest intentionally overlap with
adjacent tasks. Touch overlap is not an execution mutex: dependency-ready
work may run concurrently in isolated Git worktrees; only deterministic merge
and publication are serialized.

## Steps

1. Write failing prepared/CAS/committed crash tests and aggressive-prune
   recovery tests before implementing the journal.
2. Record immutable branch, input, tree, and output OIDs before advancing the
   exact cohort main ref with expected-old compare-and-swap.
3. Recover input-ref, output-ref, and third-ref states exactly; append a
   missing commit record only after validating the complete prepared record.
4. Re-run Task 30's exact constructor when a prepared tree or commit was
   pruned, and require byte-for-byte OID reproduction before retrying CAS.
5. Keep diagnostic landing as a typed seam for later gate isolation without
   moving the original failed-stack or publication refs.
6. Advance the partition manifest to `complete_through:31` with `final:false`
   only after both real Task 31 families are collected and owned exactly.

## Acceptance

- [ ] `python3 -m pytest tests/test_mardi_integration_task_partition.py -q` → the stage-31 manifest exactly and exclusively owns every collected node and each required nonempty Task 28–31 family, while every Task 32–37 marker or entry is absent (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task31 -k landing_journal` → sealed-order prepared/CAS/committed landing is idempotent and rejects every third-OID or mismatched-journal state (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task31 -k prune_reconstruction` → pruned prepared and diagnostic objects are deterministically reconstructed before ref recovery (L2).
