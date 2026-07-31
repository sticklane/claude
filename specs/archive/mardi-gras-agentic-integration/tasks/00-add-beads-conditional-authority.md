# Bootstrap Task 00B: add conditional Beads authority

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: 00-add-beads-authority-core.md
Priority: P0
Budget: 40 turns
Spec: ../SPEC.md (requirements R17, R21)
Touch: specs/mardi-gras-agentic-integration/upstream/beads-authority-conditional.patch, specs/mardi-gras-agentic-integration/tests/test_beads_authority_conditional.sh

## Goal

Extend the pinned Beads authority core with one stable per-issue authority
revision, actor-bound history, and revision-conditional single- and
multi-issue transactions. Every scheduling-fingerprint-relevant mutation,
including writes made by supported older clients, advances the affected
authority cursor atomically.

## Touch

This task owns only fragment B and its A+B acceptance harness. It consumes the
00A helper unchanged and must not alter the core fragment/tooling, implement
supersession redirects, or add toolkit-side adapters.

## Steps

1. Write failing A+B tests first for single-issue compare-and-swap, complete
   multi-issue atomicity, actor/reason history, ambiguous connections, and
   older-client metadata and incident-edge ABA.
2. Add one storage-backed authority revision/history cursor per issue and
   advance both endpoints for every dependency addition, removal, or retype.
3. Advance the same cursor for every issue field, provider-visible metadata
   field, and other R20 scheduling-fingerprint input regardless of writer
   version.
4. Implement conditional update/close and the closed
   `authority transact --if-revisions` request, rejecting missing endpoints,
   cycles, conflicting operations, unknown fields/types, and any cursor
   mismatch with no partial mutation.
5. Persist ordered actor/reason history in the mutation transaction and prove
   exact all-before/all-after recovery for ambiguous connections.

## Acceptance

- [ ] `bash specs/mardi-gras-agentic-integration/tests/test_beads_authority_conditional.sh` → the 00A helper applies A+B in order and passes cursor monotonicity, conditional single/batch success and conflict, actor-bound history, ambiguity recovery, and older-client metadata/incident-edge ABA tests on both backends (L3).
- [ ] `bash scripts/check.sh` → the toolkit repository gate remains green with the conditional fragment and harness (L3).
