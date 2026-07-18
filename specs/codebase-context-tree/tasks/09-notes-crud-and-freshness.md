# Task 09: Notes CRUD, derived freshness, C10 marker wiring

Status: done
Depends on: 06, 07
Priority: P1
Budget: 45 turns
Spec: ../SPEC.md (requirements R2 partial [note-freshness-on-deletion], R3, R12, R14; contracts C1, C2, C3, C9, C10)
Touch: context-tree/src/notes/mod.rs, context-tree/src/notes/anchor.rs, context-tree/src/notes/freshness.rs, context-tree/src/cmd/notes.rs, context-tree/src/cmd/mod.rs, context-tree/src/index/**, context-tree/src/cli.rs, context-tree/src/lib.rs, context-tree/src/sync/mod.rs, context-tree/Cargo.toml, context-tree/tests/fixtures/notes/**, context-tree/tests/*.rs

## Goal

`ctx notes add <symbol> <text> [--kind gotcha|invariant|rationale|todo]`
(body from the positional arg, `--file <path>`, or stdin via `--file -`)
writes one ULID-named markdown file under `.context/notes/` with YAML
frontmatter (id, anchor C1 path, anchor C2 hash, optional kind, C9
author/created). `ctx notes <symbol>` prints that symbol's notes with
derived freshness; `ctx notes list [--kind K] [--stale] [--file <path>]`
filters accordingly. Freshness is DERIVED (fresh iff the anchor path
resolves AND the frontmatter hash equals the current body hash) — never
stored as ground truth beyond an index cache of the derivation — and is
returned with every note read. A note file with unparseable/incomplete
frontmatter is skipped with one diagnostic line; it never aborts a query
or sync. This task also wires the C10 `[notes:<count>]`/`[notes:<count>!]`
marker into all four surfaces that already call task 05's `note_marker`
stub (tree, sig, map from task 06; at from task 07) by making that API
real (querying the now-populated notes join) instead of always returning
`None`.

## Touch

Notes storage/CRUD, the index schema addition for the notes join, and the
`cli.rs` wiring for the new `ctx notes add`/`ctx notes`/`ctx notes list`
subcommands (this is the only task that adds subcommands to `cli.rs`
alongside a still-in-flight peer, task 08 — 08 has no new subcommand of its
own, so there is no shared edit to coordinate). Do
not modify `cmd/tree.rs`, `cmd/sig.rs`, `cmd/map.rs`, `cmd/deps.rs`,
`cmd/at.rs`'s command logic itself — those already call `note_marker`;
only change what that function returns (in `src/index/`), not the callers.

## Steps

1. RED/GREEN: `ctx notes add <symbol> <text>` writes a ULID-named markdown
   file with correct frontmatter (C1 anchor path, C2 anchor hash, C9
   author/created). `CTX_AUTHOR=x` set -> `author: x`; unset in a no-VCS
   fixture -> `author: unknown`.
2. RED/GREEN: `--file <path>` and stdin (`--file -`) note-body sources
   produce notes whose bodies match their sources.
3. RED/GREEN: C3 ambiguous-anchor refusal — `ctx notes add` on an
   ambiguous symbol suffix refuses the same way query commands do (prints
   the candidate list, exits 3).
4. RED/GREEN: freshness derivation — a note is fresh iff its anchor
   resolves and the current body hash matches the frontmatter hash;
   editing the anchored symbol's body flips it to stale.
5. RED/GREEN: `ctx notes <symbol>` and `ctx notes list [--kind K] [--stale]
[--file <path>]` filtering.
6. RED/GREEN: corrupted-frontmatter note file — skipped with one
   diagnostic line (path + reason), query still exits 0.
7. R14 test: two divergent copies of the same note file (simulate a merge
   scenario) produce an ordinary VCS conflict and nothing else conflicts
   (assert via a git-fixture merge that only the note file conflicts).
8. Populate the notes join in the index (extend the schema from task 05)
   and make `note_marker` query it for real.
9. C10 four-surface test: on a fixture, add one fresh and one stale note
   to the same symbol; assert `[notes:2!]` appears in each of `ctx tree`,
   `ctx sig`, `ctx map`, and `ctx at` output for that symbol (all four
   commands already exist from tasks 06-07 and need no further code
   changes — this test exercises the wiring).
10. `ctx notes` and `ctx notes list` run R3's staleness sweep first, same
    as other query commands.
11. RED/GREEN: deletion-freshness test (R2, the half task 05 could not
    cover since notes didn't exist yet at that task) — in a no-VCS
    fixture, add a note to a symbol in a file, then delete that file;
    assert the next sync purges the symbol from `ctx tree` (task 05's
    purge behavior, exercised here now that notes exist) AND the note's
    derived freshness reads stale (its anchor no longer resolves).

## Acceptance

- [x] `cd context-tree && cargo test notes_add` → passes (frontmatter
      fields, C9 author resolution, C3 ambiguous refusal)
      — 5 passed (verifier evidence/09-notes-crud-and-freshness.md)
- [x] `cd context-tree && cargo test notes_body_sources` → passes
      (positional, `--file`, stdin) — 1 passed
- [x] `cd context-tree && cargo test notes_freshness` → passes (fresh/stale
      derivation on body edit) — 1 passed
- [x] `cd context-tree && cargo test notes_list` → passes (`--kind`,
      `--stale`, `--file` filters) — 1 passed
- [x] `cd context-tree && cargo test notes_corrupted_frontmatter` → passes
      (one diagnostic line, skipped, exit 0) — 1 passed
- [x] `cd context-tree && cargo test notes_merge_conflict` → passes (R14:
      two divergent note copies conflict, nothing else does) — 1 passed
- [x] `cd context-tree && cargo test c10_markers_all_surfaces` → passes
      (`[notes:2!]` on tree/sig/map/at for the same symbol) — 1 passed
- [x] `cd context-tree && cargo test notes_deletion_freshness` → passes
      (R2, no-VCS fixture: deleting an indexed file that carries a note
      purges its symbols from `ctx tree` on the next sync and the note's
      freshness reads stale — the half task 05 deferred here since notes
      didn't exist at that task) — 1 passed
- [x] `bash context-tree/scripts/check.sh` → exits 0
      — exit 0 (fmt --check, clippy -D warnings, full suite green)

## Decisions

- Additive wiring beyond declared `Touch:` (reversible; orchestrator widens
  Touch at merge). Edited: `context-tree/src/lib.rs` (`pub mod notes;` + the
  `Command::Notes` dispatch arm — the dispatch match lives in lib.rs, not
  cli.rs), `context-tree/src/cmd/mod.rs` (`pub mod notes;`),
  `context-tree/src/sync/mod.rs` (run_sync refreshes the derived note cache
  after fact updates, under the advisory lock — the correct, contention-free
  place to re-derive freshness per R2/R3/R12). Reverse: drop these three
  hunks and the `ctx notes` subcommand no longer builds/dispatches.
- No new crate for ULID/time: implemented a self-contained ULID (48-bit ms +
  80 bits from SHA-256 of nanos/counter/pid, existing `sha2`) and an ISO-8601
  formatter (days-from-civil), rather than adding `ulid`/`chrono`. `Cargo.toml`
  was in Touch but needed no change. Reverse: swap either for the crate.
- Frontmatter key names chosen (`id`, `anchor_path`, `anchor_hash`, `kind`,
  `author`, `created`) — the spec pins the fields, not the YAML keys.
- Bumped index `SCHEMA_VERSION` 1→2 for the new `notes` table (a
  version-mismatched cache rebuilds transparently, C4). Added `body_hash` to
  `SymbolRow` (needed as the anchor hash on add).
