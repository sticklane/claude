# Task 08: implement the cutover receipt

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: 06
Priority: P0
Budget: 26 turns
Spec: ../SPEC.md (requirement R19)
Touch: agentic/cli.py, agentic/cutover.py, agentic/schema/cutover-receipt-v1.json, tests/test_agentic_cutover.py, tests/inventory/mardi-gras-08-cutover.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-08-cutover.json

## Goal

Add explicit cutover certification and read-only status commands around the
installed live surface. A receipt binds a released Mardi Gras build, immutable
package, runtime binaries, full native façade report, and released-provider
terminal report; any missing or stale identity fails closed.

## Touch

This task does not change Workboard or run real proprietary canaries. It
validates caller-supplied report files, records one bounded receipt atomically,
and reads that receipt without mutating or repairing it.

## Steps

1. Write failing absent, malformed, patch-only, stale-build, stale-package,
   stale-runtime, report-substitution, and atomic-write fixtures first.
2. Define the exact `agentic.cutover/v1` schema and platform user-state path.
3. Implement `agentic live --record-cutover` so it re-runs the read-only live
   check, validates both reports, hashes them, and records every required
   identity atomically.
4. Implement `agentic live --cutover-status --json` as a bounded read-only
   comparison against current installed identities.
5. Add unique inventory fragments for the command/schema/test surfaces.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_cutover.py -q` → only exact released-build/package/runtime/façade/terminal evidence records ready; absent, malformed, patch-only, stale, substituted, and interrupted inputs fail closed (L3).
- [ ] `python3 -m pytest tests/test_agentic_cutover.py -q -k 'read_only or bounded or atomic'` → status never writes or repairs state, public fields are bounded, and interrupted record writes cannot create a ready receipt (L3).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json` → cutover command/schema/test surfaces are inventoried (L2).
- [ ] `bash scripts/check.sh` → the repository gate remains green with dormant cutover certification installed (L3).
