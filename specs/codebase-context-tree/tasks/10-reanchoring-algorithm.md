# Task 10: Deterministic layered re-anchoring, two-phase persistence

Status: done
Depends on: 09
Priority: P1
Budget: 55 turns
Spec: ../SPEC.md (requirement R13; contracts C1, C2, C5)
Touch: context-tree/src/notes/reanchor.rs, context-tree/src/sync/**, context-tree/src/index/**, context-tree/src/cli.rs, context-tree/Cargo.toml, context-tree/tests/fixtures/reanchor/**, context-tree/tests/*.rs

## Goal

When an anchored symbol no longer resolves, sync re-anchors deterministically
and in layer order: (1) qualified-name match — a unique definition sharing
the anchor's terminal name and kind among the changed files' new symbols
(zero or multiple candidates falls through to the next layer); (2)
body-hash match (C2); (3) tree-diff matching — same-kind candidates in the
changed files' new trees, scored by token overlap between identifier-excised
body texts (C2's byte basis, reading the R1-persisted token set), re-anchoring
to the highest-scoring candidate above threshold 0.6, ties broken by lowest
file:line, otherwise the note stays un-re-anchored and stale. Re-anchoring
fires only at the sync that observes the disappearance (a full index rebuild
after the anchor vanished unsynced leaves it un-re-anchorable). Persistence
is two-phase: phase 1 (every sync) records the re-anchor in the index
immediately so queries see it at once; phase 2 (only at an explicit
persistence point — `ctx sync --write-anchors`, or the pre-commit hook from
task 12) writes the new anchor PATH into the note file's frontmatter — the
only write the system ever makes to a note file. The anchor HASH is never
system-written after creation. Pending unwritten anchor updates are named
in `ctx notes list` output and in the C5 journal's `pending_reanchors`
count (this task makes that field real; task 05 stubbed it at 0).
Re-anchoring never fires against a parse-failed file's symbols — they are
unresolved-transient, not vanished.

## Touch

Owns the re-anchoring algorithm and its integration into the sync pipeline
(hooking into `src/sync/` after task 05's scan/parse phases) plus the
`--write-anchors` flag. Do not touch `src/notes/anchor.rs` /
`src/notes/freshness.rs` (task 09) beyond adding calls into them — their
existing CRUD/derivation behavior must not change.

## Steps

1. RED/GREEN leg (a) — rename a function in-file: sync's next run
   re-anchors via qualified-name match; `ctx notes` shows the re-anchored
   note immediately (index/phase-1), derived freshness reads fresh, and
   the note FILE is unchanged until a persistence point.
2. RED/GREEN leg (b) — edit the function body (no rename/move): freshness
   reads stale with a pointer to what changed; note file unchanged.
3. RED/GREEN leg (c) — move a function to a different file, rename it, AND
   make a small body edit in the same sync: note re-anchors via tree-diff
   (score > 0.6 in the fixture) and freshness reads stale. After leg (c)
   and before any persistence point, assert the latest journal record
   shows `pending_reanchors >= 1`.
4. RED/GREEN leg (d) — move a function to another file WITHOUT rename or
   edit, in a file-is-module language (a C fixture, from task 03 — the C1
   module component changes with the file): re-anchors via qualified-name
   match (layer 1), freshness fresh. Contrast fixture: the same move in a
   Go fixture (module = package, from task 02) leaves the anchor path
   unchanged with NO pending write — identity survives via the package
   component and only the query-reported file:line updates.
5. RED/GREEN: `ctx sync --write-anchors` — after legs (d)/(a)/(c), running
   it writes the re-anchored paths into frontmatter, and a subsequent sync
   journals `pending_reanchors == 0`.
6. Durability tests: delete `.context/cache/` and re-sync (rebuild
   durability); separately, clone the fixture to a fresh directory and
   sync there (clone durability). In both, leg (c)'s note resolves to the
   new symbol and reads stale (the anchor path survived because it was
   persisted; the hash was never system-written, so staleness from the
   body edit still shows).
7. Parse-failed exclusion test: a symbol in a file with a mid-function
   syntax error is "unresolved-transient," not "vanished" — assert no
   re-anchoring attempt fires against it (its anchor binding is untouched)
   and its note's freshness re-derives fresh once the file parses again on
   a later sync.
8. Threshold/tie-break unit tests for the tree-diff scorer directly (score
   computation, 0.6 threshold, lowest-file:line tie-break) independent of
   the fixture legs above.
9. Invariant test: throughout every leg, the system's only note-file write
   is the anchor path at a persistence point — bodies are never modified,
   files are never deleted, and query-triggered/background syncs (i.e.
   without `--write-anchors` and without the task-12 pre-commit hook)
   leave tracked note files byte-identical.

## Acceptance

- [x] `cd context-tree && cargo test reanchor_rename_in_file` → passes (leg a)
      — verifier: 1 test ran, PASS (rename fresh + note file unchanged).
- [x] `cd context-tree && cargo test reanchor_body_edit` → passes (leg b)
      — verifier: 1 test ran, PASS (stale, anchor unchanged, pending 0).
- [x] `cd context-tree && cargo test reanchor_move_rename_edit` → passes
      (leg c, `pending_reanchors >= 1` before persistence) — verifier: 1 test, PASS.
- [x] `cd context-tree && cargo test reanchor_move_no_edit` → passes (leg
      d, C-fixture re-anchors / Go-fixture identity-stable contrast)
      — verifier: 1 test, PASS (C re-anchors; Go `pending==0`).
- [x] `cd context-tree && cargo test write_anchors` → passes
      (`--write-anchors` persists; subsequent `pending_reanchors == 0`)
      — verifier: 1 test, PASS.
- [x] `cd context-tree && cargo test reanchor_durability` → passes (cache
      rebuild and fresh-clone durability for leg c) — verifier: 1 test, PASS.
- [x] `cd context-tree && cargo test reanchor_parse_failed_excluded` →
      passes (no re-anchor attempt against a parse-failed file's symbols;
      fresh on repair) — verifier: 1 test, PASS.
- [x] `cd context-tree && cargo test tree_diff_scorer` → passes (threshold
      0.6, lowest-file:line tie-break, unit-level) — verifier: 13 unit tests, PASS.
- [x] `cd context-tree && cargo test reanchor_only_writes_anchor_path` →
      passes (bodies/files untouched; query/background syncs don't write)
      — verifier: 1 test, PASS (line-by-line: only anchor_path changed).
- [x] `bash context-tree/scripts/check.sh` → exits 0 — verified exit 0
      (fmt + clippy -D warnings + full suite green).
