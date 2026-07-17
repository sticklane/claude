# Task 05: Sync engine, SQLite index, ignore rules, VCS adapter

Status: pending
Depends on: 01
Priority: P0
Budget: 50 turns
Spec: ../SPEC.md (requirements R2, R4, R5; contracts C5, C6)
Touch: context-tree/src/sync/**, context-tree/src/index/**, context-tree/src/vcs/**, context-tree/Cargo.toml, context-tree/tests/fixtures/sync/**, context-tree/tests/*.rs

## Goal

`ctx sync` exists and incrementally updates a `rusqlite` (bundled feature)
index in WAL mode: an mtime+size scan (or a VCS change feed) proposes
candidates, content hashes confirm, only genuinely changed files re-parse,
a racy-edit guard re-hashes files whose mtime is within the filesystem's
timestamp granularity of the previous sync, and baseline-scan deletion
detection purges a removed file's facts and re-derives its notes' freshness
to stale. Every sync appends a C5 journal record to
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
interface themselves.

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
   fixture; the next sync purges its facts from the index and, if it
   carried a note, that note's derived freshness reads stale.
4. RED/GREEN: C5 journal — assert `.context/cache/sync-journal.jsonl` gets
   one JSON line per sync with UTC timestamp, trigger (`query`|`cli`|
   `hook`), files scanned/hashed/parsed, and `pending_reanchors` (stub at
   0 until task 10 populates it).
5. Implement the SQLite schema: per-file facts tables keyed to support C1
   paths, C2 hashes, token sets; open in WAL mode with a busy timeout.
6. RED/GREEN: C6 concurrency test — a helper process holds the sync
   advisory lock; a concurrent query returns within a bounded time (assert
   a wall-clock ceiling, e.g. a few hundred ms), appends no new journal
   record, and serves the last-completed snapshot.
7. Implement the `VcsAdapter` trait (change feed, ignore rules, snapshot
   identity, user identity, hook points) with a `GitAdapter` and a
   `NoVcsBaseline` implementation.
8. RED/GREEN: R4 ignore-rule test — a `.gitignore`-matched file in a git
   fixture, and a `.ctxignore`-matched file in a no-VCS fixture, are both
   excluded from the index; `.context/cache/` is never indexed even
   without an ignore entry.
9. RED/GREEN: R5 baseline test — index builds and syncs correctly in a
   fixture directory with no `.git` present.
10. Add the `note_marker` stub API to the index store module with a unit
    test asserting it returns `None`/empty for any symbol today (no notes
    table populated yet).

## Acceptance

- [ ] `cd context-tree && cargo test sync_incremental` → passes
      (parsed==1/hashed==1 on content edit; parsed==0 on mtime-only bump)
- [ ] `cd context-tree && cargo test sync_deletion` → passes (no-VCS
      fixture: deleting an indexed noted file purges it and its note reads
      stale)
- [ ] `cd context-tree && cargo test sync_journal` → passes (C5 fields
      present per record)
- [ ] `cd context-tree && cargo test sync_concurrency` → passes (C6: bounded
      query time under a held lock, no extra journal record, last-snapshot
      served)
- [ ] `cd context-tree && cargo test ignore_rules` → passes (R4:
      `.gitignore` under git, `.ctxignore` in no-VCS baseline,
      `.context/cache/` never indexed)
- [ ] `cd context-tree && cargo test no_vcs_baseline` → passes (R5: index
      builds/syncs with no `.git` present)
- [ ] `bash context-tree/scripts/check.sh` → exits 0
