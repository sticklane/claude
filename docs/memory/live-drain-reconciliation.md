# A live drain owns its reconciliation — check before hand-fixing its flags

**Trigger:** asked to reconcile "in-progress" tasks, or to clear
"stale / needs-review / uncommitted / unpushed" git flags, in a repo that
runs the toolkit's drain.

Before flipping any `Status:` header, deleting a worktree/branch, or
committing to `main` to "clean up" what looks like stale drain leftovers,
**confirm no drain is live.** A live drain owns exactly that reconciliation:
it merges each `task/*` branch to `main`, writes the `drain:` bookkeeping
commit, flips the task `Status:` to `done`, and cleans up the worktree — all
on its own. Manual edits race it and can corrupt its state or cause
double-implementation.

Live-drain signals (any one ⇒ do not touch):

- `git worktree list` shows worktrees on `task/*` branches (often `locked`).
- HEAD advances with `drain: …` commits, or a task's `Status:` flips
  (`draft/pending → in-progress → done`) *while you watch*.
- Recent working-tree writes: `find . -type f -not -path './.git/*'
  -newermt '-60 seconds'`.

The drain orchestrator may run from another session with its `cwd` in `$HOME`
(not the repo) and its workers as Task sub-agents — so "no session has this
repo as cwd" is **not** proof no drain is running. As of workboard 0.7.13+ the
board reclassifies a live-owned repo's uncommitted/unpushed state into an
**"Active" group** (excluded from the needs-attention count) when a live
session's git-toplevel matches OR a `task/*` worktree's newest activity is
within the drain window (default 15m). Caveat: a drain that has gone quiet
for longer than that window ages back to `needs-review` even though it may
still be alive between generations — so a `needs-review` flag is *stronger*
evidence of stranding than before, but still not proof; re-check the live
signals above before hand-fixing.

If a drain is live: leave the repo alone, let it finish, then re-check with
`bash specs/status.sh`. If you must add unrelated files, do it without
committing to `main` until the drain settles.
