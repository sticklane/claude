# Task 01: Minified detection classifier + index skip storage

Status: done
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

- [x] `cd context-tree && cargo test minified` → classifier + boundary
  unit tests pass (constants and all three false-negative boundaries).
  Evidence: 11 `minified_classify_*` tests pass (renamed to carry the
  `minified` substring so this filtered command selects them).
- [x] `cd context-tree && cargo test --test minified` → a synced `*.min.js`
  fixture records reason `minified-name` and yields zero symbols in the index.
  Evidence: all 12 tests in `tests/minified.rs` pass, including
  `sync_records_skip_reason_and_yields_zero_symbols_for_min_js`.
- [x] `bash context-tree/scripts/check.sh` → exits 0 (lint + typecheck +
  tests green). Evidence: `cargo fmt --check`, `cargo clippy --all-targets
  -- -D warnings`, and `cargo test` (full suite, all existing tests plus
  the new ones) all passed; exit code 0.

## Decisions

- Decision: criterion (a)'s "average line length" is a trimmed mean —
  computed over all lines EXCLUDING the single longest one — rather than a
  plain whole-file mean. Default taken: implemented the trimmed version
  (documented in `src/minified.rs`'s doc comment on `is_minified_content`).
  Reason: a plain mean is forced above 400 bytes/line for ANY few-line file
  over 50 KB regardless of shape (e.g. 51200 bytes / 6 lines ≈ 8533 avg),
  which would wrongly flag R3's explicit false-positive fixture — many
  ordinary lines plus one embedded >50%-of-bytes literal — since the plain
  mean stays dragged up by that one outlier line no matter how many
  ordinary lines surround it. How to reverse: replace `avg_rest`'s
  exclude-largest computation with `size / line_count.max(1)`; doing so
  will also require reworking or dropping the R3(b) false-positive test
  (`minified_classify_does_not_flag_many_ordinary_lines_with_one_embedded_literal`),
  since a plain mean cannot satisfy that fixture's "must not be skipped"
  requirement for any file actually over the 50 KB threshold.
- Decision: `skip_reason` is a nullable `TEXT` column added directly to the
  existing `files` table (schema bumped 3→4, triggering the existing C4
  transparent-rebuild-on-version-mismatch path) rather than a separate
  table. Default taken: single-column approach. Reason: it is a 1:1
  per-file attribute sharing the file row's exact staleness lifecycle, and
  every read (`skip_reason_for_path`) and write (`set_skip_reason`) is
  already keyed by file/path. How to reverse: extract a `skip_reasons(file_id
  PRIMARY KEY, reason TEXT NOT NULL)` table if a future need arises (e.g.
  tracking skip-reason history) that a single column can't serve.
- Decision: the build procedure's pre-commit review fallback (`/code-review`
  unavailable → one awaited subagent on the diff) could not run as
  specified — this dispatch's toolset exposed no generic subagent-dispatch
  tool (`ToolSearch` for "Agent"/"subagent"/"general-purpose" returned
  none). Default taken: performed the review pass myself, reading the full
  diff directly and checking staleness handling, boundary math, and
  Touch-list conformance by hand; no findings required fixing. How to
  reverse: N/A — re-run `/code-review` or a subagent pass post-merge if a
  subagent-dispatch tool becomes available and a second opinion is wanted.

## Discovered

- None.
