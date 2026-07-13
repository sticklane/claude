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

**Don't over-read a same-day calendar-date mismatch as proof of a second
run.** `DRAIN-OWNER.md`/critique-findings ISO dates are stamped with
`date -u`; `git log`'s commit timestamp is local (CDT, UTC-5). A commit made
late in the evening local time can carry a header date one calendar day
ahead of what `git log`'s default local-timezone output shows. Confirmed
2026-07-13: a critique-findings entry headed "2026-07-13" turned out to be
from a commit `git log` showed as "2026-07-12 21:34 -0500" — same instant,
just past the UTC day boundary. Before concluding a second concurrent run
touched a file, diff actual commit timestamps (`git log -1 --format=%ci`),
not header calendar dates alone.
