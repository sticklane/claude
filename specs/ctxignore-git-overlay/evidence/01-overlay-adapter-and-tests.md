# Verification: Task 01 — overlay adapter and tests

Verdict: PASS

## Per-criterion

1. ✓ `cd context-tree && cargo test ctxignore_overlay`
   All 8 exact test names present (verified via
   `grep -n "fn ctxignore_overlay_" tests/ctxignore_overlay.rs`) and match the
   task's list exactly:
   `ctxignore_overlay_excludes_committed_paths_under_git`,
   `ctxignore_overlay_cannot_reinclude_gitignored`,
   `ctxignore_overlay_edit_takes_effect_on_next_query`,
   `ctxignore_overlay_absent_file_changes_nothing`,
   `ctxignore_overlay_baseline_list_unchanged`,
   `ctxignore_overlay_note_goes_stale_not_reanchored`,
   `ctxignore_overlay_git_note_author_preserved`,
   `ctxignore_overlay_at_excluded_file_exits_4`.
   Output: `running 8 tests ... test result: ok. 8 passed; 0 failed; 0 ignored;
0 measured; 0 filtered out; finished in 1.83s`. Depth: L2 behavioral.

2. ✓ `cd context-tree && cargo test ignore_rules`
   Output: `running 2 tests ... test ignore_rules_ctxignore_excludes_in_baseline
... ok / test ignore_rules_exclude_gitignored_and_context_cache ... ok /
test result: ok. 2 passed; 0 failed`. Unchanged from pre-existing behavior
   (2 tests, same names). Depth: L2 behavioral.

3. ✓ `cd context-tree && cargo test` (full suite)
   All suites green across query_edges, reanchor, rust, sync (9 tests incl.
   the 2 ignore_rules tests), typescript, zig, doc-tests. Confirmed no
   failures with `cargo test 2>&1 | grep -E "FAILED|error\[|^error"` → no
   matches. Depth: L2/L3 (integration-level, real git fixtures used in
   sync/ignore tests).

4. ✓ `PATH="$HOME/.cargo/bin:$PATH" bash context-tree/scripts/check.sh`
   Exit code 0 (fmt, clippy, full test suite all green, no warnings/errors
   surfaced). Depth: L2.

## Implementation vs Goal (src/vcs/mod.rs read directly)

`detect()` (lines 51-59): wraps the git arm only —
`Box::new(CtxignoreOverlay { inner: Box::new(GitAdapter) })` — and returns
`NoVcsBaseline` unwrapped when no `.git` root is found. Matches Goal (a).

`CtxignoreOverlay` (lines 67-102):

- `list_files` (76-81): calls `self.inner.list_files(root)?` then
  `files.retain(|rel| !ctxignore_matches(&patterns, rel))` — subtracts
  overlay matches. Matches.
- `is_ignored` (83-85): `self.inner.is_ignored(root, rel) ||
ctxignore_matches(&load_ctxignore(root), rel)` — ORs the overlay in.
  Matches.
- `name` (72-74): `self.inner.name()` — delegates verbatim.
- `change_feed` (87-89): `self.inner.change_feed(root)` — delegates verbatim.
- `snapshot_id` (91-93): `self.inner.snapshot_id(root)` — delegates verbatim.
- `user_identity` (95-97): `self.inner.user_identity(root)` — delegates
  verbatim.
- `hook_dir` (99-101): `self.inner.hook_dir(root)` — delegates verbatim.

No method fails to delegate. Goal (a) and (b) both satisfied.

## Append-only task-file check

`git diff 2fd603c99f5e4f5e758b0c07fb0fe0af6e30eccd -- specs/ctxignore-git-overlay/tasks/01-overlay-adapter-and-tests.md`
shows exactly one hunk: insertion of the `<!-- PLAN (build step 1) ... -->`
comment block after the header fields. No deletion of any line; Goal, Touch,
Steps, Budget, and Acceptance sections are byte-identical to base. Status
line was already `in-progress` at base commit (confirmed via `git show
<base>:...` — unchanged). This is an allowed additive edit (plan comment
block); no criterion text was touched.

## Touch scope check

`git diff --name-only 2fd603c99f5e4f5e758b0c07fb0fe0af6e30eccd` →

- `context-tree/src/vcs/mod.rs` (in Touch)
- `context-tree/tests/ctxignore_overlay.rs` (new file, explicitly permitted
  by the task's Touch note under the fixtures/new-test-file grant)
- `specs/ctxignore-git-overlay/tasks/01-overlay-adapter-and-tests.md` (task
  file itself, additive plan block only)

No files outside Touch scope were modified. No scope creep found.

## Gates

`bash context-tree/scripts/check.sh` → exit 0 (fmt, clippy, tests all
green).

## Criteria-adequacy

All four acceptance criteria are L2 behavioral (actual `cargo test` /
`check.sh` runs producing pass/fail verdicts over real git fixtures, not
mere text-presence). The 8 named tests directly exercise R1-R5's stated
behaviors (committed-path exclusion, non-reinclusion of gitignored paths,
lazy-sync staleness, absent-file no-op, baseline byte-identical list, note
staleness without reanchor, author delegation, `ctx at` exit code). This
entails the Goal's behavioral requirements at L2; no L0/L1-only evidence
gaps found for this task's scope (R6/R7 doc/version criteria belong to
task 02, not this task).
