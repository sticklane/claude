# Verification: Task 05 — Sync engine, SQLite index, ignore rules, VCS adapter

Verdict: **PASS**

Branch: `task/05-sync-and-index-engine`
Worktree: `/Users/sjaconette/claude/.claude/worktrees/agent-ac30f38afdf297f27`
Base commit for append-only check: `b67c3726a616e5c8392edb7707582b95590fe545`

## Acceptance criteria (all commands run in `context-tree/`, `PATH` prefixed with `$HOME/.cargo/bin`)

1. `cargo test sync_incremental` → **PASS**
   - `test sync_incremental_reparses_only_changed_content ... ok`
   - `test sync_incremental_cli_stats_reports_parsed_and_hashed ... ok`
   - `test result: ok. 2 passed; 0 failed`

2. `cargo test sync_deletion` → **PASS**
   - `test sync_deletion_purges_removed_file_facts ... ok`
   - `test result: ok. 1 passed; 0 failed`

3. `cargo test sync_journal` → **PASS**
   - `test sync_journal_appends_one_c5_record_per_sync ... ok`
   - `test result: ok. 1 passed; 0 failed`

4. `cargo test sync_references_imports` → **PASS**
   - `test sync_references_imports_persisted_without_duplication ... ok`
   - `test result: ok. 1 passed; 0 failed`

5. `cargo test sync_concurrency` → **PASS**
   - `test sync_concurrency_query_skips_sweep_under_held_lock ... ok`
   - `test result: ok. 1 passed; 0 failed`

6. `cargo test ignore_rules` → **PASS**
   - `test ignore_rules_ctxignore_excludes_in_baseline ... ok`
   - `test ignore_rules_exclude_gitignored_and_context_cache ... ok`
   - `test result: ok. 2 passed; 0 failed`

7. `cargo test no_vcs_baseline` → **PASS**
   - `test no_vcs_baseline_builds_and_syncs_without_git ... ok`
   - `test result: ok. 1 passed; 0 failed`

8. `bash scripts/check.sh` → **PASS**, exit code 0.
   - Runs `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`.
   - Full workspace test suite (all lang extractors + sync/index/vcs) green: 0 failures across
     all `*.rs` integration test binaries and unit tests observed in output.
   - Re-ran `cargo test --test sync` 3x sequentially (`--test-threads=1`) to probe for
     mtime/racy-guard flakiness — all 9 sync tests passed all 3 runs, no flakes observed.

All 7 named test-filter criteria plus the check.sh gate are exercised and green. (Note: the
task file's own `## Acceptance` checkboxes are unticked and `Status: in-progress` — the
implementation is functionally complete and all named tests pass, but the task file was not
updated to reflect completion. This is an observation, not an acceptance failure, since I was
asked to verify the commands, which all pass.)

## Correctness concerns (from the task prompt)

1. **Incremental scan re-parses only changed files** — Confirmed by reading
   `context-tree/src/sync/mod.rs`: candidacy is `size != size || mtime != mtime || racy(...)`;
   candidates are content-hashed; only a hash mismatch triggers `extractor.extract` (parse).
   A pure mtime bump with unchanged bytes hits the `prior.hash == file_hash` branch, calls
   `touch_file_meta` (no parse). The racy-edit guard (`GRANULARITY_NS = 100ms`) re-hashes (not
   re-parses) files whose mtime sits within 100ms of the last sync's timestamp — this only
   forces an extra _hash_, never skips a needed parse, so it is safe by construction, not
   racy. Test fixtures use `PAST = 250ms` sleeps, comfortably outside the guard window. Ran the
   sync test binary 3x sequentially with no flakes.

2. **Deletion purges all fact tables** — `IndexStore::delete_file` (`src/index/mod.rs:300-317`)
   deletes from `symbols`, `refs`, `imports`, `scopes`, then `files`, keyed by `file_id`/`id`.
   Confirmed correct — this is not just the file row.

3. **Reference/Import facts persisted, queryable, replace-not-accumulate** — `replace_facts`
   (`src/index/mod.rs:217-296`) deletes existing `symbols`/`refs`/`imports`/`scopes` rows for
   `file_id` before inserting the fresh extraction, so a re-parse cannot duplicate rows. Test
   `sync_references_imports_persisted_without_duplication` exercises exactly this: syncs, reads
   counts, edits the file (non-import-changing edit), re-syncs, and asserts the import count is
   unchanged (not doubled).

4. **C5 journal record fields** — `journal::append` writes
   `{timestamp, trigger, scanned, hashed, parsed, pending_reanchors}` as one JSON line per sync.
   `timestamp` is a hand-rolled UTC RFC3339 string ending in `Z` (verified via unit tests
   `format_rfc3339_renders_a_known_epoch`/`_time_of_day`, which ran green under check.sh).
   `pending_reanchors` is stubbed to 0 as specified (task 10 populates it later). All fields
   confirmed present by the `sync_journal_appends_one_c5_record_per_sync` test which parses
   each line as JSON and asserts every field.

