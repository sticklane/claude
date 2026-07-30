# Task 29: own cohort and recover

<!-- Registration fields are frozen authoring-time inputs; bd owns live task state. -->
<!-- Status is always the initial display value `pending` and is never updated in this file. -->
<!-- Task definitions are immutable after registration. Workers report progress and discoveries through the orchestrator. -->

Status: pending
Depends on: 01, 28
Priority: P0
Budget: 38 turns
Spec: ../SPEC.md (requirement R20)
Touch: agentic/integration/model.py, agentic/integration/ownership.py, tests/test_drain_worktree_integration.py, tests/mardi-integration-task-tests-v1.json

## Goal

Complete cohort ownership after admission with the N/R/C/K commit protocol,
credential custody, exact liveness, resume, and generation-safe takeover.
Every recognized crash state advances one recorded step; every unrecognized
combination fails closed without freeing or duplicating capacity.

## Touch

This task owns credentials and current-owner authority only. It consumes Task
28's Q/A/P and an injected ref-CAS seam; it does not implement deterministic
Git objects, landing journals, group disposition, gates, publication, Beads
closure, or terminal cleanup.

The shared integration test and partition manifest intentionally overlap with
sibling work. Touch overlap is not an execution mutex: dependency-ready work
may run concurrently in isolated Git worktrees; only deterministic merge and
publication are serialized.

## Steps

1. Write the failing credential-ownership state-table tests before production
   code, including every side of N, R, C, K, and rotation boundaries.
2. Implement mode-0600 credential creation and descriptor/stdin-only token
   transfer with no token in argv, environment, public evidence, or logs.
3. Implement exact-live, exact-dead, and unknown decisions and the exhaustive
   Q/A/P/N/R/C/K resume/abort rules without weakening Task 28 capacity.
4. Add the append-only rotation-prepared → next credential → current rename →
   active-owner CAS → rotation-committed protocol, always reading fresh A.
5. Test duplicate adoption, racing takeover, PID reuse/reboot evidence,
   credential mismatch, unknown-liveness token resume, and crashes before the
   first claim.
6. Advance the partition manifest to `complete_through:29` with `final:false`
   only after the real Task 29 family is collected and owned exactly.

## Acceptance

- [ ] `python3 -m pytest tests/test_mardi_integration_task_partition.py -q` → the stage-29 manifest exactly and exclusively owns every collected node and each required nonempty Task 28–29 family, while every Task 30–37 marker or entry is absent (L2).
- [ ] `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task29 -k credential_ownership` → credential custody, Q/A/P/N/R/C/K recovery, fresh-A liveness, and generation-safe takeover pass every recognized and rejected state (L2).
