# Bootstrap Task 00C: add supersession authority

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: 00-add-beads-conditional-authority.md
Priority: P0
Budget: 36 turns
Spec: ../SPEC.md (requirements R17, R21)
Touch: specs/mardi-gras-agentic-integration/upstream/beads-authority-supersession.patch, specs/mardi-gras-agentic-integration/tests/test_beads_authority_supersession.sh

## Goal

Complete the pinned Beads storage provider with transactional supersession and
durable redirect behavior on 00B's authority substrate. Existing consumers
move atomically, later older-client attempts can never create an old-only
blocking edge, and every redirect or supersession change advances ordered
authority history.

## Touch

This task owns only fragment C and its A+B+C supersession harness. It consumes
the 00A helper and earlier fragments unchanged and must not edit patch tooling
or implement the toolkit authorizer, schema-install client, or migration
driver.

## Steps

1. Write failing redirect/history and barrier-controlled older-client race
   fixtures first for embedded and server backends.
2. Implement revision-conditional supersession that enumerates current live
   dependents, adds replacement blockers, converts old blockers to historical
   relations, and installs the redirect in one transaction.
3. Make supersession and redirected dependency mutations advance the stable
   authority cursor and append actor-bound history for every affected
   endpoint.
4. Enforce the closed future behavior for older clients: atomically redirect
   to the replacement plus old historical relation, or reject with typed
   `superseded_target`, never retain an old-only blocker.
5. Prove before/during/after races, rollback, ambiguity recovery, and exact
   A/B/C fragment ordering through the shared helper.

## Acceptance

- [ ] `bash specs/mardi-gras-agentic-integration/tests/test_beads_authority_supersession.sh` → the 00A helper applies A+B+C in order and passes redirect cursor/history, current-dependent movement, older-client future redirect/rejection, and before/during/after race tests on both backends (L3).
- [ ] `bash scripts/check.sh` → the toolkit repository gate remains green with the supersession fragment and harness (L3).
