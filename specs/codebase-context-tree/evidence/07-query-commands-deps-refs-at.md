# Verification evidence — task 07: query commands deps/refs/at

Verdict: PASS

Branch: task/07-query-commands-deps-refs-at
Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-a75fd7ead1dfb2be5
HEAD at verification: 3e95c73 (style: rustfmt deps/refs query commands and tests (task 07))

## Per-criterion results

1. `cd context-tree && cargo test deps_`
   → PASS. `test deps_empty_scope_exits_0 ... ok`, `test deps_json_has_edges_key ... ok`,
   `test deps_forward_and_reverse_edges ... ok` — 3 passed; 0 failed.

2. `cd context-tree && cargo test refs_scope_aware`
   → PASS. `test refs_scope_aware_excludes_shadowed_local_keeps_cross_file ... ok` — 1 passed.

3. `cd context-tree && cargo test refs_`
   → PASS. `refs_json_has_references_key`, `refs_no_match_exits_1`,
   `refs_heuristic_labels_definitions_and_references`,
   `refs_caps_at_50_per_direction_with_truncation_line`,
   `refs_scope_aware_excludes_shadowed_local_keeps_cross_file` — 5 passed; 0 failed.

4. `cd context-tree && cargo test at_containment`
   → PASS. `at_containment_module_fallback_outside_definitions`,
   `at_containment_chain_for_nested_line` — 2 passed; 0 failed.

5. `cd context-tree && cargo test at_exit4`
   → PASS. `at_exit4_nonexistent`, `at_exit4_unsupported_extension`,
   `at_exit4_ignored` — 3 passed; 0 failed.

6. `bash context-tree/tests/fixtures/query/json_smoke_edges.sh` (from repo root)
   → PASS, exit 0. Output:

   ```
   ok: ctx deps app.py --json -> exit 0, has .edges
   ok: ctx refs helper --json -> exit 0, has .references
   ok: ctx at app.py:5 --json -> exit 0, has .chain
   json_smoke_edges: all verbs passed
   ```

7. `bash context-tree/scripts/check.sh`
   → PASS, exit 0 (all fmt/clippy/test suites green, including 9/9 typescript,
   9/9 zig, 9/9 sync suites and the full query_edges.rs suite).

## Source scrutiny

- `src/cmd/refs.rs`: always emits `"heuristic"` labels in both text and JSON
  paths; grep confirms `"precise"` never appears as an emitted label (the test
  `refs_heuristic_labels_definitions_and_references` also asserts
  `!text.contains("precise")`). Symbol resolution goes through
  `crate::path::resolve_suffix` (C3 suffix matching over qualified paths);
  0 matches → `EXIT_NO_MATCH` (1); >1 distinct name → `EXIT_AMBIGUOUS` (3).
  Scope-awareness (`is_shadowed`) checks a same-named `ScopeRow` (populated
  from a `scopes` locals-query table that predates this task) enclosing the
  reference's byte offset in the _same file_ — this correctly restricts
  shadowing to same-file locals and does not exclude legitimate cross-file
  hits. Not vacuous: `is_shadowed` filters by `s.path == rf.path` and a byte
  range, so a same-named reference in a different file is unaffected.

- `tests/query_edges.rs` `refs_scope_aware_excludes_shadowed_local_keeps_cross_file`:
  builds three files (global def in util.ts, a true cross-file call in
  app.ts, and a function-local shadowing `const target` in shadow.ts), then
  asserts by content-scan that `app.ts` IS present in the `ref` lines and
  `shadow.ts` is NOT. This is a genuine behavioral assertion, not a
  non-empty/tautological check — it positively confirms both inclusion and
  exclusion by file name.

- `refs_caps_at_50_per_direction_with_truncation_line`: asserts the exact
  ref-line count `== 50` (not `<= 50` or nonzero), that the truncation text
  contains both "more" and "--limit" (the flag to raise), that the omitted
  count "10" (60 - 50) is named, and cross-checks that `--limit 100` lifts
  the count to the full 60. This is a precise, non-vacuous cap test.

- `src/cmd/at.rs`: innermost symbol found via
  `s.full_start_byte <= target && target < s.full_end_byte`, taking the
  `max_by_key(full_start_byte)` among enclosing symbols — a real byte-span
  containment computation, not a heuristic proximity guess. The chain is
  built by walking `parent` qpath links up from the innermost symbol via a
  `by_qpath` map, then reversed to module→…→innermost order, with any
  extractor-emitted `module`-kind symbol filtered out since a synthesized
  module entry is always prepended. The module-fallback case (line 7 in the
  fixture, a bare comment enclosed by no definition) resolves to an empty
  `chain` Vec, leaving only the synthesized module entry — genuine fallback
  behavior, not string-matching a hardcoded case. Ignored/unsupported-
  extension/nonexistent-file checks run in that exact order
  (file-exists → extension-supported → vcs-ignored) each returning one-line
  reasons via `fail()` and `EXIT_BAD_POSITION` (4).

