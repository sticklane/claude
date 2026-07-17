# Task 03: C, C++, Zig extraction

Status: pending
Depends on: 02
Priority: P1
Budget: 50 turns
Spec: ../SPEC.md (requirements R1 [c, cpp, zig], R9, R10 partial; contracts C1, C2, C3, C8)
Touch: context-tree/Cargo.toml, context-tree/src/lang/mod.rs, context-tree/src/lang/c.rs, context-tree/src/lang/cpp.rs, context-tree/src/lang/zig.rs, context-tree/tests/fixtures/languages/{c,cpp,zig}/**, context-tree/tests/*.rs

## Goal

Three more `LanguageExtractor` implementations exist: C, C++, and Zig.
All three fall under C1's "no module concept" fallback (repo-relative file
path, slashes to dots, extension dropped), except C++ namespaces which are
containers, not the module component. All three use C8's leading-comment
docstring convention (no native doc-comment syntax recognized). The C++
fixture proves C1's `#<n>` ordinal-suffix disambiguation for overloads. Per
task 01's `Reference`/`Import`/`Scope` fact types, each extractor also
produces reference occurrences and module-level `#include`/import edges
(R9); extract `Scope` facts for whichever of C/C++/Zig ship a tree-sitter
locals query (check each grammar's own query files), falling back to plain
name matching per R10 for any that don't.

## Touch

Only add new `src/lang/{c,cpp,zig}.rs` files, the `pub mod` lines in
`src/lang/mod.rs`, and new grammar deps in `Cargo.toml`. Do not touch
files owned by task 02 or earlier.

## Steps

1. Add grammar deps: `tree-sitter-c`, `tree-sitter-cpp`, `tree-sitter-zig`.
2. RED: failing extraction test per language before implementing.
3. GREEN: implement each extractor — C1 path (file-path fallback for C and
   Zig; C++ uses namespace-as-container with file-path fallback only
   where no enclosing namespace exists), C8 (contiguous comment block
   immediately preceding the definition), spans, parent containment, C2
   hash + token set, parse-failed marking, plus `Reference` and `Import`
   fact extraction (R9: C/C++ `#include`, Zig `@import`) and, where the
   grammar ships a locals query, `Scope` fact extraction (R10).
4. C++ overload fixture: write a `.cpp` fixture defining two overloads of
   the same function name in the same scope. Write a property test — not
   a self-generated snapshot — asserting: (a) their C1 qualified paths are
   DISTINCT (one carries `#1`, the other `#2` or equivalent per C1's
   ordinal rule), and (b) each resolves independently via C3 suffix
   matching (i.e. resolving by full qualified path, not by the ambiguous
   bare suffix, is unambiguous for each).
5. Fixtures: `c/`, `cpp/`, `zig/` each contain ≥1 source file with a
   documented symbol whose leading-comment docstring embeds a per-fixture
   sentinel string, proving C8's leading-comment rule, plus at least one
   cross-symbol reference and one `#include`/`@import` edge each.
6. Emit `covered: c`, `covered: cpp`, `covered: zig` lines on success.
7. Tests per language: reference-extraction (a known call site produces a
   `Reference` fact) and import-extraction (a known `#include`/`@import`
   produces an `Import` fact).

## Acceptance

- [ ] `cd context-tree && cargo test '\bc_'` (or an equivalently scoped C
      test filter) → passes, incl. reference/import extraction
- [ ] `cd context-tree && cargo test cpp` → passes, including the overload
      distinct-C1-paths property test and reference/import extraction
- [ ] `cd context-tree && cargo test zig` → passes, incl. reference/import
      extraction
- [ ] `cd context-tree && cargo test 2>&1 | grep -Fx "covered: c"` → line
      present (same for `cpp`, `zig`)
- [ ] `bash context-tree/scripts/check.sh` → exits 0
