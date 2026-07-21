# Task 01: no-match boundary output for refs/sig (text + JSON + MCP)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P1
Budget: 26 turns
Spec: ../SPEC.md (requirements R1, R2, R3)
Touch: context-tree/src/cmd/sig.rs, context-tree/src/cmd/refs.rs, context-tree/src/cmd/no_match.rs, context-tree/src/cmd/mod.rs, context-tree/tests/integration.rs, context-tree/tests/query.rs, context-tree/tests/mcp.rs

## Goal

`ctx refs`/`sig` no-match output states the boundary (symbols only, not
text presence) and hands the agent a bounded grep command to run next —
in both text mode (appended to stderr, stdout/exit code unchanged) and
`--json` mode (existing error object extended with new keys) — and the
MCP surface, which renders through the same `render()` functions, carries
the same fields for free.

## Touch

Do NOT touch `context-tree/src/cmd/notes.rs`, `context-tree/src/cmd/at.rs`,
or anything under `context-tree/src/extract.rs` — the extension union this
task needs is already available read-only via `extract::registrations()`
(iterate `.extensions` on each `ExtractorRegistration`, dedupe). Do not
reference `ctx show` anywhere — it does not exist yet (lands under
specs/ctx-query-ergonomics R2); this task covers `refs`/`sig` only.

## Steps

1. Write failing golden tests first (in `tests/integration.rs` and/or
   `tests/query.rs`, matching this repo's existing golden-test style) for
   a `refs`/`sig` no-match in text mode: assert the output has exactly
   three parts on stderr (`no symbol matches 'X'` line, a boundary note
   stating object fields/JSON keys/string literals aren't indexed, and a
   suggested `grep -rl` command), stdout is empty, exit code is unchanged
   from today, and a symbol containing `$`/`'` is correctly shell-escaped
   in the suggested command.
2. Write a failing golden test for `--json` no-match: assert the legacy
   keys (`error`, `symbol`) survive unchanged and two new keys
   (`boundary_note`, `suggested_check`) are added.
3. Write a failing test asserting the suggested command's `--include`
   list is the union of `extract::registrations()`'s `.extensions`
   (deduped, one `--include='*.<ext>'` per extension, repeated flags —
   never a brace pattern), and that `| head -20` is present verbatim.
   Assert `grep -c '{' <suggested_check>` is 0.
4. Add a shared helper (`context-tree/src/cmd/no_match.rs`) that builds
   the boundary note + suggested command from a symbol name and the
   extension union, used by both `sig.rs` and `refs.rs`'s existing
   no-match branches (`sig.rs:76`, `refs.rs:107`) — text mode appends to
   the existing `eprintln!`, JSON mode extends the existing `json!({...})`
   object. Register the new module in `cmd/mod.rs`.
5. Add an MCP-surface test in `tests/mcp.rs` asserting a no-match request
   through the MCP path returns the same `boundary_note`/`suggested_check`
   fields (proves `render()` sharing works, not just the CLI path).
6. Make all tests pass; run `cargo fmt`/`cargo clippy` clean.

## Acceptance

- [x] `cd context-tree && cargo test --test integration -- no_match` (or
      wherever the new text-mode golden lands) passes, parse-asserting all
      three output parts, empty stdout, unchanged exit code, and correct
      shell-escaping of a `$`/`'`-containing symbol.
- [x] `cd context-tree && cargo test --test query -- no_match_json` (or
      wherever the JSON golden lands) passes, parse-asserting legacy keys
      unchanged plus `boundary_note`/`suggested_check` present.
- [x] `cd context-tree && cargo test -- suggested_check_extensions` (or
      equivalent) passes: the `--include` list is exactly the union of
      `extract::registrations()`'s extensions, repeated-flag form, no
      brace pattern (`grep -c '{'` on the suggested_check value is 0).
- [x] `cd context-tree && cargo test --test mcp -- no_match` passes,
      confirming the MCP surface carries the same extended fields.
- [x] `cd context-tree && cargo fmt --check && cargo clippy -- -D warnings`
      clean.
