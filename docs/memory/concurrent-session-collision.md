# Two live sessions on one non-worktree tree collide — detect before multi-file edits

**Trigger:** about to run a multi-file refactor / rename / move in a repo you
don't have an exclusive claim to, OR files start changing under you that you
didn't edit — "modified by user or linter" reminders, `git status` entries you
didn't create, an import already re-pointed that you never touched.

Two Claude sessions editing the SAME working tree with no worktree isolation
interleave and corrupt each other. Real failure seen: both sessions appended
the relocated symbols to a package barrel → duplicate `export`s that won't
compile; and one session's `git mv` became **load-bearing** for the other
session's re-pointed imports (which assumed the files were already moved).

The pre-flight and collision procedure now lives in the always-on rule
`.claude/rules/concurrent-sessions.md` (cited, not restated here) — check it
before multi-file edits in a shared checkout. A live drain is one special
case of this — see [[live-drain-reconciliation]].
