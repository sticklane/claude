# Task 03: retire the map --limit waiver after ctx-cujs/02 lands

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: blocked
Unblock: run: grep -q '^Status: done' specs/ctx-cujs/tasks/02-skill-link-and-typo-fix.md || echo "not done: specs/ctx-cujs/tasks/02 (owns the map --limit fix; retiring the waiver first reds the conformance test)"
Depends on: 01
Priority: P3
Budget: 4 turns
Spec: ../SPEC.md (requirement R1, waiver retirement)
Touch: context-tree/tests/doc_conformance.rs

## Goal

The seeded `map --limit` waiver entry is deleted from the conformance
test once specs/ctx-cujs/tasks/02 has fixed the doc rows to
`map [--tokens N]` — leaving the waiver list empty and the gate fully
strict. This spec owns the deletion because cujs/02's Touch has no grant
to the test file. NOTHING auto-flips this task: a human or later session
re-runs the Unblock check and flips to pending once cujs/02 is done.

## Steps

1. Verify cujs/02 is `Status: done` (the Unblock command) and that both
   skill files now read `map [--tokens N]`.
2. Delete the seeded waiver entry.
3. Run the conformance test — premature execution self-detects: with
   cujs/02 unlanded the test fails on the map row (SPEC's stated
   acceptance for this task).

## Acceptance

- [ ] `grep -c 'map --limit' context-tree/tests/doc_conformance.rs` → 0 (waiver gone)
- [ ] `cd context-tree && cargo test --test doc_conformance` → exit 0 with the seeded entry removed
