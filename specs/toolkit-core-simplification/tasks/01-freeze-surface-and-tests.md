# Task 01: freeze the live surface and retained tests

<!-- Task state is canonical in bd. The Status line is frozen display and is not edited by workers. -->

Status: pending
Depends on: none
Priority: P0
Budget: 32 turns
Spec: ../SPEC.md (requirements R1, R2)
Touch: scripts/inventory-core-surface.py, scripts/check.sh, tests/inventory/core.json, tests/test_check_inventory.sh, specs/toolkit-core-simplification/BASELINE.json, specs/toolkit-core-simplification/surface.schema.json, specs/toolkit-core-simplification/surface-inventory/README.md

## Goal

Create the reviewed, machine-checkable inventory that makes later cleanup
safe. The canonical check runner must fail if a retained test disappears or a
new executable test is not classified, while preserving explicit,
reason-carrying quarantines.

## Touch

Do not classify a functioning optional skill as dead merely because it is
rarely invoked. Test inventory is fragment-based under `tests/inventory/`;
post-baseline surface classification is fragment-based under this spec's
`surface-inventory/`. Later tasks can therefore add their own tests and
surfaces without contending on a frozen manifest.

## Steps

1. Write failing fixtures for missing, unclassified, duplicate, hash-drifted,
   and illegally removed surfaces, plus missing/unclassified/quarantined tests.
2. Implement the surface schema, immutable-baseline plus additive-fragment
   checker, then generate and review the real-tree `BASELINE.json`.
3. Replace glob-only check discovery with the fragment inventory while keeping
   timeout, serial-test, and quarantine behavior.

## Acceptance

- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json` → exits 0 on the real tree and its negative fixtures fail for the named R1 cases (L2).
- [ ] `bash tests/test_check_inventory.sh` → proves missing and unclassified tests fail while a reasoned quarantine runs as quarantined (L2).
- [ ] `bash scripts/check.sh` → every retained inventoried test runs exactly once and the canonical check is green (L3).
