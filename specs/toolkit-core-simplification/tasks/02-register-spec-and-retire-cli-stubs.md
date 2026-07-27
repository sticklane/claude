# Task 02: make task registration create-only and retire CLI stubs

<!-- Task state is canonical in bd. The Status line is frozen display and is not edited by workers. -->

Status: pending
Depends on: 01
Priority: P0
Budget: 36 turns
Spec: ../SPEC.md (requirements R3, R4)
Touch: agentic/cli.py, agentic/register.py, agentic/shadow.py, tests/test_agentic_shadow.py, tests/test_agentic_register.py, tests/test_agentic_cli_retirement.py, tests/inventory/02-register-cli.json, specs/toolkit-core-simplification/surface-inventory/02-register-cli.json, .claude/skills/breakdown/SKILL.md

## Goal

Replace ongoing markdown-to-bd mutation with crash-recovering, create-only task
registration. Remove the five retired commands from discovery while keeping
their exact non-mutating compatibility diagnostics until `agentic` 2.0.

## Touch

This task owns the breakdown caller update. Do not sweep other skills or
runtime profiles; Tasks 03 and 04 own those disjoint surfaces.

## Steps

1. Write failing tests for canonical hashes, ignored Status, exact dependency
   direction, interrupted phase-two recovery, same-hash idempotence,
   conflicting hashes/edges, and forbidden existing-state mutation.
2. Implement `agentic register-spec <spec-dir>` using the existing repo lock
   and the two phases in R3.
3. Hide `compose`, `inbox`, `demote`, and `shadow-sync` from discovery;
   retain exact-name exit-2 aliases with the exact R4 messages.
4. Replace the old `test_agentic_shadow.py` mutation assertions with the new
   register/retirement behavior and classify the superseded test surface in
   this task's inventory fragments.
5. Change breakdown to call `register-spec`, treat task headers as frozen
   display, and never recommend shadow-sync.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_register.py -q` → passes the real two-phase happy path and every named recovery/conflict fixture (L3).
- [ ] `python3 -m pytest tests/test_agentic_cli_retirement.py -q` → proves hidden help/completion plus all five exact exit-2 diagnostics and zero shadow mutation (L2).
- [ ] `bash scripts/check.sh` → the updated inventoried suite is green (L3).
