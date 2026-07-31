# Task 33: isolate gate failures

<!-- Registration fields are frozen authoring-time inputs; bd owns live task state. -->
<!-- Status is always the initial display value `pending` and is never updated in this file. -->
<!-- Task definitions are immutable after registration. Workers report progress and discoveries through the orchestrator. -->

Status: pending
Depends on: 01, 32
Priority: P0
Budget: 34 turns
Spec: ../SPEC.md (requirement R20)
Touch: agentic/integration/model.py, agentic/integration/groups.py, agentic/integration/gates.py, tests/test_drain_worktree_integration.py, tests/mardi-integration-task-tests-v1.json

## Goal

Run the canonical gate once on the ordinary full candidate and isolate a
functional failure through bounded, deterministic ordered bisection of
indivisible landing groups. Only a final full-gate-confirmed accepted stack
may become publication-eligible.

## Touch

This task owns gate result classification, the one allowed infrastructure
retry, diagnostic candidate rebuilding, ordered isolation, and final
confirmation. It does not publish a target, reconcile target movement, close
Beads, remove markers, or release refs and permits.

The shared integration test and partition manifest intentionally overlap with
adjacent tasks. Touch overlap is not an execution mutex: dependency-ready
work may run concurrently in isolated Git worktrees; only deterministic merge
and publication are serialized.

## Steps

1. Write failing pass, infrastructure-retry, singleton, interaction, budget,
   and final-confirmation tests before the classifier.
2. Gate the complete committed partition once and retry the identical stack
   at most once only for an explicitly classified infrastructure failure.
3. Implement `classify(known_good, candidates)` with deterministic left-then-
   right splitting and later-group attribution for interaction failures.
4. Rebuild diagnostic stacks from immutable branches and original member
   indexes without changing the original failed-stack ref or target.
5. Enforce the `2g+2` invocation budget, atomic group blocking, and final full
   canonical gate before producing `gated_oid`; preserve evidence on
   inconclusive failure.
6. Advance the partition manifest to `complete_through:33` with `final:false`
   only after the real Task 33 family is collected and owned exactly.

## Acceptance

- [ ] `python3 -m pytest tests/test_mardi_integration_task_partition.py -q` → the stage-33 manifest exactly and exclusively owns every collected node and each required nonempty Task 28–33 family, while every Task 34–37 marker or entry is absent (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task33 -k gate_isolation` → normal pass, bounded retry, ordered isolation, interaction attribution, budget exhaustion, and final confirmation obey the exact group partition (L2).
