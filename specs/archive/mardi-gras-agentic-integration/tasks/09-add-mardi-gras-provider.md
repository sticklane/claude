# Task 09: add the Mardi Gras provider

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: 05
Priority: P0
Budget: 42 turns
Spec: ../SPEC.md (requirements R10, R12, R13, R14, R18)
Touch: specs/mardi-gras-agentic-integration/upstream/mardi-gras-agentic-provider.patch, specs/mardi-gras-agentic-integration/tests/test_mardi_gras_provider.sh, specs/mardi-gras-agentic-integration/tests/mardi-gras-checkout.sh, tests/test_mardi_gras_patch.py, tests/inventory/mardi-gras-09-provider.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-09-provider.json

## Goal

Produce a reviewable upstream Mardi Gras provider patch pinned to the exact
researched revision. The provider routes every launch entrypoint through the
toolkit protocol, renders bounded activity evidence, and preserves Mardi
Gras's alternate-screen, selection, detail, and tmux behavior without owning
claims or recovery.

## Touch

The repository records a patch and reproducible test helper, not a vendored
fork or a fabricated upstream PR/release. Provider code may call only the
documented argv arrays and must not reconstruct prompts from issue prose.

## Steps

1. Write failing Go provider tests in a temporary pinned checkout first.
2. Add the exact protocol handshake, shared issue-launch confirmation, distinct
   confirmed drain action, and suppression of direct prompt/kill/recover paths.
3. Add single-flight sequenced polling, per-source last-good/stale rendering,
   selection preservation, safe strings, and ephemeral pane switching.
4. Generate the checked-in patch against commit
   `70e36ff5f180073864163e39739324c9fbec989e` and add a helper that verifies
   the base before applying it.
5. Add a hermetic root test for patch metadata, wrong-base rejection, and
   bounded helper behavior plus unique inventory fragments. Keep production
   support disabled until an upstream release advertises the handshake.

## Acceptance

- [ ] `bash specs/mardi-gras-agentic-integration/tests/test_mardi_gras_provider.sh` → the helper verifies the exact base, applies the patch, and runs the named Agentic Go suites for handshake, argv, launch routing, polling, stale data, terminal cleanup, and pane behavior (L3).
- [ ] `python3 -m pytest tests/test_mardi_gras_patch.py -q` → hermetic fixtures prove exact-base enforcement, wrong-base rejection, bounded subprocess failures, and patch provenance without network access (L2).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json && bash scripts/check.sh` → the provider helper's canonical contract test is inventoried and the toolkit gate remains green (L3).
  Depth ceiling: this repository can prove a reproducible upstream patch and behavior in the pinned checkout, but cannot prove external PR acceptance or release publication; the behavioral complement is the released-binary certification in Task 12.
