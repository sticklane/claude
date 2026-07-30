# Task 21: add the pinned Mardi Gras provider

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status is always the frozen initial display value `pending`; workers and orchestrators update bd, never this line. -->
<!-- Task definitions are immutable after registration. Workers report progress, decisions, and deferred questions to the orchestrator; they do not rewrite task files. -->

Status: pending
Depends on: 01, 18, 37
Priority: P0
Budget: 44 turns
Spec: ../SPEC.md (requirements R10, R12, R13, R14, R18)
Touch: specs/mardi-gras-agentic-integration/upstream/mardi-gras-agentic-provider.patch, specs/mardi-gras-agentic-integration/trusted-mardi-gras-releases-v1.json, specs/mardi-gras-agentic-integration/tests/test_mardi_gras_provider.sh, specs/mardi-gras-agentic-integration/tests/mardi-gras-checkout.sh, agentic/schema/public-json-surfaces-v1.json, tests/test_mardi_gras_patch.py, tests/test_agentic_public_json_contract.py, tests/inventory/mardi-gras-21-provider.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-21-provider.json

## Goal

Produce the reviewable `agentic` provider patch against exact Mardi Gras
commit `70e36ff5f180073864163e39739324c9fbec989e`. The provider routes every
launch entrypoint through the fixed R14 control protocol and Task 18's bounded
activity projection while preserving alternate-screen, selection, detail,
tmux, and foreground behavior without owning claims, recovery, or prompts.

## Touch

The repository records a reproducible upstream patch, helper, closed trusted
release allowlist, and tests—not a vendored or permanent fork. The patch may
call only the exact R2/R3/R10 argv forms, may store only ephemeral pane
handles, and must disable direct prompt, kill, and recovery controls while the
provider is active. An allowlist entry requires an upstream immutable artifact
and checksum manifest; otherwise the allowlist remains unpopulated rather than
inventing provenance.

## Steps

1. Write failing Go provider tests in a temporary exact-base checkout plus
   hermetic wrong-base, malformed-handshake, and release-provenance fixtures.
2. Add the canonical protocol handshake, one shared issue-launch confirmation,
   distinct confirmed drain action, exact argv-array execution, and routing
   from every legacy `a`, detail, and palette launch entrypoint.
3. Add single-flight sequenced activity polling, last-good per-source
   retention, stale/error rendering, bounded strings, stable selection and
   detail position, pane switching, foreground return, and alternate-screen
   cleanup.
4. Suppress direct prompt construction and provider-owned kill/recovery, then
   generate the checked-in patch against the exact pinned commit.
5. Implement the base-verifying checkout/test helper and the closed trusted
   release allowlist schema, register every new handshake, release, control,
   and error leaf in the shared public-JSON inventory, and leave production
   disabled for every local or self-reported build without exact upstream
   provenance.

## Acceptance

- [ ] `bash specs/mardi-gras-agentic-integration/tests/test_mardi_gras_provider.sh` → the helper verifies the exact base, applies the patch, and passes the Agentic Go suites for handshake/control bytes, launch routing, confirmations, polling, stale data, selection, pane behavior, and terminal cleanup (L3).
- [ ] `python3 -m pytest tests/test_mardi_gras_patch.py -q` → hermetic fixtures prove exact-base and provenance enforcement, wrong-base and patch-only rejection, bounded subprocess errors, and reproducible patch metadata without requiring an upstream release (L2).
- [ ] `python3 -m pytest tests/test_agentic_public_json_contract.py -q` → the Mardi Gras handshake, release allowlist, provider control messages, and error fields satisfy canonical R12 bytes and closed bounds (L2).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json && bash scripts/check.sh` → provider helper surfaces are classified and the toolkit gate passes (L3).

Depth ceiling: this repository can prove the pinned patch and reject
untrusted releases, but cannot cause upstream acceptance or publication; Task
27's manual-pending trusted-binary journey is the behavioral complement.
