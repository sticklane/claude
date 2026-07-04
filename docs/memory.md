# Memory index

Narrow, load-on-demand lessons. Read the topic file when a task matches its
trigger; this index is not loaded at session start. One line per topic:
path — when to read.

- [worktree-base-tracking-ref](memory/worktree-base-tracking-ref.md) — worktree agents see stale files / miss merged deps / conflict on merge (cut from `origin/main`, not HEAD).
- [unattended-worker-tool-limits](memory/unattended-worker-tool-limits.md) — authoring a drainable task, or a worker DEFERRED because it "couldn't run" a criterion (no Workflow tool / no `disable-model-invocation` skills).
- [live-drain-reconciliation](memory/live-drain-reconciliation.md) — asked to reconcile in-progress tasks or clear stale/needs-review/unpushed git flags: check for a LIVE drain first (task/* worktrees, advancing `drain:` commits, Status flipping) — it owns that cleanup; manual edits collide.
- [workboard-mirror-verbatim](memory/workboard-mirror-verbatim.md) — editing the workboard skill (workboard.py / test_workboard.py): the antigravity mirror is a byte-identical copy, so port with `cp` + `diff -q`, not hand-editing (unlike the paraphrased prose-skill mirrors).
- [concurrent-session-collision](memory/concurrent-session-collision.md) — starting a multi-file edit, or files change under you that you didn't edit: check no OTHER live Claude session shares the (non-worktree) tree (`ps aux | grep 'claude daemon'`) before proceeding; on collision stop and don't revert load-bearing changes.
