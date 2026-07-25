# Task 07: validate the native-orchestration contract

<!-- Task state is canonical in bd. The Status line is frozen display and is not edited by workers. -->

Status: pending
Depends on: 05
Priority: P1
Budget: 36 turns
Spec: ../SPEC.md (requirement R7)
Touch: agentic/conformance.py, agentic/schema/orchestration-trace.json, tests/test_native_orchestration_contract.py, tests/inventory/07-native-contract.json, specs/toolkit-core-simplification/surface-inventory/07-native-contract.json

## Goal

Define a normalized trace and hermetic validator for Claude, Codex, and
Antigravity native orchestration. The implementation validates state and
safety boundaries but contains no worker launcher, queue scheduler, retry
controller, merger, or model router.

## Touch

Fake runtime callbacks live only in tests. Production code accepts completed
events/traces and reports contract violations.

## Steps

1. Write failing happy and negative trace fixtures for all three runtimes,
   including claim, screening, runtime-appropriate isolation, verdict,
   verifier/critic barrier, exactly one gate, merge/close, and cleanup.
2. Implement the trace schema and state-machine validator.
3. Add a structural/behavioral guard that fails if production conformance code
   gains dispatch or scheduling authority.

## Acceptance

- [ ] `python3 -m pytest tests/test_native_orchestration_contract.py -q` → all runtime happy paths pass and every named R7 negative trace fails at the exact transition (L2).
  Depth ceiling: fake callbacks deliberately avoid launching native agent managers, which is outside the validator's authority — behavioral complement is the manual-pending three-runtime drain journey named in Task 08.
- [ ] `python3 -m json.tool agentic/schema/orchestration-trace.json >/dev/null` → schema parses, complemented by the L3 state-machine fixtures.
- [ ] `bash scripts/check.sh` → conformance validation integrates without changing native execution (L2).
