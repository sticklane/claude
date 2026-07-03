---
name: drain
description: Works the remaining task queue unattended - dispatches one fresh worker per unblocked task in dependency order, verifies and merges each, defers clarification questions into the task files instead of stopping, and batches them for the human when the queue runs dry. Runs until the queue is empty or only blocked work remains.
argument-hint: "[specs/<slug> or tasks directory]"
disable-model-invocation: true
---

Work through every remaining task under $ARGUMENTS without a human
relaunching each step. The queue state lives in the task files' `Status`
lines — never in this conversation — so drain is resumable by definition:
`/clear` at any point and re-run `/drain` to pick up exactly where it
stopped. This is the playbook's "coordination without an orchestrator"
pattern (the harness is dumb, the verifier is smart) plus its walk-away
contract; see docs/anthropic-playbook.md, "How they let agents run
unattended" (ships in the toolkit repo, not with installs).

First, the classification gate: drain is for queues that pass the
peripheral/core test. If tasks touch core business logic, auth, payments,
or migrations, run those attended via /build and drain only the rest —
reference.md has the checklist.

## 1. Inventory

Read only the header fields of each task file (`Status`, `Depends on`,
`Touch`) — not the bodies; workers read their own task. A task is
**dispatchable** when `Status: pending` and every dependency is `done`.
Report the plan in one block: dispatch order, what's already done, what's
deferred/blocked and why. Reset any stale `in-progress` (a dead worker's
lock) to `pending`.

## 2. Dispatch one worker

Sequential by default — merges stay trivial and spend stays bounded. (If
the user asked for throughput and a group passes /parallel's independence
test, dispatch that group via the /parallel procedure and come back here
when it drains.)

Set the task's `Status: in-progress` (the lock), then launch ONE background
`general-purpose` agent with `isolation: worktree` using the worker prompt
in [reference.md](reference.md) — the /build procedure plus the defer
contract: **never ask the human; write ambiguity into the task file as a
deferred question and stop with verdict DEFERRED.** Then wait for the
completion notification — do not poll. (No background agents available?
reference.md has the headless fallback.)

## 3. Collect the verdict

- **DONE** — merge the task branch, run the project gates, set
  `Status: done`. If the merge or gates fail: slot machine — discard the
  branch, relaunch once with the failure evidence in the prompt; on a
  second failure set `Status: failed` with the evidence and move on.
- **DEFERRED** — the worker already wrote its question and status; its
  dependents simply never become dispatchable. Move on.
- **BLOCKED** (technical blocker, no human question) — set
  `Status: blocked` with the reason. Move on.

Keep verdicts, not transcripts. Log one line per task to the user as you
go; /fleet shows the workers live. Loop to step 2 while anything is
dispatchable. If this session grows heavy mid-queue, finish the in-flight
task, tell the user to `/clear` and re-run `/drain` — nothing is lost.

## 4. The batch interview

When nothing is dispatchable and nothing is running, the queue is either
drained or waiting on humans:

- **Deferred questions exist**: collect every `## Deferred questions`
  block and ask them all in one round (AskUserQuestion where available,
  else a numbered list). Write each answer into the task file under
  `## Answers`, flip `deferred` back to `pending`, and return to step 1.
- **Queue empty**: report the run — per-task verdict with acceptance
  evidence and merged branches — and, if any verdict exposed a
  decomposition or spec problem, run /distill before the next queue.
- **Only blocked/failed remain**: report each blocker with its evidence
  and stop; those tasks need amending (back to /breakdown) or an attended
  /build.

Artifacts: drain mutates task files in place (`Status` lines, `## Deferred
questions`, `## Answers`) and merges `task/NN-*` branches. Next pipeline
step: /distill after a drained queue; answered questions loop back into
step 1.
