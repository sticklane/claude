# Bootstrap Task 00A: add the Beads authority core

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: none
Priority: P0
Budget: 48 turns
Spec: ../SPEC.md (requirements R17, R21)
Touch: specs/mardi-gras-agentic-integration/upstream/beads-authority-core.patch, specs/mardi-gras-agentic-integration/tests/beads-authority-provider-helper.sh, specs/mardi-gras-agentic-integration/tests/test_beads_authority_core.sh

## Goal

Provide the first reproducible Beads v1.1.0 authority fragment and the shared
bootstrap helper needed by every later authority task. With only this fragment
applied, the pinned Beads checkout supports no-migrate identity, transactional
core installation, storage-enforced external-reference uniqueness, and
guarded bootstrap creation plus the narrow one-shot 00A finalize needed to
finish the bootstrap without advertising the general conditional or
supersession profiles.

## Touch

This task owns the shared fragment apply/build helper, the core patch, and the
core-only acceptance harness. It must not implement authority revisions,
conditional mutations, supersession redirects, toolkit-side authorization, or
edit the later fragment/test files. The helper may apply later fragments by
explicit caller request, but their bytes remain owned by 00B and 00C.

## Steps

1. Write the failing core-only pinned-checkout fixtures first, including
   embedded and server backends, raw-client races, and crashes on both sides
   of schema-install commit.
2. Build a deterministic helper that verifies exact Beads commit
   `8e4e59d39f3459a43cf21a3236a13eca4dd874f7`, applies requested fragments
   only in A/B/C order, runs named gates, and emits bounded
   content-addressed binary/fragment/schema evidence.
3. Add `authority identity --no-migrate --json` with no initialization,
   migration, upgrade, or history side effect, plus the base/core/full
   handshake framework.
4. Add backend-serialized `authority install --profile core|full` transaction
   plumbing and exact receipt/recovery behavior; the A-only executable may
   install and advertise only the core profile.
5. Enforce uniqueness for every nonempty external ref in storage, guarded
   complete issue-plus-initial-edge creation, guarded external-ref update, and
   an expected-state one-shot transaction limited to closing, canonicalizing,
   and attaching the no-ref 00A issue against both patched and older raw
   clients.
6. Prove embedded OS-lock plus transaction serialization and server advisory
   serialization, including incompatible-data rollback and different-host
   rejection for one migration identity.

## Acceptance

- [ ] `bash specs/mardi-gras-agentic-integration/tests/test_beads_authority_core.sh` → an exact pinned checkout with only fragment A passes no-migrate identity, core install/recovery, uniqueness, guarded create/ref update, exact 00A finalize and losing-race rejection, embedded/server serialization, raw-client barriers, and core-only handshake tests (L3).
- [ ] `bash scripts/check.sh` → the toolkit repository gate remains green with the checked-in core fragment and helper (L3).
