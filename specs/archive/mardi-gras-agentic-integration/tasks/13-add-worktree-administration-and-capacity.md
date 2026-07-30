# Task 13: add worktree administration and capacity primitives

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: 01
Priority: P0
Budget: 36 turns
Spec: ../SPEC.md (requirements R8, R12, R20)
Touch: agentic/worktree_admin.py, agentic/capacity.py, agentic/lock.py, runtimes/README.md, runtimes/claude-code.md, runtimes/codex.md, runtimes/antigravity.md, runtimes/gemini-cli.md, tests/test_agentic_worktree_administration.py, tests/test_agentic_capacity_profiles.py, tests/inventory/mardi-gras-13-worktree-capacity.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-13-worktree-capacity.json

## Goal

Add the narrow canonical-repository worktree-administration critical section
and the declared runtime-capacity primitives required by later cohort
admission. Every shipped runtime profile exposes one validated writer cap,
Codex remains capped at one, and account-global/repository filtered-cap
calculations share one R8-root lock identity without serializing work inside
existing worktrees.

## Touch

This task owns only `git worktree add|lock|unlock|remove|repair|prune`
serialization, capacity declarations/parsing, the account-global capacity
root/lock primitive, and pure bounded-cap calculations. It must not implement
the Q event ledger, cohort A/P/N/R/C/K protocol, worker dispatch, landing,
publication, or cleanup policy owned by Tasks 28–37. Worktree execution,
review, tests, and edits must never take the administration lock.

## Steps

1. Write failing multi-process administration tests first, proving that
   shared Git administration serializes while commands in already-created
   worktrees continue concurrently.
2. Add one closed positive `1..5` native-writer-capacity declaration to every
   shipped runtime profile and a strict parser; pin Codex to `1` and reject
   absent, duplicate, noncanonical, zero, or over-five values.
3. Implement canonical common-repository identity and the short worktree
   administration lock around only the six allowed operations plus
   unavoidable shared Git-configuration mutation.
4. Add the environment-independent R8 global-capacity directory/lock identity,
   lock-order helpers, and pure filtered calculations for native slots,
   runtime-profile reservations, and the repository hard cap of five.
5. Reject repair/prune while a live cohort owns any worktree and require
   exact physical path, branch, HEAD, owner generation, and exact-dead proof
   before bounded cleanup entry.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_worktree_administration.py -q` → concurrent add/lock/remove/repair/prune operations serialize by canonical repository, live-cohort repair is refused, and existing-worktree execution does not acquire the administration lock (L3).
- [ ] `python3 -m pytest tests/test_agentic_capacity_profiles.py -q` → every shipped profile has one canonical `1..5` declaration, Codex is exactly one, global/repository filtered-cap math is bounded, and environment overrides cannot change the global lock identity (L3).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json` → worktree/capacity primitives, runtime declarations, and tests are uniquely classified (L2).
- [ ] `bash scripts/check.sh` → the repository gate remains green with the new primitives and profile declarations (L3).
