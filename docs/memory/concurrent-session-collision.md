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

Before starting — and the instant you see unexplained edits — confirm you are
the only editor:

- `ps aux | grep 'claude daemon'` — a daemon whose `--spawned-by … "cwd":"<your
  repo>"` carries a session UUID different from yours is another live session in
  the same tree. A `sleep-poll … DONEMARKER` shell under
  `/private/tmp/claude-501/-<repo>-<uuid>/` is that session's subagent waiting
  on a worker.
- `git worktree list` — a single checkout = shared tree = zero isolation.
- Recent file mtimes / `git status` entries you didn't produce.

On collision: **STOP editing, surface it to the user, and do NOT unilaterally
revert your own changes** — the other session may depend on them (its imports
can assume your moves already landed, so reverting breaks it). Let one session
own the finish; the other stays fully out of the tree. When parallel edits are
actually intended, `isolation: "worktree"` (Agent/Workflow) is the structural
fix. A live drain is one special case of this — see
[[live-drain-reconciliation]].
