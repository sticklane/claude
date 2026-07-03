---
description: Dispatch an independent group of task files across parallel Agent Manager agents in separate worktrees. For wall-clock throughput; costs proportionally more tokens.
---

Coordinate concurrent execution of independent tasks from the spec
directory or task files given after the command. In Antigravity, parallel
agents are spawned by the HUMAN in the Agent Manager — this workflow
prepares the dispatch and gives the user everything to launch.

1. **Verify independence.** Read the task files and the spec's
   Parallelization section (if absent, derive independence from `Depends
   on` and `Touch`). A group is dispatchable only if: no dependency edges,
   disjoint `Touch` lists, runnable acceptance criteria everywhere. Tasks
   sharing files run sequentially instead — merge conflicts cost more than
   parallelism saves. Present the dispatch plan (which tasks, which
   deferred and why).

2. **Prepare isolation.** Create one git worktree per task:
   `git worktree add -b task/NN-<slug> ../<repo>-task-NN` (the `-b` creates
   the branch).
   Each parallel agent gets its own checkout so edits don't collide.

3. **Hand the user the launch list.** For each task, one Agent Manager
   agent opened on that worktree's folder, with this prompt (fill in):

   > Run /build <task-file path>. Work only in this worktree, commit to
   > task/NN-<slug>, do not push. Final message: verdict (DONE/BLOCKED),
   > acceptance evidence per criterion, files changed.

   Suggest the session model for judgment-heavy tasks and a Flash-class
   model for mechanical ones.

4. **Collect and integrate.** As agents finish, record verdict + evidence
   per task (not transcripts). Merge DONE branches in task order, running
   the project gates after each merge. Disjoint `Touch` lists don't
   guarantee clean merges (lockfiles, barrel files, snapshots): on a
   conflict or gate failure, STOP — leave remaining branches unmerged,
   report which merged cleanly, and let the user decide. For BLOCKED tasks,
   report whether the task file needs amending or just a retry. Remove
   merged worktrees (`git worktree remove`). If any verdict exposed a
   decomposition problem, apply the distill skill before dispatching more.
