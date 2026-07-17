# Verification: Task 04 — Kotlin, OCaml, Haskell, Bash extraction

Verified fresh eyes, no source modified. Branch: task/04-remaining-language-extraction.
Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-a68f9c8f23b7a6931/context-tree

## Verdict: PASS

## Per-criterion

1. ✓ `cargo test kotlin` — command run from context-tree dir.
   Output: `tests/kotlin.rs` running 9 tests, all `ok`, including
   `kotlin_reference_extracted_at_known_call_site` and
   `kotlin_import_edges_extracted`. `test result: ok. 9 passed; 0 failed`.

2. ✓ `cargo test ocaml` — `tests/ocaml.rs` running 11 tests, all `ok`,
   including `ocaml_reference_extracted_at_known_use_site` and
   `ocaml_import_edges_extracted`, plus
   `ocaml_scope_facts_extracted_from_locals_query`.
   `test result: ok. 11 passed; 0 failed`.

3. ✓ `cargo test haskell` — `tests/haskell.rs` running 8 tests, all `ok`,
   including `haskell_reference_extracted_at_known_use_site` and an
   import-extraction test. `test result: ok. 8 passed; 0 failed`.

4. ✓ `cargo test bash` — `tests/bash.rs` running 8 tests, all `ok`,
   including `bash_reference_extracted_at_known_call_site` and
   `bash_import_edges_extracted`. `test result: ok. 8 passed; 0 failed`.

5. ✓ `ls context-tree/tests/fixtures/languages/ | sort` →
   `bash c cpp go haskell java kotlin ocaml python rust typescript zig`
   (exact match, 12 names).

6. ✓ `ls context-tree/tests/fixtures/languages/typescript/` →
   `helper.js`, `sample.ts`, `widget.tsx` — one file each of .js/.ts/.tsx.

7. ✓ `cargo test 2>&1 | grep -c '^covered: '` → `12`.

8. ✓ `bash context-tree/scripts/check.sh` → exit code `0`. Full `cargo
test` run showed zero failures across all test binaries (grepped
   `test result:` lines, all "0 failed").

## Substance checks (beyond green tests)

- **Reference facts at real cross-symbol use sites**: each of the 4
  extractors constructs `Reference { .. }` (grep counts: kotlin=2,
  ocaml=1, haskell=1, bash=1 occurrences of `Reference {` in the
  respective src file) and each has a passing
  `*_reference_extracted_at_known_*_site` test.

- **Import/open/source edges**: each extractor constructs `Import { .. }`
  (1 occurrence each) and each has a passing `*_import_edges_extracted`
  test.

- **Scope facts — OCaml yes, others legitimately no**: `src/lang/ocaml.rs`
  builds `Scope { .. }` facts (line 317) and has a passing
  `ocaml_scope_facts_extracted_from_locals_query` test. `src/lang/{kotlin,
haskell,bash}.rs` each carry an explicit doc comment stating no Scope
  facts are produced (R10 fallback), and none of `tests/{kotlin,haskell,
bash}.rs` mention "scope" (grep found none). Cross-checked against the
  actual tree-sitter grammar sources in
  `~/.cargo/registry/src/.../tree-sitter-{kotlin-ng-1.1.0,ocaml-0.25.0,
haskell-0.23.1,bash-0.25.1}`:
  - kotlin-ng: no `locals.scm` file at all.
  - bash: no `locals.scm` file at all.
  - ocaml: `queries/locals.scm` contains `@local.scope` (line 14).
  - haskell: `queries/locals.scm` contains only `@local.definition` /
    `@local.reference` captures, no `@local.scope`.
    This exactly matches the task's claimed substance.

- **Registration**: `src/lang/mod.rs` has `pub mod bash;`, `pub mod
haskell;`, `pub mod kotlin;`, `pub mod ocaml;` (plus existing 8).
  `Cargo.toml` has `tree-sitter-bash = "0.25.0"`, `tree-sitter-haskell =
"0.23.1"`, `tree-sitter-kotlin-ng = "1.1.0"`, `tree-sitter-ocaml =
"0.25.0"` (resolved versions in Cargo.lock: bash 0.25.1, others exact).
  `cargo tree` confirms all 4 present in the dependency graph.

## Touch-scope compliance

`git diff 8b85679 --stat -- context-tree/` shows exactly:

- `Cargo.toml` (+4 lines, new deps) — in Touch.
- `Cargo.lock` (+44 lines) — mechanical side-effect of the Cargo.toml
  dependency addition; not explicitly named in Touch but not a
  substantive scope violation (no independent content).
- `src/lang/{bash,haskell,kotlin,ocaml}.rs` (new files) — in Touch.
- `src/lang/mod.rs` (+4 lines, pub mod additions) — in Touch.
- `tests/{bash,haskell,kotlin,ocaml,language_coverage}.rs` (new files) —
  covered by Touch's `context-tree/tests/*.rs`.
- `tests/fixtures/languages/{bash,haskell,kotlin,ocaml}/*` (new fixtures)
  — in Touch.

No edits to any task 01-03-owned files (existing extractors, existing
tests, existing fixtures) — confirmed absent from the diff stat.

## Task-file append-only check

`git diff 8b85679 -- specs/codebase-context-tree/tasks/04-remaining-
language-extraction.md` → empty (no changes at all since base). Status
is still `in-progress` and acceptance boxes unticked, consistent with
"verifying before close-out" — not a failure per the caller's
instructions.

## Gate

`bash context-tree/scripts/check.sh` exits 0 (full cargo test suite,
all green, no failures observed in any of the 12+ test binaries).

## Scope-creep findings

None beyond the Cargo.lock note above, which is a benign mechanical
artifact of the sanctioned Cargo.toml change.
