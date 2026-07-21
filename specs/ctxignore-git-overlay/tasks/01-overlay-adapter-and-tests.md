# Task 01: `.ctxignore` overlay adapter in `detect()` + full test suite

Status: pending
Depends on: none
Priority: P1
Budget: 24 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4, R5)
Touch: context-tree/src/vcs/mod.rs, context-tree/src/sync/mod.rs, context-tree/tests/sync.rs, context-tree/tests/query_edges.rs, context-tree/tests/notes.rs, context-tree/tests/fixtures/

## Goal

`detect()` (context-tree/src/vcs/mod.rs:48) returns every non-baseline
adapter wrapped in a `.ctxignore` exclusion overlay built on the existing
`load_ctxignore`/`ctxignore_matches` pair: file lists subtract overlay
matches, composed `is_ignored` ORs the overlay in, and all other
`VcsAdapter` methods (`name`, `change_feed`, `snapshot_id`,
`user_identity`, `hook_dir`) delegate verbatim to the inner adapter.
`NoVcsBaseline` is returned unwrapped (it already applies `.ctxignore`
internally). Eight new behavioral tests prove the overlay end to end.

## Touch

All Rust work stays inside `context-tree/`. Do NOT touch
`context-tree/README.md`, any `SKILL.md`, `plugin.json`, or
`specs/codebase-context-tree/SPEC.md` — those are task 02's charter. New
test fixtures go under `context-tree/tests/fixtures/` following the
existing fixture conventions; test functions may be added to the existing
test files listed in `Touch:` or one new `context-tree/tests/ctxignore_overlay.rs`
(also permitted under the fixtures path grant — if a new test file is
cleaner, add `context-tree/tests/ctxignore_overlay.rs` and note it in the
completion report).

## Steps

1. Read `../SPEC.md` in full, then `context-tree/src/vcs/mod.rs` (the
   `VcsAdapter` trait, `detect()`, `GitAdapter`, `NoVcsBaseline`,
   `load_ctxignore`, `ctxignore_matches`) and the sweep membership logic
   in `context-tree/src/sync/mod.rs` (list_files → present → deletion
   detection).
2. RED: write the failing tests first, using the exact names in
   `## Acceptance` (they are the spec's anchored criteria — grep count 0
   at authoring time). Git-fixture tests need a real `git init` +
   `git add`/commit of a `dist/` twin of a `src/` symbol, plus
   `git config user.email` for the author test.
3. GREEN: implement the overlay wrapper; wire it in `detect()` around
   the non-baseline arm only. Subtractive-only by construction — the
   overlay never adds paths, so R2 needs no special casing beyond the
   existing matcher.
4. REFACTOR with tests green; run the component gate.

## Acceptance

- [ ] `cd context-tree && cargo test ctxignore_overlay` → passes and the
      suite contains these exact test names (L2 behavioral, per
      SPEC.md's Acceptance):
      `ctxignore_overlay_excludes_committed_paths_under_git`,
      `ctxignore_overlay_cannot_reinclude_gitignored`,
      `ctxignore_overlay_edit_takes_effect_on_next_query`,
      `ctxignore_overlay_absent_file_changes_nothing`,
      `ctxignore_overlay_baseline_list_unchanged`,
      `ctxignore_overlay_note_goes_stale_not_reanchored`,
      `ctxignore_overlay_git_note_author_preserved`,
      `ctxignore_overlay_at_excluded_file_exits_4`
- [ ] `cd context-tree && cargo test ignore_rules` → passes unchanged
      (R3/R5 no-VCS baseline regression gate)
- [ ] `cd context-tree && cargo test` → full suite green (no collateral
      regressions in query/notes/reanchor suites)
- [ ] `bash context-tree/scripts/check.sh` → green (fmt, clippy, tests)
