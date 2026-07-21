# ctx: honor `.ctxignore` as an exclusion overlay under git

Breakdown-ready: true

## Problem

Under git, `ctx`'s file universe is `git ls-files --cached --others
--exclude-standard` (`context-tree/src/vcs/mod.rs`, `GitAdapter`), so
`.gitignore` is fully honored. But a path that is *committed* yet
structurally uninteresting — build output, vendored code, generated
artifacts — cannot be excluded at all: the `.ctxignore` file already
exists with a documented minimal grammar, yet it is only consulted by the
`NoVcsBaseline` adapter. `GitAdapter` never reads it, and the original
spec pinned exactly that split (`specs/codebase-context-tree/SPEC.md`
R4: "`.ctxignore` in the no-VCS baseline"). This was an unconsidered
gap, not a decided fork — no research-doc decision addresses committed
build output.

Live evidence from the 2026-07-20 rollout across seven repos:
`ynab-mcp-server` commits its `dist/` output, so `ctx map` leads with
`dist.tools.*Tool.execute` entries that duplicate every `src/` symbol,
and `refs`/`deps` double-count each symbol that exists in both trees.
There is no supported way to fix this short of un-committing `dist/`,
which that repo needs for npx distribution.

Related but distinct: `specs/codebase-context-tree/tasks/16` covers
`map` *ranking* noise (bash locals); this spec covers index
*membership*. Fixing membership also shrinks task 16's noise surface.

## Solution

Promote `.ctxignore` from a no-VCS fallback to a VCS-independent
**exclusion overlay**: after any adapter produces its file list and
ignore verdicts, the same repo-root `.ctxignore` (same file name, same
existing matcher) subtracts paths. No new syntax, no per-adapter
opt-out, no ability to re-include what the VCS already ignores.

## Requirements

- R1 — Overlay under git: with a `.ctxignore` at the repo root of a git
  project, the indexed file set is `GitAdapter::list_files` minus
  `.ctxignore` matches, and `is_ignored` returns true when *either* git
  ignore rules *or* `.ctxignore` match. Queries (`tree`, `map`, `sig`,
  `refs`, `deps`, `at`) never surface symbols, references, or import
  edges from overlay-excluded files.
- R2 — Subtractive only: the overlay can only remove paths. No negation
  (`!`) or re-include syntax; a `.ctxignore` entry cannot resurrect a
  git-ignored file. Grammar is exactly the shipped matcher
  (`ctxignore_matches`): blank/`#` lines dropped; trailing `/` = directory
  prefix; pattern without `/` matches the basename; otherwise whole-path;
  `*` and `?` wildcards. Explicitly NOT full gitignore semantics — no
  `!`, no `**`, and this stays documented.
- R3 — One implementation, all adapters: the single overlay
  implementation is the *existing* shared `load_ctxignore` /
  `ctxignore_matches` pair. `detect()` wraps every adapter EXCEPT
  `NoVcsBaseline` with the overlay; the baseline retains its built-in
  call unchanged (it already subtracts `.ctxignore` inside its own
  `list_files`/`is_ignored`) and is never double-wrapped. Any future
  adapter registered through `detect()` gets the overlay for free.
  The wrapper delegates ALL other `VcsAdapter` methods — `name`,
  `change_feed`, `snapshot_id`, `user_identity`, `hook_dir` — to the
  inner adapter verbatim; in particular note-author resolution (C9,
  `notes/mod.rs` via `detect().user_identity()`) must still return the
  git committer identity, never fall to the trait default.
  Because double-subtraction is idempotent and thus invisible to
  output-only tests, acceptance includes a structural test that the
  baseline's file list is byte-identical before/after this change.
- R4 — Lazy-sync semantics preserved: editing `.ctxignore` takes effect
  by the next query's staleness sweep with no manual step — newly
  excluded files' symbols disappear from query results (the existing
  file-removal path when a path leaves the listed set), and removing an
  entry re-indexes the path on the next sweep. No new sync verb, no
  cache-clear instruction in docs. Notes anchored to symbols in
  overlay-excluded files become unresolved/stale by the existing
  staleness mechanism *when no equivalent symbol remains in the indexed
  set* (the layered re-anchor may legitimately re-anchor to a
  byte-identical twin, e.g. the `src/` copy of an excluded `dist/`
  symbol) — no re-anchor into an excluded file is attempted, and no
  note content is deleted; un-ignoring the path restores resolution.
