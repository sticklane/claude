# Verification evidence — task 09: notes CRUD, derived freshness, C10 marker wiring

Verdict: **PASS**

Branch: task/09-notes-crud-and-freshness (HEAD 9850dff)
Base commit checked: 141ac69a0c269fae00e8f57462162193f27e24ad

## Acceptance commands (all run from context-tree/)

Command: `export PATH="$HOME/.cargo/bin:$PATH" && cargo test notes_add`
Result: PASS — `test result: ok. 5 passed; 0 failed` (notes_add_writes_frontmatter_and_body,
notes_add_author_unknown_in_no_vcs_fixture, notes_add_author_from_ctx_author_env,
notes_add_records_kind, notes_add_refuses_ambiguous_anchor_exit3)

Command: `cargo test notes_body_sources`
Result: PASS — `1 passed` (notes_body_sources_positional_file_and_stdin)

Command: `cargo test notes_freshness`
Result: PASS — `1 passed` (notes_freshness_flips_stale_on_body_edit)

Command: `cargo test notes_list`
Result: PASS — `1 passed` (notes_list_filters_by_kind_stale_and_file)

Command: `cargo test notes_corrupted_frontmatter`
Result: PASS — `1 passed` (notes_corrupted_frontmatter_is_skipped_with_diagnostic)

Command: `cargo test notes_merge_conflict`
Result: PASS — `1 passed` (notes_merge_conflict_only_on_the_note_file)

Command: `cargo test c10_markers_all_surfaces`
Result: PASS — `1 passed` (c10_markers_all_surfaces_show_fresh_and_stale_note_count)

Command: `cargo test notes_deletion_freshness`
Result: PASS — `1 passed` (notes_deletion_freshness_purges_symbol_and_stales_note)

Command: `bash context-tree/scripts/check.sh`
Result: PASS — exited 0; ran `cargo fmt --check`, `cargo clippy -D warnings`, and full
workspace test suite (all language/notes/index test files green, e.g. typescript 9 passed,
zig 9 passed, notes.rs tests all ok).

## Code-genuineness spot checks

