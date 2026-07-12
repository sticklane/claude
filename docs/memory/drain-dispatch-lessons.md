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
action, before any other command. Recurred again 2026-07-12 (two more
workers in the same run) — the mitigation held both times (self-corrected,
verified clean), so it's now a standing risk to instruct against
preemptively rather than a one-off.

## Pinned flip-commit message is regex-sensitive to plural "tasks"

The spec-completion review's diff-base recovery greps for the literal
`^drain: <slug> task .* in-progress` pattern (singular "task", a space right
after it). A commit message bundling two simultaneous admissions —
`drain: <slug> tasks 03-04 in-progress` — does NOT match: "task" immediately
followed by "s" fails the pattern's required space. Observed 2026-07-12: a
combined-admission commit silently dropped out of the recovery grep; the
review still ran correctly because an earlier single-task flip commit in the
same spec satisfied the pattern first (the grep takes the *first* match, not
every match), but a spec whose *only* flip commits are multi-task-bundled
would SKIP its review with "no pinned flip commit" — a false skip, not a
crash. When bundling several tasks' `Status: pending -> in-progress` edits
into one commit (a legitimate way to admit a Group at once), keep the
commit message singular and literal for at least one of the bundled tasks,
e.g. `drain: <slug> task 03 in-progress (+04, Group admission)` — never
`tasks 03-04`.

## Fast-forward merges don't fire post-commit hooks

A target repo with a post-commit hook that auto-pushes (observed:
`~/ynab-app`, `~/portfolio-tracker`'s cloudbuild path) does NOT fire that
hook on `git merge --ff-only` — only `git commit` triggers post-commit
hooks, and a fast-forward merge creates no new commit. This makes
`--ff-only` merges safe to run directly in a live/auto-deploying repo's
checkout even when its own commit path is deploy-sensitive; the risk is
confined to the worker's OWN `git commit` inside its cross-repo worktree
(handled by the existing "CI/deploy precondition" dispatch clause), not the
orchestrator's merge step. Verified 2026-07-12 by checking `git status
--short` immediately after a `--ff-only` merge into `~/ynab-app` (a repo
with a confirmed post-commit auto-push hook) — no push fired, hook silent.

## Interleaved multi-spec drain: a spec-completion review double-counts a sibling's changes on shared files

When two specs are drained interleaved (not fully sequentially) and share a
Touch path — e.g. two specs both edit `token-discipline.md` or
`costsummary.go`, declared via the cross-spec `Depends on:` grammar
(specs/QUEUE.md) — the SKILL.md-pinned diff-base recovery
(`merge-base(<first pinned flip commit>, main)..main`) picks up BOTH specs'
changes to that shared file, because both landed on the same shared `main`
in between. Handing the review worker that full ref-range diff risks
re-litigating content a sibling spec's OWN spec-completion review already
passed. Observed 2026-07-12 (queue 6: `session-refresh-automation` and
`untyped-agent-fanout` both edited `token-discipline.md`,
`costsummary.go`/`SCHEMA.md`, and `agent-console.py`). Fix: dispatch the
review-fix worker with an explicit instruction naming which lines/sections
are attributable to THIS spec (cite the sibling's already-green
`evidence/spec-review.md` by path and tell the worker to exclude anything
it covers) — never blindly hand the full ref-range diff and trust the
worker to guess spec boundaries on shared files.

## Stale foreign owner lease: check the spec's own task Status first

Before running the full stale-lock liveness sweep (worktree/branch check)
on a foreign `DRAIN-OWNER.md` (different `Host:`), first check the fast,
free signal: `grep '^Status:' specs/<slug>/tasks/*.md`. If every task is
already `done`, the spec has nothing left to dispatch regardless of whether
the lease-holding process is alive — reclaiming (deleting) the lease is
safe without any worktree/branch archaeology, since a live holder of a
fully-drained spec would itself have nothing left to do with the lease.
Observed 2026-07-12: two foreign leases (`Host: claude-remote-*`, started
2026-07-09) sat unreleased on `draft-auto-promotion` and `work-exhaustion`
for 3 days after both specs' tasks had all completed — a crashed/abandoned
remote run that never ran its own release step. The task-Status check
resolved this in one command; a full liveness sweep would have needed to
probe a remote host that may not even exist anymore.

## Cross-repo worker hook-skips need orchestrator scrutiny, not a pass-through

A dispatched worker fixing a cross-repo docs task hit a pre-commit hook
failure in its target-repo worktree caused by a missing `node_modules`
(the worktree lacked installed deps, so a project-wide `tsc` ran and
failed) — unrelated to its actual change. It used `git commit --no-verify`
to get past this and reported the decision in its verdict's `Decisions:`
section. This is technically a hook-skip, which CLAUDE.md's Git Safety
Protocol reserves for explicit user request — a worker taking this
unilaterally, even for a clearly-environmental reason, is a call the
orchestrator must independently verify before accepting the DONE verdict,
not just read past. Verified 2026-07-12 by re-running the equivalent check
in the target repo's OWN live checkout (where `node_modules` exists) and
confirming it passes clean — the skip was legitimate, but that confirmation
took an extra round-trip the worker's report didn't make unnecessary.
Dispatch prompts for cross-repo tasks should flag: "a hook skip
(`--no-verify`) is not yours to take silently — if a gate fails for a
reason clearly unrelated to your change, name it explicitly in Decisions:
and let the orchestrator re-verify, don't just bypass and move on."
