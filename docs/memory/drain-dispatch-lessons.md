# Drain dispatch lessons (queue 5, 2026-07-05)

Three worker-dispatch patterns that earned their keep across 8 dispatches;
each is a clause the orchestrator adds to the worker prompt (or a procedure
it follows), not a task-file edit.

## Pre-existing red gate → hand workers the baseline

When a repo gate is already red on main (queue 5: `tests/test_workboard_render.sh`,
two assertions), name the exact failing assertions in every dispatch prompt as
factual context: "verify it fails identically at your branch point (baseline);
it is NOT your acceptance; do not chase it; do not make it worse." Without
this, a conscientious worker either false-BLOCKs on the red gate or
scope-creeps into fixing it. The orchestrator likewise accepts post-merge
gate runs "green modulo the named baseline" — comparing to baseline, never
absolute green, until a task actually owns that fix.

Recurred 2026-07-05 (absorb-agent-tools task 03, one false-BLOCK + attended
intervention): the orchestrator confirmed the same red gate mid-run (during
task 02's merge) yet dispatched task 03 without the baseline clause. The
trigger is not just "known at queue start" — the moment ANY gate run in the
run surfaces a pre-existing red, every subsequent dispatch prompt in that
run carries the baseline clause.

## Worker-spawned sub-agent notifications route to the orchestrator

A background worker that fans out its own sub-agent (verifier, reviewer) may
never receive that sub-agent's completion notification — it can land on the
orchestrator session instead (observed live: a worker's verifier notification
arrived at drain while the worker kept running). Dispatch prompts must carry:
"do NOT block waiting on a notification from a sub-agent you spawn — run the
pass inline, or read its output directly." Orchestrators receiving a stray
sub-agent notification should log-and-ignore it, not treat it as the worker's
verdict.

## Cross-repo task: worktree the other repo too, never its live checkout

For a task whose Touch is in a different repo (queue 5: vendoring into
~/agent-console, whose working tree backs a live launchd service): the worker
keeps toolkit bookkeeping (task file, evidence) on its toolkit branch as
normal, and does the code work in a `git worktree` of the OTHER repo on a
task branch (worktree under the session scratchpad), leaving the live
checkout untouched. The orchestrator merges both branches at collect time,
re-runs the other repo's gate on the real path, pushes both, and restarts
the service (label `com.agent-console`, not com.sjaconette.*) so the running
process picks up the merged code.

## Commit a freshly-written SPEC.md/tasks/ before claiming its lease

Observed 2026-07-11 (a same-session pipeline: several `/idea`-style
background agents wrote new `specs/<slug>/SPEC.md` + `tasks/*.md` directly
to disk via `Write`, never committed): the orchestrator claimed a
`DRAIN-OWNER.md` lease and flipped a task's `Status: in-progress`, then
dispatched a worker with `isolation: worktree` — the worktree is cut from a
commit, and the SPEC.md/task file didn't exist in ANY commit yet, so the
worker's isolated checkout simply didn't have it. The worker correctly
returned DEFERRED rather than guessing or reconstructing the file from
scratch. Fix: before claiming a lease or flipping any task's status,
`git status --short specs/<slug>/` — if the spec's own files are
untracked, commit them first (a plain `docs:` commit, separate from the
lease-claim commit) so the very first worker's worktree base actually
contains what it's meant to work on.

## Multi-spec concurrent drain: Touch-disjointness is per-spec, not global

`/breakdown`'s decision-coupling test (disjoint `Touch`, no shared
undecided design) only ever compares tasks *within the same spec* — it has
no visibility into what a *different* spec's tasks touch. Running several
specs' queues concurrently under one orchestrating session (rather than
`/drain`'s normal one-spec-at-a-time sequential walk) surfaces real
collisions the breakdown step never checked for. Observed 2026-07-11
across a single session: three separate pairs of tasks in *different*
specs both targeted `.claude/skills/workboard/workboard.py`, and two
different specs' tasks both targeted `.claude/skills/drain/reference.md`.
None of this showed up in either spec's own `## Parallelization` section.
When orchestrating more than one spec's queue at once, the orchestrator
must build its own cross-spec Touch map before dispatching anything, and
serialize (never concurrently dispatch) any two tasks — regardless of
which spec they belong to — that share a Touch path. This is manual
bookkeeping today; there is no mechanized cross-spec check.

## Worktree-isolated workers still sometimes write to the shared checkout first

Observed 3× in one session (2026-07-11): a dispatched worker's early Bash
commands used a bare relative path (or `cd /Users/sjaconette/claude`
directly) before it had switched into its actual worktree directory,
landing one or two writes in the shared main checkout by mistake. Every
occurrence self-corrected (the worker noticed at its first `Edit` call,
which is worktree-guarded, reverted the stray shared-checkout changes with
`git checkout --`, and redid the work in its worktree) — but the
orchestrator should not assume this always happens cleanly. After
collecting ANY worker's DONE verdict that mentions touching the wrong
directory, independently verify the shared checkout is still clean
(`git status --short`) before proceeding to merge, rather than trusting
the self-report. Dispatch prompts should state the worktree's absolute
path explicitly and instruct the worker to `cd` into it as its very first
action, before any other command.