5. **Query under held lock skips sweep, serves last snapshot, bounded time** — `query_sweep`
   (`src/sync/mod.rs:179-187`) uses `AdvisoryLock::try_acquire` (non-blocking); if the lock is
   already held it does NOT call `run_sync` (so no new journal record), and just opens the
   store to read the last-completed snapshot. Test asserts elapsed < 500ms, journal line count
   unchanged, and `total_symbols() >= 1` (last snapshot served). Confirmed correct — the query
   path never blocks on the lock.

6. **`.gitignore`/`.ctxignore`/`.context/cache` exclusion** — `GitAdapter::list_files` uses
   `git ls-files --cached --others --exclude-standard` (git-native gitignore handling);
   `NoVcsBaseline::list_files` walks the tree applying `.ctxignore` patterns via a small
   glob matcher. Both `sync::run_sync` and the baseline `walk()` additionally hard-exclude the
   `.context` dir name / `CONTEXT_DIR` prefix independent of any ignore file. Confirmed by
   reading `src/vcs/mod.rs` and the two `ignore_rules_*` tests, both green.

7. **`note_marker` returns `None`** — `IndexStore::note_marker(&self, _symbol_id: i64) ->
Option<(usize, bool)> { None }` (`src/index/mod.rs:382-384`), with a unit test
   `note_marker_returns_none_when_no_notes_exist` asserting `None` for two different ids.
   Confirmed correct per spec.

8. **Touch scope** — `git diff b67c3726a6.. --stat -- context-tree/` shows changes in:
   `Cargo.lock`, `Cargo.toml`, `src/cli.rs`, `src/index/mod.rs`, `src/lib.rs`,
   `src/sync/journal.rs`, `src/sync/lock.rs`, `src/sync/mod.rs`, `src/vcs/mod.rs`,
   `tests/sync.rs`. No changes under `src/lang/**` or `src/cmd/**` (both correctly out of
   scope). `Cargo.lock` is an automatic side effect of the `Cargo.toml` edit (adding
   `rusqlite`/`sha2`/`tempfile` deps) and is not separately Touch-listed but is standard/
   expected fallout, not a scope violation.
   **Finding (minor):** `src/cli.rs` (+6 lines: new `Sync { stats }` subcommand variant) and
   `src/lib.rs` (+33 lines: dispatch wiring for `ctx sync`/`ctx sync --stats`) are edited but
   are **not** in the task's literal `Touch:` list
   (`context-tree/src/sync/**, src/index/**, src/vcs/**, Cargo.toml, tests/fixtures/sync/**,
tests/*.rs`). This wiring is necessary — the task's own Goal states "`ctx sync` exists" and
   one of the acceptance-adjacent tests (`sync_incremental_cli_stats_reports_parsed_and_hashed`)
   invokes the `ctx` binary directly with `sync --stats` — so the CLI entry point had to be
   added somewhere, and `cli.rs`/`lib.rs` are the only place for it (not owned by another task
   per the Touch note, which reserves `src/cmd/**` for tasks 06/07, a directory that does not
   yet exist). This reads as a Touch-list omission in the task's authoring rather than
   unauthorized scope creep, but it is reported per the verification protocol.
   Task-file append-only check: `git diff b67c3726a6.. -- 'specs/codebase-context-tree/tasks/*.md'`
   is **empty** — the task file at HEAD is byte-identical to the base commit (Status still
   `in-progress`, no checkboxes ticked). Nothing to flag as an unauthorized edit since there
   is no edit at all.

## Scope-creep / overfitting review

- No test files show suspicious post-hoc edits; there is exactly one commit adding tests
  (`c368c97 test: sync engine, sqlite index, vcs adapter (red)`) followed by one commit adding
  the implementation (`4b309ca feat: sync engine, SQLite index, VCS adapter (R2/R4/R5/R9/C5/C6)`),
  consistent with the TDD red/green step ordering the task's `## Steps` describe.
- Implementation logic (candidate detection, hash confirm, replace-on-reparse, delete cascade,
  lock skip-sweep) is general — not special-cased to the exact fixture file names/paths used in
  tests (`a.py`, `gone.py`, etc.). Re-ran the sync test binary 3x for flake-robustness; all green.
- No changes to `src/lang/**` or `src/cmd/**` (out-of-scope directories per the task's own
  `## Touch` section).

## Gate results

- `bash context-tree/scripts/check.sh` → exit 0 (fmt clean, clippy clean with `-D warnings`,
  full `cargo test` suite — all language-extractor test binaries plus sync/index/vcs — green).