- R5 — Unchanged invariants: `.context/cache/` is never indexed
  regardless of any ignore entry; a repo with no `.ctxignore` behaves
  byte-identically to today (both adapters).
- R6 — Doc surface: `context-tree/README.md` documents `.ctxignore` as
  an overlay honored in both modes with the committed-build-output
  motivation; `.claude/skills/ctx/SKILL.md` gains one line naming
  `.ctxignore` for excluding committed-but-derived paths. The skill
  edit carries the `antigravity/` mirror and `plugin.json` version bump
  per CLAUDE.md's port-chain convention (the breakdown must put both in
  some task's `Touch:`).
- R7 — Parent-contract supersession: `specs/codebase-context-tree/SPEC.md`
  R4/R5 (and the matching acceptance line for `ignore_rules`) are
  amended in the same change to say `.ctxignore` is honored in both
  modes, with a one-line supersession pointer to this spec — the
  canonical contract must not be left asserting baseline-only behavior
  after this ships (the breakdown puts the parent SPEC.md in a task's
  `Touch:`).

## Acceptance

All runnable from the repo root; test names verified absent from
`context-tree/{src,tests}` at authoring time (grep count 0,
2026-07-20).

- [ ] `cd context-tree && cargo test ctxignore_overlay` → passes, and the
      suite includes (exact substrings):
      `ctxignore_overlay_excludes_committed_paths_under_git` (R1: a git
      fixture with a *committed* `dist/lib.py` and `.ctxignore`
      containing `dist/` indexes `src/` but no `dist.` symbols; `refs`
      on a symbol defined in both trees returns only the `src/` def),
      `ctxignore_overlay_cannot_reinclude_gitignored` (R2),
      `ctxignore_overlay_edit_takes_effect_on_next_query` (R4: add an
      entry → symbol gone on next query; remove it → symbol back),
      `ctxignore_overlay_absent_file_changes_nothing` (R5),
      `ctxignore_overlay_baseline_list_unchanged` (R3: `NoVcsBaseline`
      file list byte-identical to pre-change behavior in a no-VCS
      fixture with a `.ctxignore`),
      `ctxignore_overlay_note_goes_stale_not_reanchored` (R4: a note
      anchored in a newly excluded file reports unresolved/stale, is
      not re-anchored elsewhere, and resolves again when the entry is
      removed),
      `ctxignore_overlay_git_note_author_preserved` (R3 delegation: in
      a git fixture with `git config user.email` set AND a `.ctxignore`
      present, a created note records that email as author — the
      wrapped adapter's `user_identity` reaches the inner git adapter),
      `ctxignore_overlay_at_excluded_file_exits_4` (R1: `ctx at` on a
      committed-but-overlay-excluded file exits 4, proving the composed
      `is_ignored` — not just the file list — applies the overlay).
- [ ] `cd context-tree && cargo test ignore_rules` → still passes
      unchanged (R3/R5: no-VCS baseline regression gate).
- [ ] `grep -c 'ctxignore' context-tree/README.md` ≥ 2,
      `grep -ci 'ctxignore' .claude/skills/ctx/SKILL.md` ≥ 1, and
      `grep -ci 'ctxignore' antigravity/.agents/skills/ctx/SKILL.md` ≥ 1
      (R6 mirror — un-mirrored skill edits are the port-chain failure
      CLAUDE.md warns about).
- [ ] `grep -c '"version": "0.9.23"' .claude-plugin/plugin.json` → 0
      (R6: plugin version bumped past the authoring-time 0.9.23).
- [ ] `grep -c 'ctxignore-git-overlay' specs/codebase-context-tree/SPEC.md`
      ≥ 1, and its R4 no longer reads "in the no-VCS baseline" as the
      only `.ctxignore` mode (R7).
- [ ] `bash context-tree/scripts/check.sh` → green (fmt, clippy, tests).

## Out of scope

- Full gitignore pattern semantics (`!`, `**`, anchoring subtleties) —
  the minimal matcher stays as-is; extend only if a real repo need
  surfaces.
- `map` ranking changes — that is task 16's charter.
- Per-language or per-symbol-kind filtering — membership is path-based
  only.
- Rolling `.ctxignore` files out to consuming repos (e.g.
  `ynab-mcp-server`'s `dist/`) — one-line follow-up per repo after this
  ships, not part of this spec's gates.
