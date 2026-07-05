# Concurrent sessions

Before multi-file edits in a shared (non-worktree) checkout, confirm you are
the only editor — two sessions interleaving in the same tree corrupt each
other (docs/memory/concurrent-session-collision.md has the incident).

## Pre-flight

- `claude agents --json` — a live session whose `cwd` resolves into this
  repo, with a different session id than yours, is another editor.
- `git worktree list` — a single checkout entry means a shared tree, zero
  isolation.
- Recent file mtimes / unexplained `git status` entries — edits you didn't
  make are a live collision, not a fluke.

## On detected collision

STOP editing and surface it to the user. Never revert the other session's
work unilaterally — it may already depend on your changes (or you on its),
so reverting can break the other session rather than fix anything. Let one
session own the finish; the other stays fully out of the tree.
`isolation: "worktree"` (Agent/Workflow) is the structural fix when
parallel edits are actually intended.
