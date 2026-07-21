# Task 02: near-miss "did you mean" candidate list

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 01
Priority: P2
Budget: 16 turns
Spec: ../SPEC.md (requirements R4)
Touch: context-tree/src/cmd/sig.rs, context-tree/src/cmd/refs.rs, context-tree/src/cmd/no_match.rs, context-tree/tests/integration.rs, context-tree/tests/query.rs

## Goal

When a `refs`/`sig` no-match has case-insensitive or substring candidates
in the symbol table, up to 5 are listed as "did you mean" BEFORE task 01's
boundary note — cheap (symbol-table lookup only, no tree work).

## Touch

Extends task 01's shared `no_match.rs` helper and the same two call sites
(`sig.rs`, `refs.rs`) — do not duplicate task 01's boundary-note/
suggested-command logic; add the near-miss listing as a new step ahead of
it in the same output-assembly path. Do not touch
`context-tree/src/cmd/notes.rs` or `--json` mode's error shape beyond
what task 01 already extended (no new JSON keys needed unless the fixture
test requires one — check task 01's `boundary_note`/`suggested_check`
shape first).

## Steps

1. Write a failing test first: a case-variant fixture (e.g. query
   `FigureBboxes` when only `figureBboxes` is indexed) asserts up to 5
   case-insensitive/substring candidates appear as a "did you mean" list
   BEFORE the boundary note, in text mode.
2. Implement the near-miss lookup against the existing symbol table (no
   new indexing, no tree work — a linear scan or existing lookup API is
   fine at this scale) and wire it into `no_match.rs`'s output assembly,
   gated on candidates existing (empty candidate list = no "did you mean"
   section, output identical to task 01's).
3. Cap the list at 5 candidates; if the symbol table lookup can return
   more, truncate deterministically (stable order — e.g. sorted).
4. Make the test pass; run `cargo fmt`/`cargo clippy` clean.

## Acceptance

- [x] `cd context-tree && cargo test -- did_you_mean` (or equivalent, in
      `tests/integration.rs`/`tests/query.rs`) passes: a case-variant
      fixture emits up to 5 "did you mean" candidates before the boundary
      note; a fixture with zero candidates emits output identical to task
      01's baseline (parse-then-assert, not substring match).
      Evidence: `cargo test -- did_you_mean` → 5 passed (2 unit in
      no_match.rs + 3 integration in tests/integration.rs:
      sig_no_match_lists_did_you_mean_before_boundary_note,
      refs_no_match_lists_did_you_mean_candidates,
      no_match_without_near_miss_omits_did_you_mean); full `cargo test`
      green (0 failures across all binaries; integration.rs 6 passed).
- [x] `cd context-tree && cargo fmt --check && cargo clippy -- -D warnings`
      clean.
      Evidence: `cargo fmt --check` → exit 0; `cargo clippy --all-targets
      -- -D warnings` → Finished, no warnings.
