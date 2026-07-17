# Task 05: Sync engine, SQLite index, ignore rules, VCS adapter

Status: pending
Depends on: 01
Priority: P0
Budget: 60 turns
Spec: ../SPEC.md (requirements R2, R4, R5, R9 partial [storage]; contracts C5, C6)
Touch: context-tree/src/sync/**, context-tree/src/index/**, context-tree/src/vcs/**, context-tree/Cargo.toml, context-tree/tests/fixtures/sync/**, context-tree/tests/*.rs

## Goal

`ctx sync` exists and incrementally updates a `rusqlite` (bundled feature)
index in WAL mode: an mtime+size scan (or a VCS change feed) proposes
candidates, content hashes confirm, only genuinely changed files re-parse,
a racy-edit guard re-hashes files whose mtime is within the filesystem's
timestamp granularity of the previous sync, and baseline-scan deletion
detection purges a removed file's facts from the index. (The notes
subsystem doesn't exist until task 09, so this task can only assert the
fact/symbol-purge half of deletion; the "and its note reads stale" half is
covered by task 09's `notes_deletion_freshness` test once notes exist.)
Every sync appends a C5 journal record to
`.context/cache/sync-journal.jsonl`. Ignore rules (R4) exclude
`.gitignore`-matched files under git, `.ctxignore` in the no-VCS baseline,
and always exclude `.context/cache/`. The VCS adapter interface (R5)
isolates change feeds, ignores, snapshot identity, user identity, and hook
points, with a git adapter and a no-VCS baseline both shipping. Store
concurrency (C6): concurrent syncs serialize on an advisory lock; queries
read consistent snapshots and never block on a background sync, and a
query whose staleness sweep finds the lock held skips its own sweep and
reads the current snapshot without running a second concurrent sweep. This
task also adds a `note_marker(symbol_id) -> Option<(count, any_stale)>`
read API on the index store — it can and should always return `None` for
now (no notes table has rows until task 09), but its signature is fixed
here so query-command tasks (06, 07) can call it without inventing the
interface themselves. Per R1/R9, extraction (tasks 01-04) now also
produces `Reference`, `Import`, and `Scope` facts alongside `Symbol`
facts; this task adds the index tables/schema to persist all three
(reference occurrences, module-level import edges, and locals-query scope
bindings) during sync's parse step, keyed so `ctx deps` (R9) and `ctx refs`
(R10) — both task 07 — can read them straight from the index — never
re-parsing source at query time, per the spec's O(what-was-asked)
query-cost rule.

## Touch

Do not touch `src/lang/**` (extraction, owned by tasks 01-04) or `src/
cmd/**` (query commands, owned by tasks 06-07). This task owns sync,
index storage/schema, and the VCS adapter trait + git/no-VCS
implementations.

## Steps

1. RED: write a failing e2e test: sync a fixture, edit the content of
   exactly one file, run `ctx sync --stats`, assert `parsed == 1` and
   `hashed == 1`; a pure mtime bump with unchanged content yields `parsed
== 0`.
2. GREEN: implement the scan (mtime+size candidates -> hash confirm ->
   parse changed), the racy-edit guard, and `--stats` reporting.
3. RED/GREEN: deletion detection — delete an indexed file in a no-VCS
   fixture; the next sync purges its facts from the index. (Notes don't
   exist yet at this task — the note-freshness half of deletion is task
   09's `notes_deletion_freshness` test, not this task's.)
4. RED/GREEN: C5 journal — assert `.context/cache/sync-journal.jsonl` gets
   one JSON line per sync with UTC timestamp, trigger (`query`|`cli`|
   `hook`), files scanned/hashed/parsed, and `pending_reanchors` (stub at
   0 until task 10 populates it).
5. Implement the SQLite schema: per-file facts tables keyed to support C1
   paths, C2 hashes, token sets; open in WAL mode with a busy timeout. Add
   tables for `Reference` facts (name, location, kind, owning file),
   `Import` facts (source path, imported module/symbol, location), and
   `Scope` facts (locals-query bindings, per file) alongside the symbol
   facts tables, all keyed for per-file replace-on-reparse (a re-parsed
   file's stale reference/import/scope rows are replaced, not accumulated).
6. RED/GREEN: reference/import persistence test — sync a fixture whose
   extractor (from tasks 01-04) produces at least one `Reference` and one
   `Import` fact; assert both are queryable from the index after sync, and
   that re-parsing the same file on a no-op sync does not duplicate rows.
7. RED/GREEN: C6 concurrency test — a helper process holds the sync
   advisory lock; a concurrent query returns within a bounded time (assert
   a wall-clock ceiling, e.g. a few hundred ms), appends no new journal
   record, and serves the last-completed snapshot.
8. Implement the `VcsAdapter` trait (change feed, ignore rules, snapshot
   identity, user identity, hook points) with a `GitAdapter` and a
   `NoVcsBaseline` implementation.
9. RED/GREEN: R4 ignore-rule test — a `.gitignore`-matched file in a git
   fixture, and a `.ctxignore`-matched file in a no-VCS fixture, are both
   excluded from the index; `.context/cache/` is never indexed even
   without an ignore entry.
10. RED/GREEN: R5 baseline test — index builds and syncs correctly in a
    fixture directory with no `.git` present.
11. Add the `note_marker` stub API to the index store module with a unit
    test asserting it returns `None`/empty for any symbol today (no notes
    table populated yet).

## Acceptance

- [ ] `cd context-tree && cargo test sync_incremental` → passes
      (parsed==1/hashed==1 on content edit; parsed==0 on mtime-only bump)
- [ ] `cd context-tree && cargo test sync_deletion` → passes (no-VCS
      fixture: deleting an indexed file purges its facts/symbols from the
      index; note-freshness-on-deletion is covered separately by task 09,
      since the notes subsystem doesn't exist yet at this task)
- [ ] `cd context-tree && cargo test sync_journal` → passes (C5 fields
      present per record)
- [ ] `cd context-tree && cargo test sync_references_imports` → passes
      (R9 storage: `Reference`/`Import` facts from a fixture extractor are
      queryable from the index after sync; a no-op re-sync doesn't
      duplicate rows)
- [ ] `cd context-tree && cargo test sync_concurrency` → passes (C6: bounded
      query time under a held lock, no extra journal record, last-snapshot
      served)
- [ ] `cd context-tree && cargo test ignore_rules` → passes (R4:
      `.gitignore` under git, `.ctxignore` in no-VCS baseline,
      `.context/cache/` never indexed)
- [ ] `cd context-tree && cargo test no_vcs_baseline` → passes (R5: index
      builds/syncs with no `.git` present)
- [ ] `bash context-tree/scripts/check.sh` → exits 0
