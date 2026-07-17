# Task 07: Query commands — deps, refs, at

Status: pending
Depends on: 05
Priority: P1
Budget: 45 turns
Spec: ../SPEC.md (requirements R3, R9, R10, R19; contracts C3, C10)
Touch: context-tree/src/cmd/deps.rs, context-tree/src/cmd/refs.rs, context-tree/src/cmd/at.rs, context-tree/src/cli.rs, context-tree/tests/fixtures/query/**, context-tree/tests/*.rs

## Goal

`ctx deps <path> [--reverse] [--json]`, `ctx refs <symbol> [--limit N]
[--json]`, and `ctx at <file>:<line> [--json]` exist, each running R3's
staleness sweep first, resolving `<symbol>` per C3, and appending C10
markers where a symbol is named. `ctx refs` labels each result `heuristic`
or `precise`, is scope-aware where the grammar has locals queries
(excluding function-local shadowed references from cross-file candidates),
and caps at 50 results per direction by default with a truncation line.
`ctx at` resolves a file:line to its innermost enclosing symbol and prints
the containment chain, falling back to the file's module symbol when no
definition encloses the position, and exits 4 with a one-line reason for
an ignored/unsupported/nonexistent file.

## Touch

Only `cmd/deps.rs`, `cmd/refs.rs`, `cmd/at.rs`, and CLI wiring for these
three subcommands. Do not touch `cmd/tree.rs`, `cmd/sig.rs`, `cmd/map.rs`
(task 06, disjoint and safe to run concurrently with this task) — both
tasks call the same fixed `note_marker` API from task 05, so there is no
shared design decision to coordinate.

## Steps

1. RED/GREEN: `ctx deps <path>` — module-level import edges out of the
   path; `--reverse` for edges into it.
2. RED/GREEN: `ctx refs <symbol>` — definitions and references, each
   labeled `heuristic` (global-name match) or `precise` (reserved for R11
   LSP enrichment, task 08 — this task always emits `heuristic` since no
   LSP pass runs yet), capped at 50 per direction with a truncation count
   line naming the flag to raise.
3. Scope-aware refs test (R10): in the TypeScript fixture (a grammar with
   locals queries, from task 02), build a case where a function-local
   variable shadows a global function's name; assert `ctx refs <global>`
   excludes the shadowed local references and still lists the true
   cross-file call site. Implement scope-awareness via `@local.scope`/
   `@local.definition` locals-query analysis per-file where the grammar
   provides it; languages without locals queries fall back to plain
   name matching (document this fallback in a code comment, not a spec
   change).
4. RED/GREEN: `ctx at <file>:<line>` — containment chain (module -> ... ->
   innermost) with each symbol's kind, C1 path, signature first line,
   first docstring line, C10 marker; a line inside a nested function
   resolves the full chain; a line outside any definition resolves to the
   module symbol.
5. `ctx at` failure path: a file the index skips (ignored, unsupported
   extension) or that does not exist prints one line naming the reason and
   exits 4.
6. `--json` variant for all three commands; each pipes through `jq .` with
   exit 0 and an asserted key for that verb's payload.
7. Empty/symbol-less scope: `ctx deps` over a path with no imports prints
   empty output and exits 0.

## Acceptance

- [ ] `cd context-tree && cargo test deps_` → passes (forward and
      `--reverse` edges; empty scope exits 0)
- [ ] `cd context-tree && cargo test refs_scope_aware` → passes (R10:
      shadowed local excluded, true cross-file call site retained)
- [ ] `cd context-tree && cargo test refs_` → passes (heuristic labeling,
      50-result cap + truncation line)
- [ ] `cd context-tree && cargo test at_containment` → passes (nested-line
      chain; outside-definition module fallback)
- [ ] `cd context-tree && cargo test at_exit4` → passes (ignored /
      unsupported-extension / nonexistent file: one-line reason, exit 4)
- [ ] `for v in deps refs at; do ./context-tree/target/release/ctx $v --json ... | jq . ; done` →
      each exits 0 with an asserted key
- [ ] `bash context-tree/scripts/check.sh` → exits 0
