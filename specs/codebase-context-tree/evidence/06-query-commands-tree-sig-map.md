# Verification: Task 06 — Query commands tree/sig/map

Branch: `task/06-query-commands-tree-sig-map` (confirmed via `git branch --show-current`)
Base for append-only diff check: `7aaa9d6`

## Verdict: PASS

## Per-criterion results

1. `cd context-tree && cargo test root_guard` — PASS
   - 2 passed: `root_guard_exits_2_and_names_ctx_init_without_a_context_root`,
     `root_guard_query_succeeds_after_init`. Matches claimed evidence.

2. `cd context-tree && cargo test tree_` — PASS
   - 6 passed: depth cap, limit/truncation line, `--doc`, empty scope, C10
     marker plumbing, containment indentation. Matches claimed evidence.

3. `cd context-tree && cargo test sig_` — PASS
   - 5 passed: default doc-first-line, `--doc` full docstring, C3 suffix
     resolution, no-match exit 1, ambiguous exit 3. Matches claimed evidence.

4. `cd context-tree && cargo test map_ranking` — PASS
   - 1 passed: `map_ranking_orders_by_reference_count_not_alphabetical`.

5. `cd context-tree && cargo test map_` — PASS
   - 3 passed: ranking (again, prefix overlap), `--doc`, token-budget
     truncation. Matches claimed evidence.

6. `bash context-tree/tests/fixtures/query/json_smoke.sh` — PASS
   - Output: "ok: ctx tree app.py --json -> exit 0, has .symbols" /
     "ok: ctx sig solo --json -> exit 0, has .signature" /
     "ok: ctx map --json -> exit 0, has .symbols" /
     "json_smoke: all verbs passed". Confirms tree/map assert `.symbols`,
     sig asserts `.signature`, all exit 0 through `jq .`.

7. `cd context-tree && cargo test rebuild_equivalence` — PASS
   - 2 passed: `rebuild_equivalence_byte_identical_after_cache_delete`,
     `rebuild_equivalence_transparent_rebuild_on_tampered_schema_version`.

8. `bash context-tree/scripts/check.sh` — PASS (exit 0)
   - Full suite green across rust/sync/typescript/zig/query test files,
     including the new query.rs suite; fmt+clippy folded into this script's
     earlier stages, no warnings surfaced.

## Weak-test / vacuity scrutiny (all addressed)

(a) **map_ranking not alphabetical/insertion** — CONFIRMED genuine.
`RANKED_PY` fixture (tests/query.rs:355) defines `zeta_used` (referenced
3x) and `alpha_unused` (referenced 0x). `alpha_unused` sorts FIRST
alphabetically and would appear first by insertion order too (it's
defined second in source, but `zeta_used` is defined first — so neither
alphabetical nor pure insertion order would produce the assertion
trivially: the referenced symbol here, `zeta_used`, sorts LAST
alphabetically, so ranking it above `alpha_unused` genuinely requires
reference-graph weighting). Test asserts `zeta_used` position < `alpha_unused`
position in output text.

(b) **C3 suffix vs substring** — CONFIRMED genuine. `resolve_suffix` in
`src/path.rs:65` splits on `.` and compares trailing components, not a
raw substring check (`"Handler"` would NOT suffix-match `AuthHandler`'s
component `AuthHandler` since components are compared whole, not
char-by-char substring). Test fixture `TWO_HANDLERS` defines
`app.Handler` and `app.AuthHandler`; `ctx sig Handler` exits 0 resolving
only to `app.Handler`. This logic lives in `src/path.rs`, authored in
task 05 (pre-existing, reused here, not newly hardcoded for this test).

(c) **rebuild_equivalence both halves** — CONFIRMED both present:
`rebuild_equivalence_byte_identical_after_cache_delete` asserts
`before_map == after_map`, `before_tree == after_tree`,
`before_sig == after_sig` post cache-delete.
`rebuild_equivalence_transparent_rebuild_on_tampered_schema_version`
tampers `schema_meta.version` directly via rusqlite, then asserts the
next query succeeds (exit 0) AND `journal_last_parsed(root) == indexed`
(2, the full file count), proving a transparent full rebuild rather than
an incremental no-op.

(d) **Token-budget bound** — CONFIRMED: `map_token_budget_truncates_output`
computes `small_tokens = small.len().div_ceil(4)` and asserts
`small_tokens <= 5` for `--tokens 5`, i.e., literally `ceil(bytes/4) <=
    budget`, plus a relative-size sanity check against a large budget.

(e) **Exit codes** — CONFIRMED matching spec: root guard exits `2`
(`EXIT_NO_ROOT` const in `src/cmd/mod.rs`), sig no-match exits `1`
(`EXIT_NO_MATCH`), sig ambiguous exits `3` (`EXIT_AMBIGUOUS`), and all
success paths assert `Some(0)`.

## Scope / diff review

`git diff 7aaa9d6..HEAD --stat -- context-tree/` touches:
`Cargo.toml`, `src/cli.rs`, `src/cmd/map.rs`, `src/cmd/mod.rs`,
`src/cmd/sig.rs`, `src/cmd/tree.rs`, `src/index/mod.rs`, `src/lib.rs`,
`tests/fixtures/query/json_smoke.sh`, `tests/query.rs`.

- `cmd/tree.rs`, `cmd/sig.rs`, `cmd/map.rs`, `cli.rs`, `Cargo.toml`,
  `tests/fixtures/query/**`, `tests/*.rs` — all explicitly in the task's
  `Touch:` header.
- `src/lib.rs` — new match arms wiring `Tree`/`Sig`/`Map` CLI variants to
  `cmd::` dispatch, plus `pub mod cmd;` declaration. This is the minimal
  glue needed for the three touched command modules to be reachable from
  `run()`; matches the worker's self-reported justified escape
  ("subcommand dispatch/module wiring").
- `src/index/mod.rs` — two new read-only methods (`all_symbols`,
  `reference_counts`) plus a `SymbolRow` struct; no mutation of existing
  index-writing code. Matches the worker's self-reported escape
  ("read-only symbol-query methods").
- `src/cmd/mod.rs` — new module file (not explicitly named in `Touch:`,
  but `cmd/tree.rs`/`cmd/sig.rs`/`cmd/map.rs` cannot exist as a module
  tree without a `mod.rs`). Contains the shared C4 root-guard/R3
  sweep/C7 token-count/C10 marker helpers step 1 of the task explicitly
  calls for ("implement the C4 root guard as a shared pre-command check
  used by every non-init command"). Judged necessary scaffolding, not
  scope creep — no unrelated behavior added.
- `Cargo.toml` — adds `serde_json` (prod) and `rusqlite` (dev-dep, for the
  schema-tamper test) — both directly required by the `--json` variants
  and the rebuild-equivalence test respectively; consistent with Touch.

No changes outside `context-tree/` other than the task file itself.

## Task-file append-only check

`git diff 7aaa9d6..HEAD -- 'specs/*/tasks/*.md'` shows changes confined to
`specs/codebase-context-tree/tasks/06-query-commands-tree-sig-map.md`:
`Status: in-progress` → `Status: done`, all 7 acceptance checkboxes
`- [ ]` → `- [x]` with appended evidence lines (test names/counts). No
criterion text changed, no other task file touched. Compliant.

## Gate

`bash context-tree/scripts/check.sh` exits 0 (fmt + clippy -D warnings +
full test suite, confirmed via `echo EXIT:$?`).
