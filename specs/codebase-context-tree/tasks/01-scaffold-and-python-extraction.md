# Task 01: Rust scaffold, CLI shell, project init, Python extraction

Status: pending
Depends on: none
Priority: P0
Budget: 45 turns
Spec: ../SPEC.md (requirements R1 partial [python], R18; contracts C1, C2, C4, C8)
Touch: context-tree/Cargo.toml, context-tree/Cargo.lock, context-tree/scripts/check.sh, context-tree/src/**, context-tree/tests/fixtures/languages/python/**, context-tree/tests/*.rs, context-tree/.gitignore

## Goal

`context-tree/` exists as a buildable Rust binary crate (`ctx`); `ctx
--version` runs; `ctx init` scaffolds `.context/{notes,cache}` plus a
managed `.context/.gitignore` per C4 and is idempotent (R18). A
`LanguageExtractor` trait and a per-language registration pattern exist so
later tasks add one new file each without editing a shared dispatch list
more than a single `pub mod` line. The Python extractor produces per-file
symbol facts satisfying R1, keyed by C1 qualified paths and C2 body
hashes, with C8 docstring extraction. `context-tree/scripts/check.sh`
wraps the documented check command (fmt + clippy + test) other tasks and
R17's README will point to.

## Touch

This task owns the crate skeleton, the extraction trait/registry
machinery, and Python only. Do not add other languages' grammar
dependencies or files here — those are tasks 02-04. Do not implement
`ctx sync`, the SQLite index, or any query command — those are tasks 05+.
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
7. Define the `LanguageExtractor` trait (parse a file's bytes -> Vec
   `Symbol` + parse-failed flag) and the registration pattern so a future
   language module is added via one `pub mod <lang>;` line plus its own
   file — no shared match/dispatch table to hand-edit per grammar.
8. Implement the Python extractor: function/method/class definitions, C1
   path using Python's dotted-module convention, C8 docstrings (the
   language's native convention), full/identifier spans, parent
   containment, C2 hash + token set. A file whose root node reports a
   tree-sitter ERROR yields best-effort facts from recoverable subtrees
   and is marked parse-failed.
9. Add `context-tree/tests/fixtures/languages/python/` with at least one
   `.py` file containing nested definitions and one documented symbol whose
   docstring embeds a fixture-local sentinel string.
10. RED/GREEN: extraction tests — a property test that two same-name
    Python overload-shaped definitions (if constructible) or at minimum
    every symbol's C1 path is unique and resolves via suffix matching; a
    rename-only edit test proving C2 hash is unchanged; the docstring
    sentinel test; a parse-failed-file test asserting sibling symbols in a
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
      sentinel, and parse-failed best-effort facts
- [ ] `cd context-tree && cargo test 2>&1 | grep -Fx "covered: python"` →
      line present
- [ ] `bash context-tree/scripts/check.sh` → exits 0
