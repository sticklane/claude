# Task 02: Document the keyword-gated hex rule

Status: pending
Depends on: 01
Priority: P2
Budget: 4 turns
Spec: ../SPEC.md (requirement R3)
Touch: agentprof/README.md

## Goal

README's "Turn frames: secret scrubbing and naming" section documents the
keyword-gated hex class, its deliberate over-redaction trade-off, and the
residual risk (bare hex pastes with no in-window keyword remain
unredactable by shape — the git-SHA carve-out); the "deliberately not
matched" sentence is updated so SHAs-in-prose stay the documented
carve-out.

## Touch

README.md only. SCHEMA.md needs no change (it does not restate scrub
classes); do NOT touch scrub.go/scrub_test.go (task 01, already landed).

## Steps

1. Match the final rule wording task 01 shipped (read its scrub.go
   comment), including the word-boundary keyword list.
2. State the residual risk and its operational mitigations (rotation,
   paste hygiene, frame denylist) in two or three sentences.

## Acceptance

- [ ] `grep -ci 'keyword-gated' agentprof/README.md` → ≥ 1
- [ ] `sed -n '/secret scrubbing/,/^## /Ip' agentprof/README.md | grep -ci 'hex'` → ≥ 1 (documented in the right section)
- [ ] `bash agentprof/scripts/check.sh` → green
