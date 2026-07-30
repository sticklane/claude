# Bootstrap Task 00D: install the toolkit Beads authorizer

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: 00-add-beads-supersession-authority.md
Priority: P0
Budget: 48 turns
Spec: ../SPEC.md (requirements R1, R9, R17, R21)
Touch: agentic/authority.py, agentic/bd.py, agentic/cli.py, agentic/schema/bd-authority-v1.json, agentic/schema/bd-authority-transaction-v1.json, specs/mardi-gras-agentic-integration/trusted-beads-releases-v1.json, specs/mardi-gras-agentic-integration/migrate-registration.py, specs/mardi-gras-agentic-integration/tests/test_beads_authority_provider.sh, tests/test_agentic_bd_authority.py, tests/test_mardi_gras_registration_migration.py, tests/inventory/mardi-gras-00d-beads-authority.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-00d-beads-authority.json

## Goal

Install the toolkit's sole Beads capability parser, fresh per-operation
authorizer, conditional mutation adapter, and explicit production schema
installer. All claim, migration, requeue, recovery, live-check, and cohort
callers can consume one ticket that binds the actual repository to one
fingerprinted executable and the three behavior-certified authority profiles.

## Touch

This task changes no Beads storage code, patch fragment, or fragment helper.
It consumes the final A+B+C provider evidence and owns toolkit-side
authorization, no-migrate/core/full install clients, conditional
single/batch adapters, their public schemas, and their tests. It also owns
completion of the real-provider integration boundary already reserved in the
registration-migration driver and tests: exact inspection, planning,
per-primitive mutation receipts, recovery snapshots, and terminal-bootstrap
receipt consumption. It does not own the migration graph, supersession, or
Task 01 release semantics and must not change Task 01's claim grammar or lock
behavior.

## Steps

1. Write failing toolkit tests first for physical executable binding,
   actual-repository no-migrate context, all three closed profiles, unknown
   ownership capabilities, opaque IDs, binary swaps, and ambiguous outcomes.
2. Make the provider harness apply A+B+C to the exact pinned commit, exercise
   the complete R17 matrix on embedded and server backends, run the separate
   Go build/vet/race/lint/tidy-diff gate, and emit bounded binary,
   schema/fragment digest, and receipt evidence. Use that exact binary to
   complete the `provider_integration` migration fixtures with real
   embedded/server repositories, raw-client barriers, host contention, and
   crash injection after every provider primitive; the pre-00A fake-adapter
   tests are not certification.
3. Implement the shared authorizer ticket: resolve and fingerprint one
   physical `bd`, bind repository/project/database/backend/schema identity,
   certify permanent no-lease claim, conditional mutation, and supersession
   profiles, and require the same executable before and after every call.
4. Implement canonical conditional single/batch request construction,
   actor/reason history verification, and exact all-before/all-after ambiguous
   recovery without treating a digest or self-reported version as sufficient.
5. Complete the driver's closed real-provider protocol for `inspect_phase`,
   `inspect_primitive`, `plan_primitive`, and `apply_primitive`. Every
   primitive must have durable prepared/committed evidence plus a final phase
   commit, and every inspection/receipt must bind the complete issue, edge,
   revision, history, scoped-ready, and storage-transaction domain needed to
   distinguish exact before, exact after, and drift.
6. Require the canonical mode-0600 R8 terminal-bootstrap receipt through
   `--bootstrap-receipt`, validate its bytes/hash, intent, exact 00A–00D IDs,
   event head, provider executable/full authority identity, and earlier
   bootstrap source and attestation commits, require its path to be exactly the
   canonical R8 bootstrap `receipts/<content-sha256>.json` path, reject even a
   byte-identical owned copy elsewhere, and bind it into
   `bootstrap_verified`. That phase must freshly prove the receipt's exact four
   issue IDs are closed with their canonical refs, serial dependencies,
   container relations, revisions, actor-bound terminal history, and provider
   receipts; a zero-primitive provider `complete:true` claim is not proof.
   Keep the earlier commit identities distinct from the final migration source
   and reviewed-child commits.
7. Add `agentic bd-authority install --repo <physical-repo> --confirmed
   --json` as the only production full-schema installation path, with R8 and
   backend locks, exact confirmation identity, receipt verification, and no
   incompatible-data repair.
8. Register the bounded public envelopes and trusted-release schema while
   keeping an unlisted or self-reported binary unauthorized.

## Acceptance

- [ ] `bash specs/mardi-gras-agentic-integration/tests/test_beads_authority_provider.sh` → A+B+C pass the complete R17 embedded/server and older-client matrix, the full upstream Go gate, run the non-skipped `MARDI_AUTHORITY_BINARY=<exact> python3 -m pytest tests/test_mardi_gras_registration_migration.py -q -k provider_integration` suite, and prove every per-primitive crash/recovery boundary, copied/out-of-R8 terminal-receipt rejection, fresh exact 00A–00D terminal-state proof instead of provider-flag trust, closed snapshot/storage-receipt validation, and distinct bootstrap/final commit binding before emitting the pinned binary/digest/schema/receipt bundle consumed by this adapter and migration (L3).
- [ ] `python3 -m pytest tests/test_agentic_bd_authority.py -q` → fresh repository-bound authorization, all three profiles, conditional single/batch recovery, explicit install, opaque-ID handling, binary drift, and fail-closed unknown/lease behavior pass without an implicit migration (L3).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json` → the authorizer, command, schemas, and tests are uniquely classified without changing retained surfaces (L2).
- [ ] `bash scripts/check.sh` → the toolkit repository gate remains green with the shared authorizer installed (L3).