- `src/cmd/deps.rs`: forward mode filters imports by `in_scope(im.path, ...)`;
  reverse mode resolves the _scope's_ file-module identities
  (`file_module_keys`) and matches normalized import target strings
  (`norm_module`) against them — genuinely bidirectional, not the same
  filter run twice. An import-less scope (`deps_empty_scope_exits_0`)
  naturally yields an empty `edges` Vec and the text/JSON branches both
  print nothing beyond structure, exiting `ExitCode::SUCCESS` (0) — no
  special-cased early return for emptiness, so this is real, not gamed.

No overfitting to exact test-fixture strings found: `refs`/`at`/`deps` logic
is generic over any qpath/byte-span/import data, not conditioned on the
specific fixture file names or symbol names used in the tests.

## Append-only task-file check

`git diff 548003a HEAD -- specs/codebase-context-tree/tasks/07-query-commands-deps-refs-at.md`
→ **empty diff**. The task file is byte-identical to the base commit,
including the `Status: in-progress` header and all acceptance checkboxes
left unchecked. No criterion text was altered (trivially satisfies the
append-only rule since nothing changed at all), but note the Status/
checkboxes were never updated to reflect the work — a process gap for the
worker/orchestrator to close, not a scope-creep or correctness finding.

## Scope / Touch-list findings

`git diff 548003a HEAD --stat -- context-tree/` shows changes to:

- `src/cli.rs` (in Touch list)
- `src/cmd/at.rs`, `src/cmd/deps.rs`, `src/cmd/refs.rs` (in Touch list)
- `tests/query_edges.rs`, `tests/fixtures/query/json_smoke_edges.sh` (in Touch list, `tests/*.rs` / `tests/fixtures/query/**`)
- `src/cmd/mod.rs` — **not** in the task's Touch header
- `src/lib.rs` — **not** in the task's Touch header
- `src/index/mod.rs` — **not** in the task's Touch header

Judgment: these three out-of-Touch edits are the minimal structurally
required changes to deliver the stated goal, not scope creep:

- `cmd/mod.rs`: registers the new `at`/`refs` submodules (`pub mod at;`,
  `pub mod refs;`) and adds `EXIT_BAD_POSITION = 4`, the exit code R19
  requires — a new subcommand cannot be wired without a `pub mod`
  declaration, and the new exit code is a shared constant, not duplicated
  per-file.
- `src/lib.rs`: adds the `Command::Deps | Refs | At` match arms dispatching
  to the new `cmd::{deps,refs,at}::run` — required once `cli.rs` (in Touch)
  gains the new `Command` variants; there is no way to make the CLI
  variants reachable without this.
- `src/index/mod.rs`: adds `full_end_byte` to `SymbolRow` and three new
  read-only accessor methods (`all_references`, `all_imports`,
  `all_scopes`) plus their row structs (`RefRow`, `ImportRow`, `ScopeRow`).
  No new tables are created (`grep CREATE TABLE` shows none added by this
  diff) — these read from pre-existing `refs`/`imports`/`scopes` tables
  populated by earlier tasks; `ctx deps`/`ctx refs`/`ctx at` are the first
  commands to need this data, so the accessors did not exist yet. This is
  additive and read-only, does not modify sync/index behavior, and does
  not touch `cmd/tree.rs`, `cmd/sig.rs`, or `cmd/map.rs` per the task's own
  isolation instruction (verified: no changes to those three files).

No unrelated formatting sweeps, version bumps, or drive-by edits found
outside the above.

## Commands run (for reproducibility)

```
export PATH="$HOME/.cargo/bin:$PATH"
cd context-tree && cargo test deps_
cd context-tree && cargo test refs_scope_aware
cd context-tree && cargo test refs_
cd context-tree && cargo test at_containment
cd context-tree && cargo test at_exit4
bash context-tree/tests/fixtures/query/json_smoke_edges.sh   # from repo root
bash context-tree/scripts/check.sh
git diff 548003a HEAD -- specs/codebase-context-tree/tasks/07-query-commands-deps-refs-at.md
git diff 548003a HEAD --stat -- context-tree/
git diff 548003a HEAD -- context-tree/src/index/mod.rs context-tree/src/cmd/mod.rs context-tree/src/lib.rs
```
