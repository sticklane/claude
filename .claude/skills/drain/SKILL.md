---
name: drain
description: Works the remaining task queue unattended - dispatches one fresh worker per unblocked task in dependency order, verifies and merges each, defers clarification questions instead of stopping, and batches them for the human when the queue runs dry. Runs until the queue is empty or only blocked work remains.
argument-hint: "[specs/<slug> or tasks directory]"
disable-model-invocation: true
---

Work through every remaining task under $ARGUMENTS without a human
relaunching each step. Queue state lives in the task files' `Status` lines
in the MAIN checkout, and **only drain writes it — workers report verdicts,
drain records them and commits every flip**. Because state is committed
files, drain is resumable by definition: `/clear` at any point and re-run
`/drain` to pick up exactly where it stopped. This is the playbook's
"coordination without an orchestrator" pattern (the harness is dumb, the
verifier is smart) plus its walk-away contract; see
docs/anthropic-playbook.md, "How they let agents run unattended" (ships in
the toolkit repo, not with installs).

First, the classification gate: drain is for queues that pass the
peripheral/core test. If tasks touch core business logic, auth, payments,
or migrations, run those attended via /build and drain only the rest —
reference.md has the checklist.

## 1. Inventory

Read only the header fields of each task file (`Status`, `Depends on`,
`Touch`) — not the bodies; workers read their own task. A task is
**dispatchable** when `Status: pending` and every dependency is `done`.
Report the plan in one block: dispatch order, what's already done, what's
deferred/blocked and why. Any `in-progress` with no live worker is a dead
worker's lock: discard its branch/worktree if present (slot machine — never
resume a dead run), flip it to `pending`, commit the flip.

## 2. Dispatch one worker

Sequential by default — merges stay trivial and spend stays bounded. (If
the user asked for throughput and a group passes /parallel's independence
test, you may dispatch the group concurrently — but using drain's worker
prompt and drain's step-3 collection per verdict, not /parallel's; only
the independence test and worktree mechanics carry over.)

Set the task's `Status: in-progress` and **commit that edit** (e.g.
`drain: task 03 in-progress`) — the worker's worktree is cut from this
commit, so it must contain current statuses and any `## Answers`. Then
launch ONE background `general-purpose` agent with `isolation: worktree`
using the worker prompt in [reference.md](reference.md) — the /build
procedure plus the defer contract: **the worker never asks the human and
never edits queue state; on ambiguity it stops with verdict DEFERRED and
puts the exact question in its final message.** Wait for the completion
notification — do not poll. (No background agents available? reference.md
has the headless fallback — a different, self-contained prompt.)

## 3. Collect the verdict

- **DONE** — merge the task branch (it carries the task file with
  `Status: done`, ticked boxes, and the verifier's `evidence/` file, per
  /build) and run the project gates.
  If the merge or gates fail: slot machine — discard the branch, relaunch
  once with the failure evidence in the prompt; on a second failure write
  `Status: failed` with the evidence and commit.
- **DEFERRED** — the verdict message contains the question. Drain writes
  it into the main-checkout task file under `## Deferred questions`, sets
  `Status: deferred`, commits, and discards the worker's branch/worktree.
  Dependents simply never become dispatchable.
- **BLOCKED** (technical blocker, no human question) — write
  `Status: blocked` with the reason, commit.

Keep verdicts, not transcripts. Log one line per task to the user as you
go; /fleet shows the workers live. Loop to step 2 while anything is
dispatchable. If this session grows heavy mid-queue, finish the in-flight
task, tell the user to `/clear` and re-run `/drain` — nothing is lost.

## 4. The batch interview

When nothing is dispatchable and nothing is running, the queue is either
drained or waiting on humans:

- **Tasks with `Status: deferred` exist**: collect the `## Deferred
  questions` blocks from those files only, and ask them all in one round
  (AskUserQuestion where available, else a numbered list). Write each
  answer into the task file under `## Answers`, flip its status to
  `pending`, commit, and return to step 1. (Gating on the status — not on
  the mere presence of a questions block — is what stops answered
  questions from being re-asked.)
- **Queue empty**: report the run — per-task verdict with acceptance
  evidence and merged branches — and, if any verdict exposed a
  decomposition or spec problem, run /distill before the next queue.
- **Only blocked/failed remain**: report each blocker with its evidence
  and stop; those tasks need amending (back to /breakdown) or an attended
  /build.

Artifacts: drain mutates task files in the main checkout only (`Status`
lines, `## Deferred questions`, `## Answers`), committing every mutation,
and merges `task/NN-*` branches. Next pipeline step: /distill after a
drained queue; answered questions loop back into step 1.