1. **Freshness is derived, not stored as ground truth.**
   `src/notes/freshness.rs::is_fresh(current_body_hash, anchor_hash)` is a pure function:
   `current_body_hash == Some(anchor_hash)`. `src/index/mod.rs::refresh_notes()` recomputes
   this on every sync by looking up each note's anchor's _current_ symbol body hash
   (`current`) via a join against `symbols`, and writes the recomputed `fresh` bit into the
   `notes` cache table — i.e. the cache is a re-derivable projection, not authoritative
   state (matches R12 and the task's stated derivation rule).

2. **`note_marker` genuinely queries the notes table.**
   `src/index/mod.rs:639-664` — resolves the symbol's `qpath`, then
   `SELECT COUNT(*), SUM(CASE WHEN fresh=0...) FROM notes WHERE anchor_path = ?1`, returns
   `None` only when count is 0. Not a stub returning `None` unconditionally.

3. **C10 marker on all four surfaces via one API.**
   `format_note_marker`/`note_marker` calls found in `src/cmd/tree.rs`, `src/cmd/sig.rs`,
   `src/cmd/map.rs`, `src/cmd/at.rs` (plus `refs.rs`, not required here) — all route through
   the single `IndexStore::note_marker` implemented in step 2. Test
   `c10_markers_all_surfaces_show_fresh_and_stale_note_count` adds one fresh note via the CLI
   and one hand-crafted stale note (mismatched anchor_hash) to the same symbol, then asserts
   `[notes:2!]` literally appears in `ctx tree`, `ctx sig`, `ctx map`, and `ctx at` output —
   exercises real command output, not internals.

4. **Ambiguous-anchor add exits 3.**
   `src/cmd/notes.rs:111,115` — prints candidate list to stderr, returns
   `ExitCode::from(EXIT_AMBIGUOUS)` where `EXIT_AMBIGUOUS: u8 = 3` (`src/cmd/mod.rs:23`).
   Exercised by `notes_add_refuses_ambiguous_anchor_exit3`.

5. **Corrupted frontmatter skipped with one diagnostic, query still exits 0.**
   `src/notes/mod.rs::load_all()` returns `(Vec<Note>, Vec<String>)`, pushing one
   diagnostic string per unparseable/incomplete file rather than erroring. `src/sync/mod.rs`
   (`run_sync`) prints one `eprintln!("ctx: skipping note — {reason}")` per diagnostic and
   proceeds to `refresh_notes` unconditionally — a corrupted note file never aborts sync.
   Exercised by `notes_corrupted_frontmatter_is_skipped_with_diagnostic`
   (asserted PASS above).

6. **R14 merge-conflict test is a real git fixture, not a fake.**
   `notes_merge_conflict_only_on_the_note_file` does a real `git init`, two divergent
   branches editing the same note body line, a real `git merge`, and asserts via
   `git diff --name-only --diff-filter=U` that exactly the note file is the sole conflicted
   path. Not vacuous.

7. **Deletion-freshness (R2) test exercises purge + staleness together.**
   `notes_deletion_freshness_purges_symbol_and_stales_note` adds a note, deletes the
   anchored file, runs a sync-triggering query, and asserts (a) the symbol is purged from
   `ctx tree` output, (b) `ctx sig` exits 1 (not found), and (c) `ctx notes list --stale`
   picks up the now-stale note. Real end-to-end CLI assertions, not internal-state pokes.

None of the eight test bodies special-case literal fixture strings beyond what's needed to
set up realistic scenarios (symbol names, file paths); each asserts CLI-observable
behavior (exit codes, stdout content, git conflict state) rather than "runs without error."

## Task-file append-only check

Command: `git diff 141ac69a0c269fae00e8f57462162193f27e24ad -- 'specs/codebase-context-tree/tasks/*.md'`

Only diff across all task files: the 09 task file gained a `<!-- PLAN (delete at
close-out): ... -->` HTML comment block after the header fields (lines 10-25). No other
task file changed. Status line (`Status: in-progress`) and all eight acceptance checkboxes
(`- [ ]`) are byte-identical to the base — none were ticked and Status was not flipped to
`done`/`review` despite the implementation being present and all commands passing. This is
not a violation of append-only (nothing outside the allowed set — Status flip, checkbox
ticks, evidence lines, plan comment block — was touched; the PLAN comment is explicitly
allowed), but it does mean the task file's own bookkeeping was left incomplete by whatever
process produced this branch. Flagging as a process finding, not an acceptance failure.

## Scope / Touch-list check

`git diff --stat 141ac69a0c269fae00e8f57462162193f27e24ad HEAD -- context-tree/`:

```
context-tree/src/cli.rs             |  84 ++++-
context-tree/src/cmd/mod.rs         |   1 +
context-tree/src/cmd/notes.rs       | 250 +++++++++++++++
context-tree/src/index/mod.rs       | 139 ++++++++-
context-tree/src/lib.rs             |  52 ++++
context-tree/src/notes/anchor.rs    |  35 +++
context-tree/src/notes/freshness.rs |  32 ++
context-tree/src/notes/mod.rs       | 267 ++++++++++++++++
context-tree/src/sync/mod.rs        |   9 +
context-tree/tests/notes.rs         | 591 ++++++++++++++++++++++++++++++++++++
```

No file outside `context-tree/` changed except the task file itself (see above). Touch
declared: `src/notes/mod.rs, src/notes/anchor.rs, src/notes/freshness.rs, src/cmd/notes.rs,
src/index/**, src/cli.rs, Cargo.toml, tests/fixtures/notes/**, tests/*.rs`.

- `Cargo.toml` and `tests/fixtures/notes/**` are in Touch but were not modified — fine
  (Touch is a ceiling, not a requirement).
- `src/lib.rs`, `src/cmd/mod.rs`, `src/sync/mod.rs` were changed but are **not** in the
  declared Touch list. The task's own PLAN comment pre-declares this ("Wiring (additive,
  beyond declared Touch — reversible, reported in Decisions): lib.rs (pub mod notes; Notes
  match arm), cmd/mod.rs (pub mod notes;), sync/mod.rs (notes refresh call), cli.rs (Notes
  subcommand)"), and the diffs are exactly that: `pub mod notes;` + a `Notes` match arm in
  `lib.rs`'s command dispatch, `pub mod notes;` in `cmd/mod.rs`, and a notes-refresh call
  in `sync/mod.rs`. This is minimal, necessary wiring to make the declared `cli.rs`
  subcommand actually dispatch and the declared `src/index/**` cache actually get
  refreshed — not unrelated scope creep. However, the PLAN's own promise to report this
  "in Decisions" was not fulfilled: no `## Decisions` section exists anywhere in the task
  file. Flagging as a minor process gap, not a functional problem — the wiring itself is
  correct, tested, and necessary for the feature to work at all.

## Verdict

PASS. All 8 acceptance test commands pass with real, non-vacuous assertions; `scripts/check.sh`
exits 0 (fmt, clippy -D warnings, full test suite green); freshness is genuinely derived;
`note_marker` genuinely queries the notes table; C10 wiring is real and shared across all
four surfaces; ambiguous-add exits 3; corrupted frontmatter is skipped with one diagnostic
and sync/query still succeeds; R14 merge-conflict and R2 deletion-freshness are exercised by
real git/file-system scenarios. Findings are process-only (task file bookkeeping left
unfinished; a promised "Decisions" note for the beyond-Touch wiring was never written) and
do not affect functional correctness.
