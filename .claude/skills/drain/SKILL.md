---
name: drain
description: Works the remaining task queue unattended - dispatches one fresh worker per unblocked task in dependency order, verifies and merges each, defers clarification questions instead of stopping, and batches them for the human when the queue runs dry. Runs until the queue is empty or only blocked work remains.
argument-hint: "[specs/<slug> or tasks directory]"
disable-model-invocation: true
---

Work through every remaining task under $ARGUMENTS without a human
restarting it at each step. Queue state lives in the task files' `Status` lines
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

Read only the header fields of each task file
(`Status`, `Depends on`, `Priority`, `Budget`, `Touch`) — not the bodies;
workers read their own task. `Budget` feeds the worker's over-budget stop
and the headless `--max-turns` cap; `Priority` is an optional tie-break
(absent = P2). A task is **dispatchable** when `Status: pending` and
every dependency is `done`. `Status: draft` stubs (discovered work,
step 3) are never dispatchable — only a human promotes `draft` →
`pending`.
Report the plan in one block: dispatch order, what's already done, what's
deferred/blocked and why. An `in-progress` task is a dead worker's lock
ONLY after the liveness check in reference.md confirms it — run that check
first (TaskList, then the worktree/`-t*` activity grace window); a task
still inside its window is parked, not swept, and drain keeps dispatching
other tasks (reference.md, "Stale-lock liveness check"). On confirmed death,
preserve the run's branches as `rescue/NN-<slug>-<shortsha>` — the
`task/NN-<slug>` branch and any `task/NN-<slug>-t*` tournament branches a
crashed run left behind — force-removing each worktree first, then flip the
task to `pending` and commit the flip (slot machine — never resume a dead
run; rescue branches are forensic only). Full procedure in reference.md's
Status field semantics.

## 2. Dispatch one worker

