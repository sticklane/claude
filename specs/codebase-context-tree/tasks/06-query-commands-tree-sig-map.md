# Task 06: Query commands — tree, sig, map; root guard; rebuild equivalence

Status: pending
Depends on: 05
Priority: P1
Budget: 45 turns
Spec: ../SPEC.md (requirements R3, R6, R7, R8, R18; contracts C1, C3, C4, C7, C10)
Touch: context-tree/src/cmd/tree.rs, context-tree/src/cmd/sig.rs, context-tree/src/cmd/map.rs, context-tree/src/cli.rs, context-tree/Cargo.toml, context-tree/tests/fixtures/query/**, context-tree/tests/*.rs

## Goal

`ctx tree <path> [--depth N] [--limit N] [--doc] [--json]`, `ctx sig
<symbol> [--doc] [--json]`, and `ctx map [--tokens N] [--doc] [--json]`
exist, each running R3's staleness sweep first (skippable with
`--no-sync`), printing compact plain text by default and a `--json`
variant otherwise, resolving `<symbol>`/`<path>` arguments per C3, and
appending the C10 `[notes:<count>]` / `[notes:<count>!]` marker via task
05's `note_marker` API wherever a symbol is named (markers will show
nothing until task 09 populates notes — that's expected here). `ctx map`
ranks by reference-graph importance, not lexical/insertion order (R8),
truncated to a token budget counted per C7. `ctx tree` honors both a depth
cap and a result cap (default 200) with a truncation line. Every command
that runs without a `.context/` ancestor exits 2 naming `ctx init` (C4
root guard), except `ctx init` itself.

## Touch

Only `cmd/tree.rs`, `cmd/sig.rs`, `cmd/map.rs`, and CLI wiring for these
three subcommands. Do not touch `cmd/deps.rs`, `cmd/refs.rs`, `cmd/at.rs`
(task 07, disjoint and safe to run concurrently with this task).

## Steps

1. RED: failing test — `ctx map` in a git fixture with no `.context/`
   exits 2 and names `ctx init`; running `ctx init` then the same query
   succeeds. GREEN: implement the C4 root guard as a shared pre-command
   check used by every non-init command.
2. RED/GREEN: `ctx tree <path>` — containment outline for the requested
   subtree, `--depth N`, `--limit N` (default 200) with a truncation line
   naming the omitted count and the flag to raise, `--doc` appending each
   symbol's first docstring line, C10 markers on symbol lines.
3. RED/GREEN: `ctx sig <symbol>` — signature + first docstring line + C10
   marker by default; `--doc` prints the full (possibly multi-line)
   docstring in full where the default prints only its first line.
4. RED/GREEN: `ctx map` — ranked overview by reference-graph importance
   (requires a reference-count pass over the index), truncated to
   `--tokens` (default 1000, `ceil(bytes/4)` per C7), `--doc` appending
   first docstring lines counted within the same budget, C10 markers.
5. Ranking test (R8): build a fixture where symbol A is referenced by ≥3
   other symbols, symbol B by none, and lexical order would place B
   first; assert `ctx map` ranks A strictly above B.
6. `--json` variant for all three commands; each pipes through `jq .` with
   exit 0 and an asserted key for that verb's payload.
7. C3 suffix-resolution test via `ctx sig`: a fixture defining both
   `app.Handler` and `app.AuthHandler`; `ctx sig Handler` exits 0 and
   resolves to `app.Handler` (proving suffix matching, not substring
   matching, since a substring matcher would ambiguously match both and
   exit 3); a no-match argument exits 1; an argument matching multiple
   symbols on a `.`-boundary suffix prints the candidate list (qualified
   path + file:line) and exits 3.
8. Rebuild equivalence test (C4, CUJS CUJ11): capture `ctx map`, `ctx
tree`, and `ctx sig` output on a fixture; delete `.context/cache/`;
   re-run the same queries; assert byte-identical output. Separately,
   tamper the cache's schema-version field; assert the next query
   transparently rebuilds (the post-tamper journal record shows `parsed`
   == the full indexed file count) and the query still succeeds.
9. Empty/symbol-less scope: `ctx tree` over an empty or symbol-less path
   prints empty output and exits 0.

## Acceptance

- [ ] `cd context-tree && cargo test root_guard` → passes (C4: exit 2 +
      `ctx init` pointer; success after init)
- [ ] `cd context-tree && cargo test tree_` → passes (depth/result caps,
      truncation line, `--doc`, C10 marker plumbing)
- [ ] `cd context-tree && cargo test sig_` → passes (default vs `--doc`
      docstring depth, C10 marker plumbing, C3 suffix resolution incl.
      exit 3 ambiguous / exit 1 no-match)
- [ ] `cd context-tree && cargo test map_ranking` → passes (A ranks above
      B; not alphabetical/insertion order)
- [ ] `cd context-tree && cargo test map_` → passes (token budget per C7,
      `--doc`)
- [ ] `for v in tree sig map; do ./context-tree/target/release/ctx $v --json ... | jq . ; done` →
      each exits 0 with an asserted key (exact invocation per verb defined
      in the test fixture script)
- [ ] `cd context-tree && cargo test rebuild_equivalence` → passes
      (byte-identical post-cache-delete; transparent rebuild on tampered
      schema version)
- [ ] `bash context-tree/scripts/check.sh` → exits 0
