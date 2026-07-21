# ctxignore-git-overlay — spec-completion review

spec review: 1 findings, 0 fixed, 1 discovered

Ref range reviewed: `2fd603c99f5e4f5e758b0c07fb0fe0af6e30eccd..7470c26c3cccac3b85f88c44009de20af1921856`
(the spec's first `Status: in-progress` flip commit through the last
merged task, both tasks 01 and 02 done).

## Finding (not fixed → materialized as a draft stub)

`context-tree/src/vcs/mod.rs:76-85` (overlay `list_files`/`is_ignored`)
via `ctxignore_matches` at `:250-266` — a bare directory-name `.ctxignore`
pattern with no trailing slash (`dist`, `node_modules`, `target`) excludes
nothing under the git overlay but prunes the whole subtree in the no-VCS
baseline. Same `.ctxignore`, opposite results across the two VCS modes,
silently defeating the feature's headline use case for users who omit the
trailing slash.

Not auto-fixed: resolving it requires a design decision (basename-only
vs. directory-pruning semantics for bare patterns) that also touches the
just-shipped README wording — a spec-intent choice, not a mechanical
correctness fix, per the review's ambiguity-defer contract. Materialized
as `specs/ctxignore-git-overlay/tasks/03-bare-pattern-basename-vs-directory-mismatch.md`
(`Status: draft`, `Blocking: no`).

## Confirmed clean (no other findings)

Overlay is purely subtractive (`is_ignored` ORs, `list_files` only
`retain`-drops); trailing-slash directory patterns work correctly under
git; the no-VCS baseline is returned unwrapped with no double-subtraction;
`change_feed`'s verbatim delegation has no consumer in `context-tree/src`
and `GitAdapter` returns the `None` default regardless; the test suite is
thorough and behavior-focused.

## Process note

The first spec-review dispatch this run synced its worktree to this
repo's stale LOCAL `main` branch ref (pinned well behind `origin/main`)
and wrongly concluded nothing had merged — a dispatch-prompt gap (the
worker wasn't told to use `origin/main` explicitly), not a real problem.
It committed nothing. Retried with pinned commit SHAs and an explicit
`origin/main` instruction; this file reflects the retry's real findings.
