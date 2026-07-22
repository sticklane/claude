# Task 02: Tree `(skipped: minified)` marker + zero-symbol queries

Status: pending
Depends on: 01
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirement R2)
Touch: context-tree/src/cmd/tree.rs, context-tree/src/index/mod.rs, context-tree/tests/tree_minified.rs

## Goal

`ctx tree <dir>` lists minified-skipped CANDIDATES with a
`(skipped: minified)` marker — a NEW file-level output class. Symbol-bearing
files render as today; non-candidate files (.md, .json, .css, sourcemaps)
remain omitted. `map`/`refs`/`sig` continue to show none of a skipped file's
symbols (already true once task 01 records zero facts — this task asserts it
with a regression test, it does not re-implement skipping).

## Touch

Owns tree rendering (`src/cmd/tree.rs`) and any read-only query added to
`src/index/mod.rs` to enumerate skipped candidates for a scope. Does NOT
touch `src/minified.rs`, `src/sync/mod.rs`, or `src/vcs/mod.rs`. The index
skip-storage schema is task 01's — only add a reader here, never alter the
write path.

## Steps

1. Write a failing test in `tests/tree_minified.rs`: a fixture dir with a
   `*.min.js` (skipped), a normal `.rs` (symbol-bearing), and a `.md`
   (non-candidate). Assert `ctx tree <dir>` shows the `.min.js` with
   `(skipped: minified)`, shows the `.rs` normally, and does NOT list the
   `.md`.
2. Add an index reader in `src/index/mod.rs` returning skipped candidates
   (path + reason) within a scope.
3. In `src/cmd/tree.rs` (`render` / `render_files`), interleave skipped
   candidates into the listing with the marker; keep non-candidates omitted.
   Mirror the marker into the JSON output path if tree has one.
4. Add a regression test asserting `ctx map`/`ctx refs`/`ctx sig` return
   none of the skipped file's symbols.

## Acceptance

- [ ] `cd context-tree && cargo test --test tree_minified` → tree shows the
  `.min.js` with `(skipped: minified)`, shows the `.rs`, omits the `.md`.
- [ ] `cd context-tree && cargo test tree_minified` (unit/regression) →
  `map`/`refs`/`sig` return zero symbols for the skipped path.
- [ ] `bash context-tree/scripts/check.sh` → exits 0.
