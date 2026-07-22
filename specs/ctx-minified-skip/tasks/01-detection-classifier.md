# Task 01: Minified detection classifier + index skip storage

Status: in-progress
Depends on: none
Priority: P0
Budget: 24 turns
Spec: ../SPEC.md (requirement R1)
Touch: context-tree/src/minified.rs, context-tree/src/lib.rs, context-tree/src/sync/mod.rs, context-tree/src/index/mod.rs, context-tree/tests/minified.rs

## Goal

At index time, before parsing, each CANDIDATE file (one an
`extract::for_extension` extractor would accept) is classified as
minified-or-not. A classified-minified candidate is recorded in the index
as skipped-with-reason (enum `minified-name` / `minified-content`) and
produces zero symbols; a non-minified candidate parses as before.
Classification is per-file (O(changed files)) and re-runs under the same
staleness rules as parsing.

## Touch

Owns the new detection module `context-tree/src/minified.rs` and the
sync-site + index-schema wiring. Does NOT touch `src/cmd/tree.rs` (task 02
owns tree output), `src/vcs/mod.rs`, or `.ctxkeep` handling (task 03). Leave
the `.ctxkeep` exemption gate as a clearly-marked seam task 03 fills — do
not implement `.ctxkeep` here.

## Steps

1. Write failing unit tests in `tests/minified.rs` pinning the tunable
   constants: name pattern `*.min.js` / `*.min.mjs` → `minified-name`;
   content heuristic → `minified-content` only when file > 50 KB AND
   (avg line length > 400 bytes OR (line count ≤ 5 AND largest line > 50%
   of file bytes)); a `//# sourceMappingURL=` comment may strengthen but
   never suffices alone. Assert the three false-negative-favoring boundaries
   (just-under 50 KB, avg-line 400, 6-line file) classify as NOT minified.
2. Add `src/minified.rs` with a `classify(rel: &str, content: &str) ->
   Option<MinifiedReason>` (or equivalent) implementing the above; register
   it in `src/lib.rs`.
3. Add a skip-with-reason column/table to the index schema in
   `src/index/mod.rs` (reason enum stored; queryable per path), replacing
   facts on re-parse the same way `replace_facts` does so staleness matches
   parsing.
4. At the sync parse site (`src/sync/mod.rs`, the
   `extract::for_extension(ext)` branch ~L179-199): classify the candidate
   first; if minified, record the skip (no `extractor.extract` call, zero
   facts) instead of parsing.
5. Add a sync-level test: a temp repo containing a `*.min.js` yields zero
   symbols for that path after sync, and its skip reason is recorded.

## Acceptance

- [ ] `cd context-tree && cargo test minified` → classifier + boundary
  unit tests pass (constants and all three false-negative boundaries).
- [ ] `cd context-tree && cargo test --test minified` → a synced `*.min.js`
  fixture records reason `minified-name` and yields zero symbols in the index.
- [ ] `bash context-tree/scripts/check.sh` → exits 0 (lint + typecheck +
  tests green).
