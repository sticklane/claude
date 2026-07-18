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
undecided design) only ever compares tasks _within the same spec_ — it has
no visibility into what a _different_ spec's tasks touch. Running several
specs' queues concurrently under one orchestrating session (rather than
`/drain`'s normal one-spec-at-a-time sequential walk) surfaces real
collisions the breakdown step never checked for. Observed 2026-07-11
across a single session: three separate pairs of tasks in _different_
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
same spec satisfied the pattern first (the grep takes the _first_ match, not
every match), but a spec whose _only_ flip commits are multi-task-bundled
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

## Two live drains, one shared checkout: intake-alongside works (2026-07-13)

A fresh /drain that finds the only pending spec under a FRESH foreign
`DRAIN-OWNER.md` (another live drain mid-dispatch) does not have to stand
down or halt: with the human's explicit choice, it can work everything the
leaseholder can't reach — critique intake over draft specs, stub intake,
and dispatch of any tasks those promote — claiming per-spec leases as
usual. Observed working for a full run with zero push rejections and zero
divergence-halts alongside an actively-merging sibling drain. The
load-bearing habits: push immediately after EVERY bookkeeping commit
(claim, flip, findings, release — a lingering unpushed commit is what turns
the sibling's next push into true divergence), keep every commit
path-scoped, and never touch the foreign spec's dir, drafts included. The
scope question itself is the other lesson: /drain launched outside any repo
(cwd not a git tree) has no derivable queue — ask, don't guess.

## Critique intake: skip the critic when SPEC.md is unchanged — mechanized in /critique

This skip is now **mechanized in /critique** itself
(specs/critique-findings-loop-closure R5), not a manual `git log` recipe.
`/critique` records the **content hash** of the `SPEC.md` a NOT READY /
READY WITH NITS verdict was produced from into
`specs/<slug>/critique-findings.md`, and on the next invocation compares the
current `SPEC.md` content hash against that recorded header — matching hash
plus a recorded verdict → skip the critic dispatch and relay the recorded
verdict. Drain's critique intake invokes `/critique` unconditionally, so it
inherits the skip for free; it no longer runs its own `git log -1` pre-check
(that short-circuit and its findings write were removed from
`.claude/skills/drain/reference.md`). Content hash, **not**
`git log -1 --format=%ct`/`%H` — a commit hash stops resolving across a
squash or rebase, the fragility this change fixes. The original evidence
still stands: four fresh critic runs on 2026-07-13 (~40k subagent tokens
each) on an unchanged spec reproduced the identical verdict — which is what
motivated mechanizing the skip rather than re-deriving it each session.

## Record a worker's reported `Decisions:` into the task file — nothing gates it mechanically

Drain's SKILL.md/reference.md say the orchestrator appends each worker's
verdict `Decisions:` bullets into the task file's own `## Decisions` section
(path-scoped commit) — this is separate from the worker ticking its own
acceptance boxes and flipping its own `Status:` line. Nothing mechanically
checks this happened: no gate greps for a `## Decisions` section, so it is
easy to collect a DONE verdict, merge it, and move on to the next dispatch
without ever writing the reported decisions into the file. Observed
2026-07-14 (drain generation 5, `c92aedb1ae49f8d3`): two of three dispatched
tasks' verdicts carried non-empty `Decisions:` bullets that went unwritten
until a deliberate catch-up pass just before the exit checklist. Treat
"write worker Decisions into the task file" as a checklist item at collect-verdict
time, not something to remember to do later — by the time you notice the gap,
you're reconstructing it from verdict text still in context rather than from
the file itself.

## A HUMAN.md entry citing a `critique-findings.md` can go stale mid-run — check the file's OWN latest round before trusting the entry

`critique-findings.md` accumulates rounds over multiple critique passes; only
the LAST round's `Verdict:` line is current — an earlier round's NOT READY
can be superseded by a later READY in the same file, especially across
different drain runs (different `Run-token:`). A HUMAN.md `## Agent-filed
blockers` entry citing that file is filed once and never mechanically
re-checked, so it can outlive the concern it named: the spec gets revised,
critiqued again, marked READY, broken down, and fully completed — while the
stale entry keeps telling a human "this needs your decision." Observed
2026-07-14 (drain generation 5): `codequality-agent-console-mutation-coverage`'s
HUMAN.md entry cited a 5th-round NOT READY verdict, but the same
`critique-findings.md` file's actual final (6th) round said READY, and the
spec's `tasks/` directory showed 4/4 done. Before trusting any HUMAN.md entry
that cites a `critique-findings.md`, `grep -n "^Verdict:" <file> | tail -1`
and cross-check the spec's own `tasks/` status — a resolved concern gets its
HUMAN.md entry deleted (human-blockers.md's "open items only" rule), not left
as a stale checkbox.

## Inside an orchestrator-isolation worktree, never diff/compare against the local `main` branch ref — it's stale

When drain's own dispatch loop runs from an isolated worktree (the default,
per reference.md's "Orchestrator isolation"), the local `main` branch ref in
that shared repo stays wherever the MAIN checkout last left it — it only
advances via an explicit checkout/fast-forward on that ref itself, which the
orchestrator worktree never does (it commits to its own `drain-<slug>-run`
branch instead). A spec-completion review's diff computation (or any other
"diff against main" check) that names the branch `main` by name, rather than
`HEAD`/`origin/main`/an explicit SHA, silently diffs against that stale ref
and can read as "my merged changes are missing" even though they landed and
pushed correctly — a false alarm that costs a debugging detour to resolve.
Confirmed 2026-07-17 (`workboard-kanban-view` drain run): `git diff
<base> main -- <paths>` came back empty right after a real, pushed merge;
`git rev-parse HEAD main` showed HEAD several commits ahead of the local
`main` ref, which was also un-force-updatable from the worktree ("cannot
force update the branch … used by worktree at …") since the main checkout
had it checked out elsewhere. Fix: always diff against `origin/main` (after
a fetch) or an explicit commit SHA from an isolated worktree, never the bare
`main` branch name.

## A stray `cd <other-worktree> && ...` cleanup one-liner silently redirects every later relative-path command

Post-merge worker-worktree cleanup (`git worktree remove <path> --force
--force; git branch -D <branch>`) is commonly run from the primary checkout
by name (`cd /Users/sjaconette/claude && ...`) rather than from inside the
orchestrator's own isolated worktree. That `cd` persists as the session's
working directory for every SUBSEQUENT Bash tool call — the harness does not
reset it — so it silently redirects the orchestrator away from
`.claude/worktrees/drain-orchestrator` back to the primary checkout (which
can itself be stale/behind, as in the "local `main` ref" lesson above). This
went undetected for several calls in one session (2026-07-17) because
branch-level git commands (`git branch`, `git worktree list`,
`git merge-base`) are location-independent within a repo — shared refs
across worktrees mean they keep returning correct results regardless of
which worktree's directory the shell is actually in — and `Write`/`Edit`
tool calls used explicit absolute paths, so file edits still landed
correctly. Only a later bare relative-path `Bash` read (`tail -8
specs/.../SPEC.md`) surfaced the drift, with "No such file or directory".
No damage occurred that time (confirmed: intervening `git commit`s could
only have succeeded on the branch they reported, proving cwd was still
correct at those points), but a `git add <relative-path>` + `git commit` run
after the drift would have silently committed the WRONG worktree's
(unrelated, possibly stale) copy of that path instead of the intended one.
Fix: after any `cd <other-path> && ...` cleanup command run from an
isolated orchestrator worktree, either explicitly `cd` back to the
orchestrator worktree before resuming relative-path work, or prefer a
subshell (`(cd <other-path> && <command>)`) so the `cd` never escapes that
one invocation.

## A rejected push from a concurrent drain needs fetch+merge+retry, not just "warn and continue"

The push guard's documented behavior ("a rejected, non-fast-forward, or
offline push warns and continues... never `--force`") is correct for NOT
failing the task, but taken literally without a retry it leaves the just-made
commit stranded unpushed on the local branch while the orchestrator's own
bookkeeping believes the merge landed on shared `main`. With a second live
drain session active in the same repo (observed 2026-07-17, two concurrent
`/drain` runs on different specs), every queue-state commit is a live race:
this run's push was rejected twice in a row as the other session's commits
landed first. Each time, `git fetch origin main && git merge origin/main
-m "..." && git push` resolved cleanly (no conflicts — different specs touch
different files) and the retry succeeded. Treat every drain push rejection
during an active run as "fetch, merge, retry" — not a terminal warning to
shrug off — so the commit actually reaches the shared remote before the next
step assumes it did.
