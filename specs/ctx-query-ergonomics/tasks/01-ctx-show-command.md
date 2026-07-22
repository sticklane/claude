# Task 01: `ctx show` — symbol-bounded body retrieval

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: done
Depends on: none
Priority: P1
Budget: 20 turns
Spec: ../SPEC.md (requirement R2)
Touch: context-tree/src/cli.rs, context-tree/src/lib.rs, context-tree/src/cmd/show.rs, context-tree/src/cmd/mod.rs, context-tree/tests/show.rs

## Goal

`ctx show <symbol> [--head N]` prints the resolved symbol's exact source span
from the working tree, resolving by the existing C3 suffix matcher. The span is
read from the freshly-reconciled index (the shared `load_index` staleness sweep
runs first), so an edit that shifts the symbol's lines cannot produce a stale
range. `--head N` truncates long bodies; the default prints the whole span with
a truncation guard. `--json` returns `{path, start_line, end_line, text}`.

## Touch

New file `context-tree/src/cmd/show.rs`; wire it into the `Command` enum
(`cli.rs`), the `run()` dispatch (`lib.rs`), and register the module in
`cmd/mod.rs`. Tests go in a new `context-tree/tests/show.rs`.

Do NOT touch `sig.rs`, `refs.rs`, `notes.rs`, `map.rs`, or `path.rs` — the
file-scoped selector that also lands on `show` is task 02's job; this task
resolves by the bare-name C3 matcher only. Do NOT touch any `SKILL.md` (docs are
task 04). Do NOT add a `show` tool to `mcp/mod.rs` — MCP exposure is out of
scope for R2 (CLI-only); leave the MCP surface unchanged.

## Steps

1. Write the failing tests first in `tests/show.rs`, modeled on `tests/query.rs`
   helpers (`write`, `ctx`, `init`, `stdout`):
   - Span correctness: against a fixture with a known symbol at known line
     ranges, `ctx show <sym>` output is exactly that span (start..end lines,
     inclusive), no more.
   - Staleness (span-shifting edit): index the fixture, then INSERT lines ABOVE
     the symbol so its line range moves down, run `ctx show <sym>` again, and
     assert the returned span is re-resolved to the NEW location — a fixed-range
     re-read would fail this. (The sweep runs via `load_index`; do not pass
     `--no-sync`.)
   - `--head N`: caps output at N lines.
   - Truncation guard: a body longer than the cap (200 lines) prints the capped
     lines followed by a tail like `… +K more lines, use --head/Read`.
   - `--json`: emits `{path, start_line, end_line, text}`; assert the keys and
     that `text` equals the span.
2. Add `Show { symbol, head: Option<usize>, json, no_sync }` to the `Command`
   enum in `cli.rs` (mirror the doc-comment + `--no-sync`/`--json` pattern of the
   sibling verbs).
3. Add the dispatch arm in `lib.rs::run()` building `cmd::show::Args`.
4. Implement `cmd/show.rs`: reuse `cmd::load_index(no_sync)` (runs the sweep),
   resolve via `crate::path::resolve_suffix` over `store.all_symbols()`, reuse
   the sig/refs exit-code conventions (`EXIT_NO_MATCH`, `EXIT_AMBIGUOUS`,
   candidate listing on ambiguity), then read the file at `SymbolRow.path` and
   slice bytes `[full_start_byte, full_end_byte)`, converting to 1-based
   start/end lines. Provide a `render(&Args) -> (String, ExitCode)` split like
   `sig::render` if convenient, but MCP wiring is out of scope.
5. Run `bash scripts/check.sh` green.

## Acceptance

- [x] `cd context-tree && cargo test show` → the new `tests/show.rs` cases pass
      — evidence: 5/5 passed (span correctness, staleness re-resolution,
      `--head N` cap, 200-line default truncation guard, `--json`).
- [x] `bash context-tree/scripts/check.sh` → exits 0 (fmt, clippy -D warnings, all tests)
      — evidence: full workspace suite green after `cargo fmt` (one
      auto-applied formatting diff in `show.rs`), 0 clippy warnings.
