# Task 20: implement the production cutover receipt

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status is always the frozen initial display value `pending`; workers and orchestrators update bd, never this line. -->
<!-- Task definitions are immutable after registration. Workers report progress, decisions, and deferred questions to the orchestrator; they do not rewrite task files. -->

Status: pending
Depends on: 01, 39, 37
Priority: P0
Budget: 30 turns
Spec: ../SPEC.md (requirements R8, R12, R19)
Touch: agentic/cli.py, agentic/cutover.py, agentic/schema/cutover-receipt-v1.json, agentic/schema/production-cutover-evidence-v1.json, agentic/schema/public-json-surfaces-v1.json, specs/mardi-gras-agentic-integration/tests/validate-manual-certification.py, tests/test_agentic_cutover.py, tests/test_agentic_manual_certification.py, tests/test_agentic_public_json_contract.py, tests/inventory/mardi-gras-20-cutover.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-20-cutover.json

## Goal

Add the sole mutating production certification command and its read-only
status companion. The canonical R8 receipt binds exact trusted Beads and
Mardi Gras releases, the verified R7 package identity pair, runtime
fingerprints, complete native façade evidence, terminal parity, and the
repository fixture revision; any stale or substituted identity fails closed.

## Touch

This task owns cutover receipt/status validation and storage plus the shared
production-evidence schema and revision-aware manual-certification validator
used by Tasks 26 and 27. It must not change Workboard, run proprietary
canaries, install authority schemas, accept a patch-only provider, repair
malformed state, or weaken Task 19's package verification or Task 39's
live/runtime verification.

## Steps

1. Write failing absent, malformed, patch-only, stale-build, stale-Beads,
   stale-package, stale-runtime, report-substitution, noncanonical-JSON, and
   interrupted-write fixtures first.
2. Define the closed `agentic.cutover/v1` schema and canonical mode-0600
   atomic record below R8's environment-independent state root, plus the
   bounded `agentic.production-cutover-evidence/v1` schema Task 27 will use
   for its final command verdicts and receipt identities.
3. Implement `agentic live --record-cutover` to rerun the complete read-only
   live check, rehash both provider binaries and the package identity pair,
   re-resolve every runtime fingerprint, validate both reports against those
   identities, and atomically record the receipt.
4. Implement `agentic live --cutover-status --json` as a bounded read-only
   comparison that never appends, repairs, migrates, or caches authority.
5. Add a revision-aware manual-certification validator for Tasks 26 and 27.
   It compares one evidence commit with its parent; permits only the named
   report/evidence files plus deletion of that task's exact attested HUMAN
   line; reconstructs the child HUMAN bytes by removing that exact parent
   line so every other byte is proven unchanged; and rejects a missing,
   altered, duplicate, out-of-section, or separately committed deletion.
   Task 27 validation additionally requires the closed production-evidence
   object to bind and match fresh cutover-status identities plus SHA-256 over
   the exact façade report, terminal report, and cutover receipt bytes.
6. Register every receipt, status, certification-evidence leaf, validator
   error, and new test/helper surface in the public JSON and measured-surface
   inventories.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_cutover.py -q` → only exact trusted-release, package, runtime, façade, terminal, and fixture identities record and remain ready; every missing, stale, substituted, patch-only, and interrupted case fails closed (L3).
- [ ] `python3 -m pytest tests/test_agentic_cutover.py -q -k 'read_only or canonical or bounded or atomic or fingerprint'` → status performs no write or repair, receipt bytes and fields are bounded and canonical, and atomic crash recovery never fabricates readiness (L3).
- [ ] `python3 -m pytest tests/test_agentic_manual_certification.py -q` → exact-parent fixtures prove Tasks 26/27 may change only their named evidence files and delete only their attested HUMAN line in the same commit; altered or collateral HUMAN bytes, split commits, minimal forged evidence, report substitution, stale status, and any identity/hash mismatch fail closed (L3).
- [ ] `python3 -m pytest tests/test_agentic_public_json_contract.py -q` → cutover record, status, production evidence, trusted identities, runtime fingerprints, and every failure envelope are in the closed public JSON contract (L2).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json && bash scripts/check.sh` → cutover surfaces are classified and the full toolkit gate passes (L3).
