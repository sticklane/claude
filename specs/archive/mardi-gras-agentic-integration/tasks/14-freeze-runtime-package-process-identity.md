# Task 14: freeze runtime, package, and process identity

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: 01
Priority: P0
Budget: 42 turns
Spec: ../SPEC.md (requirements R5, R7, R8, R12, R15, R17)
Touch: agentic/package_identity.py, agentic/runtime_profile.py, agentic/process_identity.py, agentic/cli.py, agentic/schema/package-current-v1.json, agentic/schema/runtime-binary-v1.json, agentic/schema/process-identity-v1.json, tests/fixtures/agentic-process-identities-v1.json, tests/test_agentic_package_identity.py, tests/test_agentic_runtime_profiles.py, tests/test_agentic_process_identity.py, tests/inventory/mardi-gras-14-runtime-identity.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-14-runtime-identity.json

## Goal

Provide the package-current, runtime-profile/fingerprint, and process identity
foundation consumed by launcher, events, activity, packaging, and canaries.
One shared fixture fixes the exact Linux and Darwin process-start/boot
grammars, including omission and malformed boundaries, while package identity
is always the manifest/execution-environment pair.

## Touch

This task owns identity parsing, canonical validation, package-current fixture
verification, runtime capability/profile reads, and the shared process
round-trip fixture. It does not build or install the final self-contained
package, certify live façades, authorize Beads, launch children, write run
events, or implement cohort scheduling. Tasks 15, 16, and 18 consume the
shared fixture without editing it.

## Steps

1. Write failing package, runtime, and cross-platform process-identity tests
   first, using one fixture shared by supervisor, event, and activity callers.
2. Implement exact `agentic.process-start/v1` and `agentic.process-boot/v1`
   parsers/readers for Linux procfs and Darwin proc APIs, with canonical
   positive-decimal bounds, microseconds `0..999999`, lowercase UUIDs,
   wrong-platform rejection, and omission when unavailable.
3. Implement strict runtime-profile capability parsing and canonical
   `agentic.runtime-binary/v1` fingerprint construction from one resolved
   physical executable, bounded parsed version, OS, and architecture.
4. Implement fixture-backed `agentic package current --json` validation of
   the reproducible package-manifest hash plus installed
   execution-environment hash, including installed-runtime, inventory, and
   loader-closure identities; reject either-member or member-byte drift.
5. Register the closed JSON schemas and boundary cases without duplicating
   00D's Beads capability parser or Task 13's writer-capacity ownership.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_process_identity.py -q` → Linux/Darwin start and boot readers round-trip the shared zero/maximum-microsecond fixture, reject malformed/overflow/wrong-platform evidence, and omit unavailable identities (L3).
- [ ] `python3 -m pytest tests/test_agentic_package_identity.py tests/test_agentic_runtime_profiles.py -q` → package current binds both identity hashes and every fixture member, while runtime profile and executable fingerprints reject path/byte/version/OS/architecture or canonical-byte drift (L3).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json` → package/runtime/process schemas, fixtures, and tests are uniquely classified (L2).
- [ ] `bash scripts/check.sh` → the repository gate remains green with the shared identity foundation (L3).
