# Task 34: publish target safely

<!-- Registration fields are frozen authoring-time inputs; bd owns live task state. -->
<!-- Status is always the initial display value `pending` and is never updated in this file. -->
<!-- Task definitions are immutable after registration. Workers report progress and discoveries through the orchestrator. -->

Status: pending
Depends on: 01, 33
Priority: P0
Budget: 38 turns
Spec: ../SPEC.md (requirement R20)
Touch: agentic/integration/model.py, agentic/integration/gates.py, agentic/integration/publication.py, tests/test_drain_worktree_integration.py, tests/mardi-integration-task-tests-v1.json

## Goal

Publish only a fully gated OID into the one clean checked-out target worktree,
with prepared/committed evidence and exact recovery for every ref/index/tree
combination. A workset or target race must become typed non-closing evidence,
never authorize a stale close or destructive reset.

## Touch

This task owns the post-gate fingerprint barrier, launch-worktree lock and
cleanliness checks, read-tree/target-ref CAS publication, the four recovery
states, and detection of publication drift. It emits closing-eligible or
closing-ineligible intents but leaves target-movement reconciliation, Beads
close, marker cleanup, quarantine execution, and capacity release to later
tasks.

The shared integration test and partition manifest intentionally overlap with
adjacent tasks. Touch overlap is not an execution mutex: dependency-ready
work may run concurrently in isolated Git worktrees; only deterministic merge
and publication are serialized.

## Steps

1. Write failing publication and drift tests first, including every side of
   prepared evidence, read-tree, target CAS, receipt, and current-workset
   barriers.
2. Require the launch worktree to be the sole checkout of the canonical target
   with exact tracked, staged, untracked, ignored, submodule, index, tree, ref,
   and symbolic-HEAD state.
3. Implement prepared evidence, sanitized `read-tree --reset -u`, expected-old
   target CAS, committed receipt, and post-state verification without moving
   the ref before the worktree is ready.
4. Recover only the four exact expected/gated ref and index/worktree
   combinations; block every mixed/dirty/third-OID state without reset.
5. Bind receipt fingerprints/cursors and emit `publish_conflict` or
   `published_contended` terminal intent on target/workset races.
6. Advance the partition manifest to `complete_through:34` with `final:false`
   only after both real Task 34 families are collected and owned exactly.

## Acceptance

- [ ] `python3 -m pytest tests/test_mardi_integration_task_partition.py -q` → the stage-34 manifest exactly and exclusively owns every collected node and each required nonempty Task 28–34 family, while every Task 35–37 marker or entry is absent (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task34 -k target_publication` → checked-out-target publication and all four crash states preserve exact ref/index/worktree authority (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task34 -k publication_drift` → workset, target, dirt, and checkout races fail closed into non-closing evidence without stale tracker authority (L2).
