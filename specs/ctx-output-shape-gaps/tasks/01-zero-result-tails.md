# Task 01: zero-result diagnostic tails for refs and deps (3 branches)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P1
Budget: 14 turns
Spec: ../SPEC.md (requirement R1)
Touch: context-tree/src/cmd/refs.rs, context-tree/src/cmd/deps.rs, context-tree/src/cmd/no_match.rs, context-tree/tests/zero_result_tails.rs

## Goal

`refs` and `deps` explain zero-result outcomes instead of printing
silent emptiness: (a) a resolved symbol with zero references keeps its
`def` lines on stdout and adds a stderr tail "0 references to <name>"
(the QUERY argument, never a qpath — multi-def names) with a
`ctx deps --reverse <file>` suggestion for module/file-level symbols;
(b) `deps` on an INDEXED path with zero edges states the fact on stderr
("no indexed importers of <path>" for `--reverse`); (c) `deps` on a
path NOT in the index states "path not in index: <path>" — deps gains a
path-membership check, since today a typo'd path and a real leaf are
byte-identical. Exit codes unchanged; `--json` gains a `note` field with
existing keys untouched; the shared `render()` path carries the fields
to the MCP surface.

## Touch

Mirror the existing `no_match` eprintln/JSON-note pattern in
`refs.rs::render` (~lines 102-118); membership via `indexed_paths()`
already fetched in deps' `--reverse` branch. Do NOT touch `tree.rs` or
`cli.rs` (task 02) and do NOT emit tails on the no-match branch
(absence-check owns it) or on filter-emptied results (dead-code-zones'
future filter tail — pin with a test).

## Steps

1. Failing goldens first (new `tests/zero_result_tails.rs`, fixture
   with: a symbol defined but never referenced; a module-level symbol;
   an importless leaf file; a nonexistent path): pin today's silent
   behavior is replaced by the three tails — stderr content, stdout
   unchanged (defs preserved in (a), empty in (b)/(c)), exit codes
   unchanged.
2. Implement (a) in refs.rs (zero refs after def print → stderr tail;
   `kind == "module"` triggers the deps suggestion), (b)+(c) in deps.rs
   (membership check via `indexed_paths()`, both directions).
3. `--json`: add `note` field; golden asserts legacy keys survive
   unchanged. MCP-surface test asserts the note arrives through the MCP
   path (same `render()` — follow the absence-check two-surface test
   precedent).
4. Negative goldens: symbol no-match emits absence-check's boundary
   output and NO R1 tail.
5. fmt + clippy clean.

## Acceptance

- [x] `cd context-tree && cargo test --test zero_result_tails` → exit 0, covering: (a) def-preserved + "0 references to <name>" tail; module-symbol deps suggestion; (b) "no indexed importers" on a real leaf; (c) "path not in index" on a nonexistent path; (b)≠(c) distinction; exit codes unchanged; --json note field + legacy keys; MCP parity; no tail on symbol no-match — verifier: 13 passed, L3 (real `ctx` subprocess + MCP round-trip)
- [x] `cd context-tree && cargo test` → exit 0 (no regression across the suite) — verifier: full suite green
- [x] `cd context-tree && cargo clippy --tests -- -D warnings` → exit 0 — verifier: clean, exit 0

## Decisions

- 2026-07-21: Forward-direction zero-edge `deps` wording is `no indexed
  imports out of <path>` (the spec pinned only the reverse phrasing "no
  indexed importers of <path>"). Reversible: edit the forward-branch
  format string in `deps.rs::render`.
- 2026-07-21: The module-symbol suggestion is folded into the single
  `note` string (`"0 references to <q>; for import-level callers, try:
  ctx deps --reverse <file>"`) rather than two separate stderr lines.
  Reversible: split into two `eprintln!`/two note fields in `refs.rs`.
- 2026-07-21: When a resolved name has multiple def rows, the suggestion
  path uses the first def with `kind == "module"`. Reversible: change the
  `.find()` selector in `refs.rs::render`.
