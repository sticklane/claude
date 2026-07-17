# Verification: 02-mainstream-language-extraction

Verdict: PASS

## Environment

`export PATH="$HOME/.cargo/bin:$PATH"` applied before all cargo commands, as instructed.

## Per-criterion results

1. `cd context-tree && cargo test typescript` → **PASS**
   9 tests passed (0 failed): typescript_parse_failed_file_yields_best_effort_sibling_facts,
   typescript_import_edges_extracted, typescript_coverage_marker_emitted,
   typescript_c8_docstring_carries_fixture_sentinel,
   typescript_reference_extracted_at_known_call_site,
   typescript_c1_paths_are_unique_and_resolve_by_suffix,
   typescript_locals_scope_distinguishes_local_from_global,
   typescript_tsx_and_js_dispatch_by_extension,
   typescript_c2_hash_stable_under_pure_rename_changes_on_body_edit.
   `test result: ok. 9 passed; 0 failed; ...`

2. `cd context-tree && cargo test go` → **PASS**
   8 tests passed (0 failed), including go_reference_extracted_at_known_call_site and
   go_import_edges_extracted. `test result: ok. 8 passed; 0 failed; ...`

3. `cd context-tree && cargo test rust` → **PASS**
   7 tests passed (0 failed), including rust_reference_extracted_at_known_call_site and
   rust_import_edges_extracted. `test result: ok. 7 passed; 0 failed; ...`

4. `cd context-tree && cargo test java` → **PASS**
   8 tests passed (0 failed), including java_reference_extracted_at_known_call_site and
   java_import_edges_extracted. `test result: ok. 8 passed; 0 failed; ...`

5. `cd context-tree && cargo test 2>&1 | grep -Fx "covered: typescript"` (and go/rust/java)
   → **PASS** — all four lines present verbatim in full `cargo test` output:
   `covered: typescript`, `covered: go`, `covered: rust`, `covered: java`.

6. `bash context-tree/scripts/check.sh` → **PASS**, exit code 0 (verified explicitly via
   `$?` immediately after the run, not piped through `tail`). Full suite (fmt/clippy/tests
   per script) ran clean; all 4 language test files reported `ok`.

## Goal sanity-check (not just tests passing)

- **TypeScript dispatch by extension is real**: `src/lang/typescript.rs` registers one
  `TypescriptExtractor` for extensions `["ts","tsx","js"]`; `language_for_ext` maps
  `"tsx"→tree_sitter_typescript::LANGUAGE_TSX`, `"js"→tree_sitter_javascript::LANGUAGE`,
  else `tree_sitter_typescript::LANGUAGE_TYPESCRIPT` — three distinct tree-sitter grammars,
  not one grammar reused. `typescript_tsx_and_js_dispatch_by_extension` test exercises all
  three fixture files (sample.ts, widget.tsx, helper.js).
- **Go/Java C1 module = package, not file path**: `go.rs::package_name` reads the
  `package_clause` node's identifier (file-path used only as a fallback if absent);
  `java.rs::package_name` reads `package …;` similarly. Both have a dedicated passing test
  (`go_module_is_the_package_name_not_the_file_path`,
  `java_module_is_the_package_not_the_file_path`).
- **Scope fact for shadowing is genuinely produced, not stubbed**: the TS fixture
  (`tests/fixtures/languages/typescript/sample.ts`) contains a module-level
  `function value()` and, inside `class Widget { render() { const value = 42; ... } }`,
  a function-local `value` that shadows it. `extract_scopes` runs a real tree-sitter
  locals query (`LOCALS_QUERY`, authored in typescript.rs since the shipped TS query is
  params-only) over scope/definition captures and computes innermost-scope containment by
  byte range. The test `typescript_locals_scope_distinguishes_local_from_global` asserts
  the local scope does NOT contain the global def's byte offset and DOES contain the local
  read's byte offset — genuine logic, not a fixed/stubbed fact.
- **References/imports are real facts**: all four extractors walk the AST
  (`call_expression`/`selector_expression`/`member_expression` for calls,
  `import_statement`/`import_declaration`/`use_declaration`-equivalent for imports) and
  each has a passing reference-extraction and import-extraction test tied to a specific
  known call site / import statement in its fixture.

## Touch-scope check

`git diff --stat 949b33e..HEAD -- context-tree/` shows only:
Cargo.lock, Cargo.toml, src/lang/{go,java,mod,rust,typescript}.rs,
tests/fixtures/languages/{go,java,rust,typescript}/*, tests/{go,java,rust,typescript}.rs.

`git diff 949b33e..HEAD -- context-tree/src/lang/python.rs context-tree/src/path.rs
context-tree/src/facts.rs context-tree/src/hash.rs context-tree/src/extract.rs
context-tree/src/sync/ context-tree/src/index/ context-tree/src/cmd/` → empty (0 lines) —
none of the explicitly forbidden files/dirs were touched.

`src/lang/mod.rs` diff is exactly 4 added `pub mod` lines (go, java, rust, typescript) —
matches Touch's "minimal pub mod lines" instruction.

Note: `Cargo.lock` changed (55 lines) as an automatic side effect of the `Cargo.toml`
grammar-dependency additions. Not separately listed in Touch, but this is a standard,
unavoidable side effect of a Cargo.toml edit, not scope creep.

## Append-only task-file check (base 949b33e)

`git diff 949b33e -- specs/codebase-context-tree/tasks/02-mainstream-language-extraction.md`
shows exactly one hunk: insertion of the `<!-- PLAN ... -->` HTML comment block
(delete-at-close-out plan notes) directly under the header fields. Status line
(`in-progress`), Touch line, and all acceptance checkboxes are byte-identical to base —
unchanged. This is within the allowed edit set (plan comment block); no criterion text,
other files, or unauthorized sections were touched.

Flag (process, not correctness): the task file's own Status line still reads
`in-progress` and none of the 6 acceptance checkboxes are ticked, despite all 6
criteria passing under independent verification. The task is functionally complete
per this audit but was not self-marked done by the implementer.

## Scope-creep findings

None found. Diff is fully within Touch list (plus the expected Cargo.lock side effect).

## Overfitting check

Extractors use genuine AST-node-kind pattern matching (symbol_kind/classify_identifier
tables, receiver-type extraction, doc-comment adjacency walks) rather than special-casing
literal fixture strings/names. The TS shadowing test asserts byte-range containment
logic, not a hardcoded expected count. No evidence of test-gaming.
