---
name: parallel
description: Dispatches an independent group of task files to concurrent background agents in isolated worktrees and collects their verdicts. For wall-clock throughput on independent tasks; costs proportionally more tokens.
argument-hint: "[specs/<slug> or task files...]"
disable-model-invocation: true
---

Run independent tasks from $ARGUMENTS concurrently. Parallelism multiplies
token spend — every agent pays its own context — so it buys wall-clock time,
not efficiency. Use it when the user wants throughput; otherwise sequential
`/build` in fresh sessions is cheaper.

## 1. Verify independence

Read the task files and the spec's Parallelization section (if there is no
such section, derive independence yourself from the tasks' `Depends on` and
`Touch` fields). A group is dispatchable only if: no `Depends on` edges between members, disjoint `Touch`
lists, and every member has runnable acceptance criteria. If tasks share
files, run them sequentially instead — merge conflicts cost more than the
parallelism saves. Tell the user the dispatch plan (which tasks, which
deferred and why) before launching.

## 2. Dispatch

Before dispatching, ensure `.claude/worktrees/` is gitignored —
harness-managed worker worktrees land there and trip git-cleanliness
hooks otherwise.

For each task in the group, launch a background `general-purpose` agent with
`isolation: worktree`, prompted with:

> Execute the task in <task-file> following the build skill's procedure
> exactly (in-repo: .claude/skills/build/SKILL.md; plugin install: invoke
> /agentic:build or read build's SKILL.md from the plugin's skills
> directory): scouts for exploration, tests first
> where criteria are test-shaped, run every acceptance command, standard
> gates, then commit to a branch named task/NN-<slug>. Your final message
> must be: verdict (DONE/BLOCKED), acceptance evidence per criterion (command
> + result), branch name, and files changed. If blocked, say why and stop —
> do not improvise around the task's scope.

Launch all agents of the group in one message so they actually run
concurrently. Then stop and wait for completion notifications — do not poll.
(Worker agents spawning their own scouts/verifiers requires Claude Code
v2.1.172+; on older versions, or if worktree isolation is unavailable, fall
back to headless dispatch: `git worktree add` per task, then
`claude -p "<task prompt>" --allowedTools ...` in each.)

## 3. Collect and integrate

As verdicts arrive: summarize per task (verdict + evidence, not transcripts).
When the group completes, merge the DONE branches in task order, running the
project gates after each merge. Disjoint `Touch` lists don't guarantee clean
merges (lockfiles, barrel files, snapshots): on a merge conflict or a
post-merge gate failure, STOP — leave the remaining branches unmerged, report
which branches merged cleanly and which are pending, and let the user decide.
For BLOCKED tasks, report the blocker and
whether the task file needs amending (back to /breakdown) or just a retry.
Dependent tasks unlocked by this group run next — sequentially via /build, or
another /parallel group if independent. If any worker's verdict exposed a
task-file or decomposition problem, run /distill before dispatching more.
