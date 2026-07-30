# Task 28: seal cohort and admit capacity

<!-- Registration fields are frozen authoring-time inputs; bd owns live task state. -->
<!-- Status is always the initial display value `pending` and is never updated in this file. -->
<!-- Task definitions are immutable after registration. Workers report progress and discoveries through the orchestrator. -->

Status: pending
Depends on: 01, 13, 14
Priority: P0
Budget: 44 turns
Spec: ../SPEC.md (requirement R20)
Touch: agentic/frontier.py, agentic/lock.py, agentic/integration/__init__.py, agentic/integration/model.py, agentic/integration/admission.py, tests/test_agentic_ready.py, tests/test_drain_worktree_integration.py, tests/test_mardi_integration_task_partition.py, tests/mardi-integration-task-tests-v1.json

## Goal

Replace Touch-disjoint greedy admission with R20's dependency-ready,
capacity-bounded cohort seal. Add the sole account-global Q ledger, filtered
runtime/repository limits, immutable prepared membership, and per-target
active pointer without dispatching a worker before committed admission.

## Touch

`agentic.frontier.compute_frontier` is currently a Touch-disjoint greedy
prefix, and `agentic.lock.RepoLock` is the existing repository lock seam; this
task evolves both rather than building a second scheduler or unrelated lock
stack. It creates the shared integration model and admission modules but does
not implement credentials, Git object construction, landing, gates,
publication, closure, or cleanup.

The shared integration test and partition manifest intentionally overlap with
later tasks. Touch overlap is not an execution mutex: dependency-ready work
may run concurrently in isolated Git worktrees; only deterministic merge and
publication are serialized.

## Steps

1. Write the failing Task 28 seal, active-pointer, and cross-runtime capacity
   tests first. Create the staged partition test/manifest with
   `complete_through:28` and `final:false`; assign only the real Task 28 nodes
   to its exact nonempty families and reject every future-task marker or entry.
2. Evolve `compute_frontier` so dependency and decision edges determine the
   ready antichain while file overlap remains eligible for isolated-worktree
   execution. Preserve deterministic priority/creation/spec/ref/ID ordering.
3. Extend the lock seam with the exact account-global → repository → target
   order and implement the one content-addressed global Q event chain,
   including Q-only credential/liveness recovery and filtered runtime and
   repository accounting.
4. Implement cohort sealing through prepared Q, immutable membership/P, and
   the target-keyed A pointer. No claim, worktree, or worker may start before
   the committed-admission seam reports success.
5. Cover same-target, cross-target, cross-repository, and cross-runtime races,
   killed holders on both sides of Q/A, malformed ledgers, capacity zero, and
   Codex's one-writer profile.

## Acceptance

- [ ] `python3 -m pytest tests/test_mardi_integration_task_partition.py -q` → the stage-28 manifest exactly and exclusively owns every collected real Task 28 node, every required Task 28 family is nonempty, and all Task 29–37 markers or entries are absent rather than placeholders (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task28 -k seal_admission` → deterministic ready-antichain sealing never uses Touch overlap as an execution mutex and dispatches nothing before committed admission (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task28 -k active_pointer` → A/P membership and per-target pointer creation, collision, and crash recovery satisfy the closed seal states (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task28 -k capacity_admission` → the sole Q ledger atomically enforces filtered runtime/repository caps across runtimes, repositories, targets, and Q/A crash boundaries (L2).
