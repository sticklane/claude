# Task 04: Kotlin, OCaml, Haskell, Bash extraction — full 12-language coverage

Status: in-progress
Depends on: 03
Priority: P1
Budget: 50 turns
Spec: ../SPEC.md (requirements R1 [kotlin, ocaml, haskell, bash], R9, R10 partial; contracts C1, C2, C8)
Touch: context-tree/Cargo.toml, context-tree/src/lang/mod.rs, context-tree/src/lang/{kotlin,ocaml,haskell,bash}.rs, context-tree/tests/fixtures/languages/{kotlin,ocaml,haskell,bash}/**, context-tree/tests/*.rs

## Goal

The final four `LanguageExtractor` implementations exist: Kotlin (package
as C1 module, KDoc per C8), OCaml (module as C1 module, `(** *)` per C8),
Haskell (module as C1 module, Haddock per C8), and Bash (file-path
fallback per C1, leading-comment per C8, same as C/Zig). With this task
complete, all 12 languages required by R1 have extractors, and the
mechanical language-coverage acceptance criterion becomes fully checkable.
Per task 01's `Reference`/`Import`/`Scope` fact types, each extractor also
produces reference occurrences and module-level import edges (R9: Kotlin
`import`, OCaml `open`/module access, Haskell `import`, Bash `source`);
extract `Scope` facts for whichever of the four ship a tree-sitter locals
query (check each grammar's own query files), falling back to plain name
matching per R10 for any that don't.

## Touch

Only add new `src/lang/{kotlin,ocaml,haskell,bash}.rs` files, the `pub
mod` lines in `src/lang/mod.rs`, and new grammar deps in `Cargo.toml`. Do
not touch files owned by tasks 01-03.

## Steps

1. Add grammar deps: `tree-sitter-kotlin-ng` 1.1.0, `tree-sitter-ocaml`
   0.25.0, `tree-sitter-haskell` 0.23.1, `tree-sitter-bash`.
2. RED: failing extraction test per language before implementing.
3. GREEN: implement each extractor — C1 path per language, C8 docstring
   convention per language, spans, parent containment, C2 hash + token
   set, parse-failed marking, plus `Reference` and `Import` fact
   extraction (R9) and, where the grammar ships a locals query, `Scope`
   fact extraction (R10).
4. Fixtures: `kotlin/`, `ocaml/`, `haskell/`, `bash/` each contain ≥1
   source file with a documented symbol whose docstring (native
   convention for kotlin/ocaml/haskell; leading-comment for bash) embeds a
   per-fixture sentinel string, plus at least one cross-symbol reference
   and one import/`open`/`source` edge each.
5. Emit `covered: kotlin`, `covered: ocaml`, `covered: haskell`, `covered:
bash` lines on success.
6. Tests per language: reference-extraction (a known reference site
   produces a `Reference` fact) and import-extraction (a known
   import/`open`/`source` produces an `Import` fact).
7. Verify the full language-coverage fixture layout: `context-tree/tests/
fixtures/languages/` now contains exactly the 12 directories named
   `python, typescript, go, rust, java, c, cpp, zig, kotlin, ocaml,
haskell, bash`, each holding ≥1 source file, and `typescript/` holds a
   `.ts`, a `.tsx`, and a `.js` file (from task 02). Write (or extend) an
   integration test asserting this directory layout mechanically (`ls`
   the fixtures dir and assert the exact 12-name set) so a future
   accidental deletion/rename fails loudly.

## Acceptance

- [ ] `cd context-tree && cargo test kotlin` → passes, incl.
      reference/import extraction
- [ ] `cd context-tree && cargo test ocaml` → passes, incl.
      reference/import extraction
- [ ] `cd context-tree && cargo test haskell` → passes, incl.
      reference/import extraction
- [ ] `cd context-tree && cargo test bash` → passes, incl.
      reference/import extraction
- [ ] `ls context-tree/tests/fixtures/languages/ | sort` → exactly
      `bash c cpp go haskell java kotlin ocaml python rust typescript zig`
- [ ] `ls context-tree/tests/fixtures/languages/typescript/` → contains at
      least one file each ending `.ts`, `.tsx`, `.js`
- [ ] `cd context-tree && cargo test 2>&1 | grep -c '^covered: '` → 12 (one
      line per language, exact set matches the 12 names above — a
      hardcoded subset or an extra/misnamed line fails this count or the
      per-language `grep -Fx` checks in tasks 01-03)
- [ ] `bash context-tree/scripts/check.sh` → exits 0
