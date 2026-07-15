# Worktree agents are cut from `origin/main`, not local HEAD

When to read: debugging why `isolation: worktree` background agents (drain,
parallel, build workers) see stale files, miss just-merged dependencies,
or produce conflicting merges — especially on a never-pushed / local-only
repo.

## The gotcha

The Claude Code harness cuts each `isolation: worktree` agent's worktree from
the `refs/remotes/origin/main` tracking ref, **not** the local branch HEAD. On
a repo that is never pushed (or whose `origin/main` otherwise lags), that ref
freezes at whatever it pointed to when the first worktree of the session was
created. Every subsequently dispatched worker is then cut from that same stale
commit, regardless of the orchestrator's committed status flips and merges.

Symptoms observed (2026-07-04 drain of `specs/`):
- The orchestrator commits a task's `in-progress` lock, dispatches, yet the
  worker's branch merge-base is an *earlier* commit → status-line merge
  conflicts on every task.
- A dependent task's worker cannot see its dependency's merged output — e.g.
  a task whose acceptance runs `bin/check-token-discipline` failed because that
  file (created by an earlier-merged sibling) was absent from its stale base.

## The fix (both, applied together)

1. **Worker-side:** the first step of the worker prompt force-syncs the
   worktree — `git reset --hard main` (no uncommitted work exists yet, so
   nothing is lost), then create the task branch from there. The branch now
   descends from current `main`, so the merge back is clean.
2. **Orchestrator-side (local-only repos):** after every merge, run
   `git update-ref refs/remotes/origin/main main` so the next dispatched
   worktree is cut fresh.

The `drain` skill now bakes in both (reference.md Worker prompt + Status field
semantics, v0.7.7). `parallel` / `build` authors dispatching worktree
workers should apply the same two defenses.