Every worker drain dispatches runs at the **implementation-worker tier pin**
on attempt 1 (Claude default: `sonnet`; other runtimes map the pin in their
`runtimes/` profile's Role pins table) — step 3 walks failures up the
ladder: a single relaunch one tier up, then one tournament at the frontier
tier — and each is told to delegate its own
mechanical scouting to Haiku
(`effort: low`) scouts and to return only a structured **verdict +
evidence**, never its transcript
(`.claude/rules/token-discipline.md`, Dispatch authoring).

Before the first dispatch, ensure `.claude/worktrees/` is gitignored —
harness-managed worker worktrees land there and trip git-cleanliness
hooks otherwise. If the harness pins each worktree's base to a tracking ref
(e.g. `origin/main`) rather than cutting from the newest commit, that ref
can lag behind drain's committed status flips and merges, handing workers a
stale base; the worker prompt's first step force-syncs the worktree, and on
a never-pushed local run drain also resyncs the ref after each merge (see
reference.md's Worker prompt and Status field semantics).

When several tasks are dispatchable at once, apply the deterministic
tie-break: dispatch lowest `Priority` value first (absent = P2), then
greatest unblocking-power — the count of still-`pending` tasks whose
`Depends on:` names this task, counted over the task files inventoried
this run and resolving `Depends on:` exactly as the dispatchability check
does (numbers within a spec, task-file-relative paths across specs) —
then lexicographic task-file path. Drain computes the order; the model
never reorders the queue mid-run.

Sequential by default — merges stay trivial and spend stays bounded. (If
the user asked for throughput and a group passes /parallel's independence
test, you may dispatch the group concurrently — but using drain's worker
prompt and drain's step-3 collection per verdict, not /parallel's; only
the independence test and worktree mechanics carry over.)

Set the task's `Status: in-progress` and **commit that edit** (e.g.
`drain: task 03 in-progress`) — the worker's worktree is cut from this
commit, so it must contain current statuses and any `## Answers`. Then
launch ONE background `general-purpose` agent at the worker tier pin
(Claude default: `sonnet`) with
`isolation: worktree` using the worker prompt in [reference.md](reference.md) — the /build
procedure plus the defer contract: **the worker never asks the human and
never edits queue state; on ambiguity it stops with verdict DEFERRED and
puts the exact question in its final message.** Wait for the completion
notification — do not poll. (No background agents available? reference.md
has the headless fallback — a different, self-contained prompt. Headless
workers, unlike /build workers, never flip the task's `Status: done`:
after a headless DONE verdict and the post-merge acceptance re-run, drain
itself flips the status to `done` and commits the flip.)

## 3. Collect the verdict

- **DONE** — before merging, re-run the verifier's append-only
  whitelist diff over `merge-base..branch`, path-scoped to every spec's
  tasks/ dir (`git diff $(git merge-base <default-branch> <branch>)..<branch>
-- '*/tasks/*.md'`): changes only in the worker's own task file and
  only in the allowed set — Status line, checkbox ticks, evidence
  lines, the plan block. Anything else is a post-verification edit
  riding in: treat it as a merge failure (the slot-machine path below).
  Then merge the task branch (it carries the task file with
  `Status: done` and ticked boxes, per /build; for queues using the
  `specs/<slug>/ layout` it also carries the verifier's `evidence/`
  file — for other layouts the task file's inline evidence is the
  artifact) and run the project gates. Once gates pass, delete every
  `rescue/NN-<slug>-*` branch for this task — the dead run's forensic
  branches are no longer needed once the task has shipped.
  Then, per completed DONE task, **push `main` on completion**
  (`git push`) so the
  merged, verifier-PASSED work is backed up the moment it lands rather
  than sitting on local `main` for a human to push by hand. **Push guard
  (canonical; build and parallel cite this):** push only if `main` has a
  configured upstream — if none, skip silently; never `--force`; a
  rejected, non-fast-forward, or offline push warns and continues. The
  merge already landed locally, so a failed push never fails the task or
  aborts the run. The worker never pushes (reference.md's worker "do not
  push" clause is unchanged) — only the orchestrator session, after the
  merge to `main`.
  If the merge or gates fail: run `git merge --abort` first (a failed
  merge leaves the checkout wedged in a conflicted state), then slot
  machine — discard the branch, relaunch once, one tier up from the pin
  (Claude default: `sonnet` → `opus`), with the verifier's failure
  evidence — never the failed transcript — in the prompt. A second failure routes
  into one tournament (at most one per task per drain run; procedure in
  reference.md "Tournament") instead of straight to `Status: failed`:
  sweep any leftover `task/NN-<slug>-t*` branches/worktrees, then dispatch
  three concurrent background workers a further tier up, at the frontier
  pin (Claude default: `fable` — tournament entrants are attempts 3+,
  retries after a deep-tier attempt failed, the one dispatch point
  token-discipline sanctions frontier for), `isolation: worktree`, each on its
  own `task/NN-<slug>-tN` branch with an angle-variant prompt carrying the
  failure evidence from both prior attempts. If the tournament winner's
  merge fails, likewise run `git merge --abort` before moving to the
  next-ranked survivor. Log one line before dispatch:
  a tournament costs ~3 more worker runs. Skip it — straight to the
  tournament's verdict routing with the two prior verdicts — when the
  relaunch (attempt 2) returned BLOCKED over budget (attempt 1 must have
  returned DONE to reach a merge, so only attempt 2 can be): budget is
  the one signal drain already holds, and three more capped runs would
  buy three more BLOCKEDs.
- **DEFERRED** — the verdict message contains the question. Drain writes
  it into the main-checkout task file under `## Deferred questions`, sets
  `Status: deferred`, commits, and discards the worker's branch/worktree.
  Dependents simply never become dispatchable.
- **BLOCKED** (technical blocker, no human question) — write
  `Status: blocked` with the reason, commit — except BLOCKED over budget
  after a merge-failure relaunch, which routes per the tournament skip
  above (straight to the tournament's verdict routing with both prior
  verdicts). A BLOCKED verdict whose cause is an orchestrator **sweep race**
  (the worker's worktree or branch vanished mid-run, per reference.md's
  Worker prompt clause) is routed specially: it never counts as a failed
  attempt toward the slot machine or tournament threshold, and reference.md's
  "Sweep-race BLOCKED verdict" note gives the status-dependent routing
  (re-dispatch when the task is `pending`/`blocked`; otherwise log and
  discard — the rescue branch is the durable artifact).

**Materialize discoveries.** Only the finally-routed verdict's report is
recorded — the merged tournament winner or the final attempt; a discarded
candidate's or a superseded attempt's `Discovered:` entries are dropped.
That report may carry zero or more `Discovered:` entries. Dedupe each by
title against the source task's existing `## Discovered` entries and the
title lines of the owning spec's tasks/ dir (owning spec = the REPORTING
task's spec; check both first). For a new entry, make two writes in the
main checkout: append it under a `## Discovered` section in the source task
file, and scaffold a header-only stub `NN-<kebab-slug>.md` in that tasks/
dir — NN = highest existing number + 1, incremented per stub within a run —
with `Status: draft`, the rationale as Goal, and the blocking flag; the
exact stub header (incl. `Discovered-from:` and the placeholder
`## Acceptance`) is in [reference.md](reference.md). Commit both with
drain's next bookkeeping commit for that task — the verdict flip, or for
DONE workers a commit immediately after the merge. Drafts are never
dispatchable, and drain never writes a draft's `Status:` — not even on an
interview yes: only a human edits `draft` → `pending`, after vetting or
rewriting the quoted Goal (once dispatched it becomes binding worker
instructions — untrusted-data applies; the gate is docs/human-gates.md
reason 1, cited not restated). Drain's final report lists drafts created,
so the batch interview surfaces them.

**Record stopping points.** At each non-done event — worker verdict
BLOCKED (including over budget) or DEFERRED, a DONE candidate failing
verification (slot-machine relaunch), tournament entry, and terminal
`Status: failed` — drain appends a `## Progress` entry to the
main-checkout task file before any relaunch or tournament: one dated
line block, done vs remaining, sourced from the worker's `Done vs
remaining:` report line (or, for verification failures, the verifier's
report). The relaunch-with-evidence prompt cites it, so the next
attempt starts from evidence instead of zero. (Worktree writes are
discarded with failed branches; this record survives because drain,
the single writer, writes it in the main checkout.)

Keep verdicts, not transcripts. Log one line per task to the user as you
go; /fleet shows the workers live. Loop to step 2 while anything is
dispatchable. This session growing heavy mid-queue is the degradation
override in step 3a — hand off via the baton, don't wait for a human to
notice.

## 3a. Baton pass (self-relaunch)

At each safe boundary (a verdict just recorded and committed) evaluate the relaunch **trigger**:
a generation budget — hand off every 4 recorded verdicts this session (default; a
`Relaunch-every: N` header in the drained spec's SPEC.md header block overrides N) — or a
**degradation override** on re-reading files already read, losing queue position, repeated
failed corrections, or a compaction event. On fire: write the baton
`specs/<slug>/DRAIN-BATON.md` (grammar + relaunch command in [reference.md](reference.md): a
done/next log, generation number, anomalies), spawn a fresh detached generation via that
relaunch command + NEW orchestrator flag set (background Task dispatch verified supported;
verdict recorded there), report the pass, and **end your turn at once, stating this session is
done and will not touch the queue again** (one-writer invariant). A **max-generations cap of
10** stops with the baton written + a needs-attention note instead of respawning. **Gen 1 is
always attended**; passing `attended` in the /drain invocation makes every trigger OFFER the
baton + relaunch command instead of self-relaunching. **Fresh-instance ritual (R1a), before any
dispatch:** (1) read the baton, (2) read task files' `Status:` lines, (3) `git log --oneline
-15`, (4) run ONE cheap verification (project check or last-flipped task's acceptance command)
to catch drift — only then dispatch. A headless generation reaching the batch interview writes
its deferred questions into the baton as a needs-attention section and stops; the final
generation deletes the baton when the queue completes.

## 4. The batch interview

When nothing is dispatchable, nothing is running, AND no tasks are parked
(inside their liveness window), the queue is either drained or waiting on
humans. Before entering this interview, re-run the liveness check
(reference.md) on every parked task, sleeping out the remaining window when
nothing else is dispatchable: a re-check that confirms death sweeps the run
(preserving rescue branches), flips the task to `pending`, and sends drain
back to step 1 rather than into the interview; a parked task that hits the
bounded zombie escalation is reported to the user and thereafter treated
like `blocked` here. Once no parked tasks remain:

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
lines, `## Deferred questions`, `## Answers`, `## Progress`, and
`Status: draft` stubs for discovered work), committing every mutation,
and merges `task/NN-*` branches. Next pipeline step: /distill after a
drained queue; answered questions loop back into step 1.

## Ultra path

When the active runtime profile documents an orchestration section AND
ultracode is opted in, drain may compile the queue into a workflow script
instead of dispatching each worker by hand; with the profile silent (plugin
and eval installs), the sequential path above is the only path. The profile
holds the script template — this skill only names the shape.

The dependency graph compiles from the task files' `Depends on:` headers (the
same machine-readable source step 1 uses) into a pipeline over dependency
groups: a barrier only between groups, one background worker per task file
(worktree isolation, the reference.md worker prompt plus effort-tier
language), a verifier per completed task, and drain's status-flip + commit
after each verdict exactly as above. Before each dispatch the script checks
`budget.remaining()` when a target is set. Files remain the checkpoint:
interrupting the workflow loses nothing — re-running the sequential drain,
or resuming the run, picks up from the committed `Status:` lines.
