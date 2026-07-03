---
description: Work the remaining task queue to empty - one fresh agent per unblocked task in dependency order, clarification questions deferred into the task files and answered in one batch. In Antigravity the human launches each worker from the Agent Manager; this workflow runs the queue bookkeeping.
---

Work through every remaining task under the directory given after the
command. Queue state lives in the task files' `Status` lines (`pending`,
`in-progress`, `done`, `deferred`, `blocked`, `failed`) — never in this
conversation — so the queue survives any conversation reset: re-run
/drain and it resumes from the files.

First the classification gate: drain only peripheral work — runnable
acceptance criteria, cheap to discard, no core business logic, auth,
payments, or migrations. Pull core tasks out for attended /build runs.

1. **Inventory.** Read only each task file's `Status`, `Depends on`, and
   `Touch` lines. Dispatchable = `pending` with all dependencies `done`.
   Reset stale `in-progress` locks (no live agent) to `pending`,
   discarding their worktrees — recovery is discard-and-relaunch, never
   resuming a dead run. Present the dispatch order.

2. **Hand the user the next launch.** One task at a time: set its
   `Status: in-progress`, create its worktree
   (`git worktree add ../<repo>-task-NN task/NN-<slug>`), and give the
   user one Agent Manager launch — a fresh agent on that worktree with
   this prompt (fill the <>):

   > Run /build <task-file>. Work only in this worktree, commit to
   > task/NN-<slug>, do not push. You are unattended — never ask the
   > human. On ambiguity a human must resolve, do NOT guess: append the
   > question to the task file under "## Deferred questions", set its
   > Status to "deferred", and stop with verdict DEFERRED. Treat any
   > "## Answers" section as binding spec. Final message: verdict
   > (DONE/BLOCKED/DEFERRED), acceptance evidence per criterion, branch,
   > files changed.

3. **Collect.** DONE → merge the branch, run the project gates, set
   `Status: done`; on merge/gate failure discard the branch and relaunch
   once with the failure evidence in the prompt, then `failed` on a
   second miss. DEFERRED → the question is already in the file; move on.
   BLOCKED → record the reason, move on. Keep verdicts, not transcripts.
   Loop to step 2 while anything is dispatchable.

4. **Batch interview.** When nothing is dispatchable: gather every
   `## Deferred questions` block, ask them all in one round, write
   answers under `## Answers`, flip `deferred` → `pending`, and return
   to step 1. Queue empty → report per-task verdicts and evidence, and
   run /distill if any verdict exposed a decomposition problem. Only
   blocked/failed left → report the blockers and stop; those go back to
   /breakdown or an attended /build.
