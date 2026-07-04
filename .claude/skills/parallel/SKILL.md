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
lists, and every member has runnable acceptance criteria. The group must
also pass /breakdown's "decision coupling" test — members sharing an
undecided design choice serialize even with disjoint `Touch` lists. If tasks share
files, run them sequentially instead — merge conflicts cost more than the
parallelism saves. Tell the user the dispatch plan (which tasks, which
deferred and why) before launching.

## 2. Dispatch

Before dispatching, ensure `.claude/worktrees/` is gitignored —
harness-managed worker worktrees land there and trip git-cleanliness
hooks otherwise.

At dispatch time, resolve build's SKILL.md to a concrete path —
`.claude/skills/build/SKILL.md` when the toolkit is in-repo, otherwise the
plugin cache path found at dispatch — and substitute it for
`<build-skill-path>` (workers cannot invoke `disable-model-invocation`
skills, so the prompt must carry a readable path). For each task in the
group, launch a background `general-purpose` agent with
`isolation: worktree`, prompted with:

> Execute the task in <task-file> following the build skill's procedure
> exactly, as written in <build-skill-path> (resolved at dispatch):
> scouts for exploration, tests first
> where criteria are test-shaped, run every acceptance command, standard
> gates, then commit to a branch named task/NN-<slug>. The task file's
> `Budget:` line is a ceiling, not a target: when remaining work clearly
> exceeds the remaining budget, stop with verdict BLOCKED "over budget"
> rather than grind on. Your final message
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

## Ultra path

When the active runtime profile documents an orchestration section AND
ultracode is opted in, parallel may compile the group into a workflow script
rather than launching each background agent by hand; with the profile silent,
the manual dispatch above is the only path. The profile holds the template —
this skill only names the shape.

The graph compiles from the members' `Depends on:` headers into a pipeline
over dependency groups (a barrier only between groups), one worker per task
file (worktree isolation, the same worker prompt plus effort-tier language),
and a verifier per completed task; merge-in-task-order and the gate-after-each
rule from step 3 are unchanged. The script checks `budget.remaining()` before
each dispatch when a target is set. Files remain the checkpoint: interrupting
loses nothing — the committed branches and task-file state resume the run.
