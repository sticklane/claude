# Task 02: TypeScript/JavaScript/TSX, Go, Rust, Java extraction

Status: pending
Depends on: 01
Priority: P1
Budget: 40 turns
Spec: ../SPEC.md (requirements R1 [typescript, javascript, go, rust, java]; contracts C1, C2, C8)
Touch: context-tree/Cargo.toml, context-tree/src/lang/mod.rs, context-tree/src/lang/typescript.rs, context-tree/src/lang/go.rs, context-tree/src/lang/rust.rs, context-tree/src/lang/java.rs, context-tree/tests/fixtures/languages/{typescript,go,rust,java}/**, context-tree/tests/*.rs

## Goal

Four more `LanguageExtractor` implementations exist and are registered:
TypeScript/TSX/JavaScript (one fixture bucket, `typescript/`, dispatching
by file extension to the right grammar), Go, Rust, and Java — each
producing R1 facts with C1 qualified paths using that language's own
module concept (Go package, Java package, Rust module path; TS/JS has no
listed module concept in C1, so use the repo-relative-file-path fallback,
consistent with how C1 treats languages without one) and C8 docstrings
(Go doc comments, Rust `///`/`//!`, Javadoc, JSDoc/TSDoc).

## Touch

Only add new `src/lang/<name>.rs` files plus the minimal `pub mod` lines
in `src/lang/mod.rs` and new grammar dependencies in `Cargo.toml`. Do not
touch `src/lang/python.rs` (task 01) or any file under `src/sync/`,
`src/index/`, or `src/cmd/` (later tasks).

## Steps

1. Add grammar deps: `tree-sitter-typescript` (covers both `.ts`/`.tsx`
   grammar variants), `tree-sitter-javascript`, `tree-sitter-go`,
   `tree-sitter-rust` (or the ABI-shim-compatible current crate),
   `tree-sitter-java`.
2. RED: for each language, write a failing extraction test against a new
   fixture file before implementing the extractor.
3. GREEN: implement each extractor against the `LanguageExtractor` trait
   from task 01 — kind enum entries, C1 path, C8 docstring, spans, parent
   containment, C2 hash + token set, parse-failed marking.
4. Fixtures: `context-tree/tests/fixtures/languages/typescript/` contains
   at least one `.ts`, one `.tsx`, and one `.js` file (per the language
   coverage acceptance criterion); `go/`, `rust/`, `java/` each contain at
   least one source file. Each fixture has one documented symbol whose
   docstring embeds a per-fixture sentinel string.
5. Wire extension-based dispatch so `.ts`/`.tsx` route to the TypeScript
   grammar and `.js` routes to the JavaScript grammar, both counted under
   the single `typescript` coverage bucket.
6. Emit `covered: typescript`, `covered: go`, `covered: rust`, `covered:
java` lines from the respective test modules on success (same pattern
   as task 01's `covered: python`).
7. Tests per language: C1 path correctness/uniqueness, C2 rename-hash
   stability, C8 sentinel docstring, parse-failed best-effort facts.

## Acceptance

- [ ] `cd context-tree && cargo test typescript` → passes (covers `.ts`,
      `.tsx`, `.js` fixtures)
- [ ] `cd context-tree && cargo test go` → passes
- [ ] `cd context-tree && cargo test rust` → passes
- [ ] `cd context-tree && cargo test java` → passes
- [ ] `cd context-tree && cargo test 2>&1 | grep -Fx "covered: typescript"`
      → line present (same for `go`, `rust`, `java`)
- [ ] `bash context-tree/scripts/check.sh` → exits 0
