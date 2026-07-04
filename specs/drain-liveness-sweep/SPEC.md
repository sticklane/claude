# Drain: liveness-checked stale-lock sweep with rescue branches

## Problem

Drain's startup sweep declares any `in-progress` task with "no live worker" a
dead lock and discards its branch and worktree. "No live worker" is undefined
anywhere in the toolkit — in practice it means "this session's `TaskList`
shows nothing", which is wrong across session boundaries: on 2026-07-03 a
`/clear` orphaned a still-running background worker on ynab task 01; the new
session's drain saw no tracked task, swept the worktree and branch out from
under a live agent mid-`pnpm check`, and re-dispatched the task to a third
worker. The live worker's work (7 TDD commits, all per-package acceptance
commands passing) survived only because the worker improvised a
`rescue/ynab-01-<sha>` branch — a convention two independent swept workers
have now invented, which drain neither creates nor cleans up. The evidence
that the worker was alive (worktree file mtimes minutes old) was visible to
the orchestrator at sweep time and was misread; the signal it did consult
(the worktree lock's pid) is the parent session's pid and proves nothing.

## Solution

Amend the drain skill only — `.claude/skills/drain/SKILL.md` and
`.claude/skills/drain/reference.md` in this repo. Four changes: (1) define a
stale-lock liveness check (harness `TaskList` first, then a worktree activity
grace window) that drain must run before any sweep, plus the control-flow
home for tasks inside their window (park, drain other tasks, re-check before
the batch interview, bounded escalation); (2) codify the rescue branch
convention the workers improvised — the sweeper preserves a swept run's
branch as `rescue/NN-<slug>-<shortsha>` instead of deleting it, and DONE
bookkeeping deletes the task's rescues after its merge passes gates; (3) add
one clause to the worker prompt telling a worker whose worktree vanishes
mid-run to stop, preserve its commits as a rescue branch, and exit BLOCKED
naming the sweep; (4) define how drain routes such a verdict without
escalating. All edits are prose in the two skill files; no harness changes.

## Requirements

R1. `reference.md` gains a "Stale-lock liveness check" section defining the
    procedure drain MUST run before sweeping an `in-progress` task, in order:
    (a) harness check — `TaskList`/background-task state; a running or queued
    worker for the task means live: wait for its notification, never sweep.
    (b) activity check — gather EVERY worktree and branch belonging to the
    task (the `task/NN-<slug>` worktree and any `task/NN-<slug>-t*`
    tournament worktrees/branches); take the newest of: file mtimes under
    each worktree (excluding `node_modules` and `.git` internals) and each
    branch's tip-commit time. If that newest activity is younger than the
    grace window, the worker is possibly alive: do not sweep — park the task
    (R2). Sweep only when a full window has passed with no new activity.

R2. Parked-task control flow, amended into SKILL.md (steps 1 and 4) and the
    new reference.md section:
    (a) A parked task is left `in-progress`; drain continues dispatching
    other tasks whose dependencies are met.
    (b) Step 4's trigger changes from "when nothing is dispatchable and
    nothing is running" to also require no parked tasks: before entering the
    batch interview / final report, drain re-runs the liveness check on each
    parked task, sleeping out the remaining window when nothing else is
    dispatchable. A task whose re-check confirms death is swept (R5), flipped
    to `pending`, and drain returns to step 1 — it does not proceed into the
    interview past a newly dispatchable task.
    (c) Bounded: after 4 consecutive window extensions on the same task with
    no verdict and no harness-tracked worker, drain stops waiting and reports
    the task to the user as a suspected zombie (leftover process refreshing
    mtimes) — it does NOT silently sweep and does NOT wait forever. A
    zombie-reported task leaves the parked set and is treated like `blocked`
    for step 4's trigger and the final report; its status stays
    `in-progress`. Each park and extension is logged to the user in one line.

R3. The grace window is 15 minutes, stated once as a named default that a
    queue may override, not hard-coded into multiple sentences.

R4. The same reference.md section states explicitly that the worktree lock's
    recorded pid is NOT a liveness signal (it is the spawning session's pid:
    alive after `/clear` orphaned the agent, and it is this session's own pid
    for workers this session spawned).

R5. Sweep procedure change, in both SKILL.md step 1 and reference.md's
    status-semantics/startup-sweep passage: when a run is swept, each of its
    branches (including unevaluated `task/NN-<slug>-t*` ones from a crashed
    tournament) is preserved as `rescue/NN-<slug>-<shortsha>` (shortsha =
    that branch's tip) instead of deleted; branches sharing a tip collapse
    into one rescue branch (skip the duplicates), and a pre-existing rescue
    at the same sha counts as already preserved;
    worktrees are still removed (force-remove before the branch rename, since
    a checked-out branch cannot be renamed away safely). The existing
    delete-outright instructions ("discard its branch/worktree" in SKILL.md,
    "discard the dead run's worktree/branch" in reference.md) are replaced,
    not merely supplemented. Rescue branches are forensic only — the slot
    machine's "never resume a dead run" still holds; new workers are not
    pointed at them. Post-Filter tournament losers (evaluated candidates)
    keep their existing handling: deleted after some merge passes gates, no
    rescue.

R6. DONE bookkeeping: two exact insertion points — (a) SKILL.md step 3's
    DONE bullet, and (b) reference.md's tournament Merge paragraph ("normal
    DONE bookkeeping") or status-semantics table note — both state that after
    a task's branch merges and project gates pass, drain deletes every
    `rescue/NN-<slug>-*` branch for that task. Both files, not either.

R7. The verbatim worker prompt block in reference.md gains one clause: if the
    worker's worktree or branch disappears mid-run, stop immediately,
    preserve any commits as `rescue/NN-<slug>-<shortsha>` if git still
    permits, and exit with verdict BLOCKED naming the sweep as the cause.

R8. Verdict routing for a BLOCKED verdict whose stated cause is an
    orchestrator sweep race (per R7), added to step 3 / the reference: it
    never counts as a failed attempt toward the slot-machine relaunch or
    tournament threshold. Routing depends on the task's current status when
    the verdict arrives: currently `pending` or `blocked` → treat as a
    normal dispatch decision; any other status (re-owned `in-progress`,
    `done`, `deferred`, `failed`) → log the verdict and discard it — the
    rescue branch, not the verdict, is the durable artifact.

R9. SKILL.md's step-1 dead-lock sentence references the liveness check
    ("after the liveness check in reference.md confirms it") instead of the
    bare "with no live worker", so a drain run cannot follow SKILL.md alone
    into a blind sweep.

R10. Residual risk stated in the reference.md section: the activity signal
    can go silent on a live worker for a full window (read-only phases;
    writes landing only under excluded paths like `node_modules`), so false
    sweeps remain possible by design — the rescue branch (R5) plus the
    worker's vanished-worktree clause (R7) are the deliberate safety net.
    Implementers must not add worker-side heartbeats to close this gap
    (rejected; see Out of scope).

## Out of scope

- Autopilot and parallel skills — no changes, even where their sweep language
  is similar; follow-up only if the drain protocol proves out.
- A worker heartbeat protocol (worker-side periodic touch) — rejected in
  favor of passive activity detection; R10 records the accepted residual
  risk.
- Harness/CLI changes (TaskList semantics, worktree lock format, `/clear`
  behavior) — the fix is skill-text only.
- Resuming or merging rescue branches — they stay forensic; no reconciliation
  procedure.
- Cleaning up pre-existing `rescue/*` branches in any particular repo.
- Zombie-process cleanup (killing the leftover process behind R2c) — drain
  only reports it.

## Acceptance criteria

Run from the repo root (`/Users/sjaconette/claude`). Files under
test: `S=.claude/skills/drain/SKILL.md`, `R=.claude/skills/drain/reference.md`.

- [ ] R1: `grep -qi "grace window" $R`; the new section names the TaskList
      check, the multi-worktree/`-t*` activity sweep, and both signals
      (file mtimes and tip-commit time).
- [ ] R2: `grep -qi "park" $S && grep -qi "park" $R`; SKILL.md step 4's
      trigger sentence mentions parked tasks; `grep -qi "zombie" $R` (or an
      equivalent bounded-escalation sentence) with the 4-extension bound
      present in exactly one place.
- [ ] R3: `grep -o "15 min" $R | wc -l` → 1, or the window is written once
      as a named default and referenced elsewhere by name.
- [ ] R4: `grep -qi "not a liveness signal" $R` (or equivalent explicit pid
      caveat inside the new section).
- [ ] R5 positive: `grep -q "rescue/NN-<slug>-" $R && grep -q "rescue/" $S`.
      R5 negative (old instructions gone):
      `! grep -q "discard its branch/worktree" $S` and
      `! grep -q "discard the dead run's worktree/branch" $R`.
- [ ] R6: `grep -q "rescue" $S`'s step-3 DONE bullet AND
      `grep -q "rescue/NN-<slug>-" $R`'s DONE-bookkeeping passage — check
      each file's passage individually (conjunctive, not either/or).
- [ ] R7: `grep -q "worktree or branch disappears" $R` inside the verbatim
      worker prompt block.
- [ ] R8: `grep -qi "sweep race" $R || grep -qi "sweep race" $S`; the routing
      text distinguishes task-status cases and says the verdict never counts
      toward relaunch/tournament thresholds.
- [ ] R9: `grep -q "liveness check" $S`.
- [ ] R10: `grep -qi "residual" $R || grep -qi "safety net" $R`.
- [ ] End-to-end (promptable check, one subagent or `claude -p` call per
      scenario, given only the amended reference.md + SKILL.md):
      (1) "drain startup finds task 07 `in-progress`, TaskList empty,
      worktree present, newest file mtime 4 minutes old" → answer must be:
      park, keep draining others, re-check after the window; NOT sweep.
      (2) "newest activity 40 minutes old, TaskList empty" → answer must be:
      sweep, and it names the `rescue/07-<slug>-<shortsha>` branch it
      creates instead of deleting.
      (3) "same task parked 4 windows in a row, mtimes keep refreshing,
      TaskList still empty" → answer must be: stop waiting, report a
      suspected zombie to the user, do not sweep.

## Open questions

(none)

## Parallelization

See specs/QUEUE.md (canonical, single copy) — this spec's tasks are
wired into the combined wave plan there; the Depends-on headers in
tasks/ are the machine-readable source.
