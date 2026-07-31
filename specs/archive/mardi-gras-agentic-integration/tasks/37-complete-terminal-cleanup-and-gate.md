# Task 37: complete terminal cleanup and gate

<!-- Registration fields are frozen authoring-time inputs; bd owns live task state. -->
<!-- Status is always the initial display value `pending` and is never updated in this file. -->
<!-- Task definitions are immutable after registration. Workers report progress and discoveries through the orchestrator. -->

Status: pending
Depends on: 01, 36
Priority: P0
Budget: 44 turns
Spec: ../SPEC.md (requirement R20)
Touch: agentic/frontier.py, agentic/ready.py, agentic/cli.py, agentic/integration/__init__.py, agentic/integration/model.py, agentic/integration/cleanup.py, .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, tests/test_agentic_ready.py, tests/test_drain_touch_claims.sh, tests/test_drain_worktree_integration.py, tests/test_mardi_integration_task_partition.py, tests/mardi-integration-task-tests-v1.json

## Goal

Finish every ordinary and closing-ineligible cohort through crash-safe
worktree/ref/marker cleanup, active-pointer transition, and exact Q release.
Wire the programmatic coordinator into drain, add the capacity-bound
quarantine reconciliation escape, consume typed mandatory-scope extensions
through guarded atomic registration, and prove the entire R20 workflow plus
the final exclusive test-ownership table in one unfiltered integration run.

## Touch

This task owns terminal cleanup, non-capacity diagnostic/quarantine pointers,
the guarded `reconcile-quarantine` command, final coordinator/skill wiring,
guarded workset-extension consumption, and the complete integration gate. It
must preserve Beads as task authority and must not mutate registered task
definitions, expand a sealed cohort, invoke this repair's ordinary
create-then-edge `register-spec` path, reintroduce transcript messaging, add a
second scheduler, or restore Touch-disjoint admission.

Several paths overlap earlier implementation and the shared test module.
Touch overlap is not an execution mutex: dependency-ready tasks may run in
isolated Git worktrees even when they edit the same file; deterministic branch
integration and checked-out-target publication are the serialized boundaries.

## Steps

1. Write failing terminal-cleanup tests first for ordinary success,
   all-excluded/gate-inconclusive, reconciliation-blocked,
   published/close-contended, quarantine, and every A/Q release crash
   boundary.
2. Implement idempotent process-stop/dead proof, exact worktree/ref/marker
   cleanup, diagnostic/quarantine pointer transfer, A CAS clear, and release
   of only the matching global-ledger Q under the ordered locks.
3. Add `agentic cohort reconcile-quarantine`: guarded reconciliation Bead,
   one normal capacity permit, dedicated retained-ref worktree, closed
   revalidate/publish/abandon decisions, fresh review/tests/full gate, new
   receipt-bound closure, and terminal pointer/Q recovery.
4. Consume Task 32's `agentic.workset-extension/v1` action only after
   revalidating the canonical authored task bytes/hash, complete issue
   envelope, affected downstream issue/revision, and intended blocking edge.
   Through Task 00D, apply one storage-guarded complete
   create-plus-initial-edge transaction; exact conflict creates nothing, the
   registered definition remains unchanged, and the new issue can enter only
   a later fresh ready wave after this sealed cohort publishes and closes.
5. Wire drain and the CLI to the full Tasks 28–37 coordinator. Preserve
   deterministic dependency-ready ordering while removing
   `compute_frontier`'s old Touch-disjoint execution exclusion; retain
   worktree isolation and short administration locks.
6. Add only the real Task 37 families, advance the partition manifest to
   `complete_through:37` and `final:true`, and require the exact complete,
   exclusive, nonempty Task 28–37/family table with no extra or missing
   collected node.
7. Run every Task 37 family test, then run the unfiltered worktree integration
   module to exercise same-file fan-out, later-wave workset extension, ordered
   landing, publication-before-close, quarantine, and capacity release end to
   end.

## Acceptance

- [ ] `python3 -m pytest tests/test_mardi_integration_task_partition.py -q` → `complete_through:37` and `final:true` require exact equality with the complete Task 28–37/family table: every task and family is nonempty, every collected node has exactly one exact marker and family, and no missing, extra, duplicate, substring-only, or drifting entry exists (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task37 -k workset_extension` → a typed mandatory-scope action verifies its authored path/hash and atomically guarded-creates the complete new issue plus downstream blocking edge, never mutates a registered definition or sealed cohort, and exposes the issue only to a later fresh wave (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task37 -k terminal_cleanup` → every ordinary, blocked, contended, reconciliation, quarantine, worktree/ref/marker, A, and Q terminal boundary is idempotent and capacity-safe (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q` → overlapping-file workers, global admission, ownership, deterministic landing, group/gate isolation, publication, reconciliation, exact close, quarantine, and terminal cleanup pass as one end-to-end workflow (L3).
