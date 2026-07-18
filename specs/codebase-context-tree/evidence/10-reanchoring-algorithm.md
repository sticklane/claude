# Verification evidence: Task 10 — reanchoring-algorithm

Verified by: independent verifier (subagent), 2026-07-17
Branch: task/10-reanchoring-algorithm @ 06c6a39
Base for Touch/task-file diff: 40ace97 (drain: codebase-context-tree task 10 in-progress)

## Verdict: PASS (with 2 findings — Touch-scope drift, task file not marked complete)

## Per-criterion results

All commands run with `export PATH="$HOME/.cargo/bin:$PATH"` and `cd context-tree`
first, as instructed.

1. `cargo test reanchor_rename_in_file` → PASS. Ran 1 test (`reanchor_rename_in_file
... ok`) in tests/reanchor.rs, not 0-test vacuous.
2. `cargo test reanchor_body_edit` → PASS. 1 test ran and passed.
3. `cargo test reanchor_move_rename_edit` → PASS. 1 test ran and passed.
4. `cargo test reanchor_move_no_edit` → PASS. 1 test ran and passed (covers both
   C-fixture and Go-fixture contrast inside one #[test] fn).
5. `cargo test write_anchors` → PASS. 1 test ran and passed.
6. `cargo test reanchor_durability` → PASS. 1 test ran and passed.
7. `cargo test reanchor_parse_failed_excluded` → PASS. 1 test ran and passed.
8. `cargo test tree_diff_scorer` → PASS. 13 unit tests ran (module
   `notes::reanchor::tree_diff_scorer::*`), all passed — not vacuous.
9. `cargo test reanchor_only_writes_anchor_path` → PASS. 1 test ran and passed.
10. `bash context-tree/scripts/check.sh` → PASS, exit code 0. Full test suite
    (all language fixtures, sync.rs, reanchor.rs, doc-tests) green; no warnings/
    errors grepped in the log.

Total: all 9 acceptance-checklist commands pass; every named filter produced
≥1 actual test run (no vacuous 0-test passes).

## R13 behavior genuineness (tests/reanchor.rs + src/notes/reanchor.rs skim)

- Leg (a) `reanchor_rename_in_file`: writes byte-identical body under a new
  function name, asserts anchor ends `.bar`, `fresh==true`, `file=="m.py"`,
  AND explicitly reads the note file text and asserts it still contains `foo`
  and does NOT contain `anchor_path: m.bar` — confirms phase-1-only (index)
  update with file untouched. Genuine, not tautological.
- Leg (c) `reanchor_move_rename_edit`: asserts `pending_reanchors >= 1` via
  `latest_journal(root)["pending_reanchors"]` BEFORE any `--write-anchors`
  call, plus `!fresh(&after)` (stale) and note file unchanged. Matches the
  criterion's explicit requirement.
- Leg (d) `reanchor_move_no_edit`: single test contains both C-fixture
  (module=file; moving a.c→b.c re-anchors, `anchor` starts with `b.`,
  `pending_reanchors >= 1`) and Go-fixture (module=package; anchor STRING
  EQUALS its pre-move value, `pending_reanchors == 0`) — a real behavioral
  contrast, not two copies of the same assertion.
- `write_anchors`: asserts pending>=1 pre-write, note file still contains
  `foo` pre-write, then after `ctx sync --write-anchors` asserts frontmatter
  now contains `bar`, and a SUBSEQUENT sync (`notes list`) journals
  `pending_reanchors == Some(0)`. Matches criterion exactly.
- `reanchor_durability`: covers both legs required — (1) `.context/cache`
  deleted and re-synced ("cache-rebuild durability"): asserts anchor still
  resolves to `.bar`/`b.py` and stays stale; (2) fresh `copy_tree` clone with
  cache stripped ("fresh-clone durability"): same assertions on the clone.
  Both durability legs present, not just one.
- `reanchor_parse_failed_excluded`: introduces a mid-function syntax error,
  asserts the untouched sibling note stays fresh, the broken-symbol note's
  anchor STILL CONTAINS "middle" (i.e. binding untouched, not silently
  re-anchored to a sibling), `pending_reanchors == 0` (no re-anchor attempt
  fired), then repairs the file and asserts freshness re-derives on all
  notes. All four assertions from the criterion text present.
- `tree_diff_scorer` unit tests (src/notes/reanchor.rs, 13 tests): includes
  `layer3_threshold_is_strict_at_point_six` — constructs a candidate at
  EXACTLY 3/5=0.6 overlap and asserts it does NOT re-anchor (threshold is
  strict-greater, not >=), plus a second candidate at 0.8 that does — this is
  a real boundary test, not a tautology. Also `layer1_falls_through_when_
multiple_name_kind_candidates`, `layer2_ties_break_by_lowest_file_line`,
  `layer3_ties_break_by_lowest_file_line`, `different_kind_blocks_all_layers`,
  `no_candidate_yields_none` — covers the layered fallthrough order and
  tie-break rule described in the Goal section.
- `reanchor_only_writes_anchor_path`: captures original note-file text,
  triggers a rename (pending re-anchor), then runs THREE different
  query/background-triggering commands (`notes list`, `notes list --json`,
  `sig bar`) and asserts the note file is byte-identical after all three —
  covers "no write from query/background syncs." Then runs
  `sync --write-anchors` and does a line-by-line diff of old vs new text,
  asserting exactly ONE line changed and that line starts with
  `anchor_path:` — a real structural invariant check, not a string-contains
  tautology.

No test file modification after tests were seeded is apparent from a single
git-log inspection; both test-adding commits (038e041) and the algorithm
commit (615bca5, 06c6a39) are visible in sequence with tests preceding/
alongside the implementation commits, consistent with TDD. I did not exhume
whether tests were edited post-hoc to fit a broken implementation (out of
tool-call budget for a full git-blame-per-hunk sweep), but the assertions
themselves are structurally sound and don't special-case literal fixture
strings beyond what the scenario legitimately requires (e.g. `.ends_with(".bar")`
is checking the real renamed symbol, not hardcoding an unrelated pass value).

## scripts/check.sh gate

`bash context-tree/scripts/check.sh` → exit 0. Full log tail confirms format/
lint/build style checks ran (fmt, clippy implied by earlier untail'd portion —
not independently re-verified beyond exit code and grep for
error/warning/fail, which found none) plus the full `cargo test` suite across
all language fixtures (bash, c, cpp, go, java, kotlin, ocaml, python, rust,
sync, typescript, zig, reanchor) all green.

## Touch-scope check (git diff --stat 40ace97)

Task's `Touch:` header field:

```
context-tree/src/notes/reanchor.rs, context-tree/src/sync/**,
context-tree/src/index/**, context-tree/src/cli.rs, context-tree/Cargo.toml,
context-tree/tests/fixtures/reanchor/**, context-tree/tests/*.rs
```

Files actually changed (`git diff --name-status 40ace97`):

- `context-tree/src/cli.rs` — in Touch. OK.
- `context-tree/src/cmd/notes.rs` — **NOT in Touch.** Modified: adds a
  `pending` field to `note_json` and a `\tpending` suffix to `note_line`, per
  the (unauthoritative, human-readable) `## Touch` prose and the PLAN
  comment's "cmd/notes list: append pending marker" line — functionally
  required by the Goal text ("Pending unwritten anchor updates are named in
  `ctx notes list` output"), but the mechanical `Touch:` header field never
  lists this path.
- `context-tree/src/index/mod.rs` — in Touch (`index/**`). OK.
- `context-tree/src/lib.rs` — **NOT in Touch.** Modified: CLI dispatch wiring
  for the new `--write-anchors` flag (destructures `write_anchors` from the
  `Sync` command, branches to `sync::write_anchors(...)` vs
  `sync::run_sync(...)`). Functionally required to wire cli.rs's new flag
  through to sync/, but `src/lib.rs` is not in the `Touch:` header.
- `context-tree/src/notes/mod.rs` — **NOT in Touch.** Modified: adds
  `pub mod reanchor;` and a new `rewrite_anchor_path()` function (phase-2
  frontmatter rewrite). `context-tree/src/notes/reanchor.rs` IS in Touch, but
  `context-tree/src/notes/mod.rs` (a different file) is not listed.
- `context-tree/src/notes/reanchor.rs` — in Touch. OK (new file).
- `context-tree/src/sync/mod.rs` — in Touch (`sync/**`). OK.
- `context-tree/tests/reanchor.rs` — in Touch (`tests/*.rs`). OK (new file).
- `specs/codebase-context-tree/tasks/10-reanchoring-algorithm.md` — the task
  file itself (expected; see append-only check below).

No `context-tree/tests/fixtures/reanchor/**` files were created (test uses
inline temp-dir fixtures instead) — not a violation, just an unused Touch
grant.

**Finding (scope creep relative to the mechanical Touch header):**
`src/cmd/notes.rs`, `src/lib.rs`, and `src/notes/mod.rs` were all modified but
are absent from the task's `Touch:` header. All three changes are small and
functionally necessary for the feature described in the task's own Goal/PLAN
(CLI plumbing for `--write-anchors`, the `pending` marker in `notes list`,
and registering + using the new `reanchor` module) — this reads as an
authoring gap in the Touch header (it names `reanchor.rs` but not the
`notes/mod.rs` that must declare it, and names `cli.rs` but not `lib.rs`
which dispatches it) rather than gratuitous drift (no formatting sweeps,
version bumps, or unrelated edits found). Still, per the verification
charter, the Touch list is binding and this is out-of-scope by that
mechanical definition — flagged, not silently accepted.

## Task-file append-only check

`git diff 40ace97 -- specs/codebase-context-tree/tasks/10-reanchoring-algorithm.md`
shows only ONE hunk: the 32-line `<!-- PLAN (delete at close-out) -->` HTML
comment block was inserted after the header. This falls within the allowed
append-only set (plan comment block).

**Finding (not a Touch/append-only violation, but a completeness gap):** the
`Status:` line is still `in-progress` (not `done`/`complete`), and none of
the 9 acceptance checkboxes were ticked (`- [ ]` throughout, none `- [x]`),
and no evidence-citation lines were added. Per this repo's conventions, a
finished task normally flips Status and ticks its checklist in the same
commit set. Since all 9 commands independently pass when I ran them, this
looks like an incomplete close-out step rather than a functional gap — but
it means the task, as currently represented on disk, does not itself claim
completion; I am reporting based on independently exercising the commands,
not trusting any claimed-done state (there was none to distrust).

## Scope creep beyond Touch

No other scope creep found: no version bumps, no unrelated formatting
sweeps, no edits to `src/notes/anchor.rs` or `src/notes/freshness.rs` (the
task explicitly forbids touching those beyond adding calls into them — grep
confirms no diff to either file). Cargo.toml listed in Touch but not
modified — no new dependency added, consistent with "treat new dependencies
with extreme caution."

## Summary

All 9 acceptance commands pass, tests are genuine (non-tautological,
threshold-boundary-tested, both-legs covered), and `scripts/check.sh` exits 0. Two findings for human attention: (1) Touch-scope drift on 3 files
(cmd/notes.rs, lib.rs, notes/mod.rs) not listed in the task's mechanical
`Touch:` header despite being functionally required by the task's own Goal;
(2) the task file's Status/checkbox state was never updated to reflect
completion, despite the implementation and tests being complete and passing.
