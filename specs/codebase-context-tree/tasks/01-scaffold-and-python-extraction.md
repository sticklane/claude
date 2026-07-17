# Task 01: Rust scaffold, CLI shell, project init, Python extraction

Status: pending
Depends on: none
Priority: P0
Budget: 60 turns
Spec: ../SPEC.md (requirements R1 partial [python], R9, R10 partial, R18; contracts C1, C2, C4, C8)
Touch: context-tree/Cargo.toml, context-tree/Cargo.lock, context-tree/scripts/check.sh, context-tree/src/**, context-tree/tests/fixtures/languages/python/**, context-tree/tests/*.rs, context-tree/.gitignore

## Goal

`context-tree/` exists as a buildable Rust binary crate (`ctx`); `ctx
--version` runs; `ctx init` scaffolds `.context/{notes,cache}` plus a
managed `.context/.gitignore` per C4 and is idempotent (R18). A
`LanguageExtractor` trait and a per-language registration pattern exist so
later tasks add one new file each without editing a shared dispatch list
more than a single `pub mod` line. The Python extractor produces per-file
symbol facts satisfying R1, keyed by C1 qualified paths and C2 body
hashes, with C8 docstring extraction. Per R1, extraction also produces
reference occurrences (name + location + kind: call/read/etc) and
module-level import edges (R9's raw material) alongside definitions, plus
`@local.scope`/`@local.definition` locals-query scope data where
tree-sitter-python's grammar provides it (R10's scope-aware requirement) —
this is extraction-time work so that query commands (tasks 06/07) only
ever read from the index, never re-parse source. `context-tree/
scripts/check.sh` wraps the documented check command (fmt + clippy + test)
other tasks and R17's README will point to.

## Touch

This task owns the crate skeleton, the extraction trait/registry
machinery (including the `Reference`/`Import` fact types and the locals-
query scope-analysis shape later language tasks reuse), and Python only.
Do not add other languages' grammar dependencies or files here — those are
tasks 02-04. Do not implement `ctx sync`, the SQLite index, or any query
command — those are tasks 05+ (reference/import facts are produced and
held in-memory/tested here; task 05 is what persists them to the index).
`ctx init` here only scaffolds `.context/`; it does not need to know about
languages.

## Steps

1. `cargo new --bin context-tree` (or workspace equivalent); add
   dependencies: `tree-sitter`, `tree-sitter-python`, `tree-sitter-language`
   (ABI shim), a CLI-parsing crate (e.g. `clap`), `sha2` (C2 hashing),
   `insta` (snapshot tests, dev-dependency), and a registration mechanism
   (e.g. `inventory`) for per-language extractors.
2. RED: write a failing integration test asserting `ctx --version` exits 0
   and prints a version string. Run it, confirm it fails (binary/flag
   doesn't exist).
3. GREEN: implement the CLI entry point and `--version` flag.
4. RED: write a failing test that `ctx init` in an empty temp dir creates
   `.context/notes/` (empty, ready for VCS tracking), `.context/cache/`
   (empty), and a `.context/.gitignore` ignoring `cache/`; running `ctx
init` a second time changes nothing and exits 0.
5. GREEN: implement C4 project-root discovery (nearest ancestor containing
   `.context/`; only `ctx init` itself falls back to the git-root adapter to
   decide where to scaffold when no `.context/` exists yet) and `ctx init`.
6. Define the `Symbol` fact type: kind (small closed enum), name, C1
   qualified path, signature text, docstring (C8), full span + identifier
   span (line:col), parent containment, C2 body content hash, and the
   identifier-excised body token set (tokenized, for R13's later tree-diff
   scoring — persist the token set even though nothing consumes it yet).
   Implement the C1 path builder (`.`-joined, `#<n>` ordinal suffix only
   when a module has multiple same-path definitions) and the C2 hash
   function (SHA-256 over full-span bytes with the identifier span excised).
   Also define two new fact types R1 requires alongside `Symbol`: a
   `Reference` fact (name, location, kind: call/read/etc — the occurrence,
   not the definition) and an `Import` fact (module-level import edge:
   source path, imported module/symbol, location) — R9's `ctx deps` and
   R10's `ctx refs` read these from the index rather than re-parsing source
   at query time (the spec's O(what-was-asked) query-cost rule). Define a
   `Scope` fact shape for locals-query results (`@local.scope`/
   `@local.definition` bindings, per file) that R10's scope-aware `ctx
refs` will consume — populated only for grammars that ship locals
   queries; languages without one simply produce no `Scope` facts.
7. Define the `LanguageExtractor` trait (parse a file's bytes and return
   `Symbol`s, `Reference`s, `Import`s, `Scope` facts, and a parse-failed
   flag) and the registration pattern so a future language module is added
   via one `pub mod <lang>;` line plus its own file — no shared
   match/dispatch table to hand-edit per grammar.
8. Implement the Python extractor: function/method/class definitions, C1
   path using Python's dotted-module convention, C8 docstrings (the
   language's native convention), full/identifier spans, parent
   containment, C2 hash + token set. Also extract: reference occurrences
   (name lookups/calls with kind and location), module-level `import`/
   `from ... import` edges, and — since tree-sitter-python ships a locals
   query — `@local.scope`/`@local.definition` scope facts so a
   function-local variable can be told apart from a same-named global
   reference. A file whose root node reports a tree-sitter ERROR yields
   best-effort facts from recoverable subtrees and is marked parse-failed.
9. Add `context-tree/tests/fixtures/languages/python/` with at least one
   `.py` file containing nested definitions, at least one cross-symbol
   call/reference, at least one `import` statement, a function-local
   variable that shadows a global name (for the locals-query test), and one
   documented symbol whose docstring embeds a fixture-local sentinel
   string.
10. RED/GREEN: extraction tests — a property test that two same-name
    Python overload-shaped definitions (if constructible) or at minimum
    every symbol's C1 path is unique and resolves via suffix matching; a
    rename-only edit test proving C2 hash is unchanged; the docstring
    sentinel test; a reference-extraction test asserting a known call site
    produces a `Reference` fact with the right name/location/kind; an
    import-extraction test asserting a known `import` statement produces
    an `Import` fact; a locals-query test asserting the function-local
    shadowing variable produces a `Scope` fact that distinguishes it from
    the global of the same name; a parse-failed-file test asserting sibling symbols in a
    file with a mid-function syntax error still extract.
11. Make the test suite print one `covered: python` line during this run
    (e.g. each language integration test module logs
    `println!("covered: python")` on success) so the mechanical
    language-coverage acceptance criterion (task 04) can grep it.
12. Write `context-tree/scripts/check.sh`: `cargo fmt --check && cargo
clippy -- -D warnings && cargo test`, executable.

## Acceptance

- [ ] `cd context-tree && cargo build --release` → exits 0, produces
      `target/release/ctx`
- [ ] `./context-tree/target/release/ctx --version` → exits 0, stdout
      contains a version string
- [ ] `cd context-tree && cargo test init_` → passes; asserts `.context/`
      layout per C4 and idempotent re-run
- [ ] `cd context-tree && cargo test python` → passes, covering C1 path
      uniqueness/resolution, C2 rename-hash-stability, C8 docstring
      sentinel, reference extraction (`Reference` facts at known call
      sites), import extraction (`Import` facts for known `import`
      statements), locals-query scope facts (a function-local shadowing
      variable distinguished from the same-named global), and
      parse-failed best-effort facts
- [ ] `cd context-tree && cargo test 2>&1 | grep -Fx "covered: python"` →
      line present
- [ ] `bash context-tree/scripts/check.sh` → exits 0
