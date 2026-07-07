---
name: drain
description: Works the remaining task queue unattended - dispatches one fresh worker per unblocked task in dependency order (or an independent group concurrently when the user asks for throughput), verifies and merges each, defers clarification questions instead of stopping, and batches them for the human when the queue runs dry. At lowest priority, also auto-breaks-down critic-READY specs that have no tasks/ yet. Runs until the queue is empty or only blocked work remains.
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

**Path-scoped commits, always.** Every queue-state commit drain makes —
owner claim/release, status flips, Progress entries, Deferred questions,
draft stubs, evidence — uses `git add <explicit paths>` and `git commit`
limited to those paths; never `-a`, never bare `git add .`, never an
unscoped commit, in the shared checkout. A concurrent session's staged or
working-tree changes must never ride along. Stated once here; every
commit below follows it without restating it.

**Startup session sweep (advisory).** Before inventory, list other live
sessions whose cwd resolves into this repo: `claude agents --json`,
filtered by cwd the way `agent-console/agent-console.py`'s
`live_sessions_from_cli` (≈429–490) does; if the CLI is unavailable, fall
back to `~/.claude/sessions/*.json` pid records probed with `kill -0`.
Print one line per foreign live session (sid or pid, cwd, last activity).
Sweep failure (CLI absent, no session files) prints one "sweep
unavailable" line and continues — this check is advisory only and never
blocks dispatch; correctness comes from the owner-lease claim below, not
this sweep.

## 1. Inventory

Read only the header fields of each task file
(`Status`, `Depends on`, `Priority`, `Budget`, `Touch`) — not the bodies;
workers read their own task. `Budget` feeds the worker's over-budget stop
and the headless `--max-turns` cap; `Priority` is an optional tie-break
(absent = P2). A task is **dispatchable** when `Status: pending` and
every dependency is `done`. `Status: draft` stubs (discovered work,
step 3) are never dispatchable — only a human promotes `draft` →
`pending`.

**Claim the owner lease, before reporting the plan below.** If
`specs/<slug>/DRAIN-OWNER.md` is absent, write it (pinned format in
reference.md's "Owner lease") and commit it, path-scoped, as drain's
first bookkeeping commit — then push (guard in step 3). The claim is
itself compare-and-swap: immediately after committing, re-read the file
at HEAD and confirm YOUR `Run-token:` is the one present — a different
token means you lost a simultaneous-start race; take the refuse path
below (treat the winner as the existing owner), never proceed as owner.
If DRAIN-OWNER.md already exists, evaluate its liveness (reference.md,
"Owner lease" liveness definition): **FRESH** (any signal younger than
the grace window) → REFUSE — report the owner file's headers, the
freshest signal and its age, and any other specs with dispatchable
tasks, then stop — UNLESS this generation was launched via the baton
relaunch command and its baton's `Run-token:` matches DRAIN-OWNER.md's
(adopt the existing owner; a mismatched token means the predecessor died
and a foreign drain claimed — apply the FRESH path above on the evidence
like any other startup). **ALL signals stale** → reclaim: run the
stale-lock sweep for each of the spec's in-progress tasks, tightened here
so a task is swept only when its activity signals are stale AND
`git worktree list` shows no worktree checked out on its `task/NN-<slug>`
branch — then replace DRAIN-OWNER.md with your own claim, committing the
takeover as one path-scoped commit and pushing it. Release: the terminal
report (queue empty / only blocked / interview handoff to human, step 4)
deletes the owner file in a committed, path-scoped cleanup, pushed like
every other bookkeeping commit.

Report the plan in one block: dispatch order, what's already done, what's
deferred/blocked and why. An `in-progress` task is a dead worker's lock
ONLY after the liveness check in reference.md confirms it — run that check
first (TaskList, then the worktree/`-t*` activity grace window); a task
still inside its window is parked, not swept, and drain keeps dispatching
other tasks (reference.md, "Stale-lock liveness check"). On confirmed death,
preserve the run's branches as `rescue/NN-<slug>-<shortsha>` — the
`task/NN-<slug>` branch and any `task/NN-<slug>-t*` tournament branches a
crashed run left behind — snapshotting uncommitted worktree changes per
reference.md's rescue procedure and force-removing each worktree first, then
flip the task to `pending` and commit the flip (slot machine — never resume
a dead run; rescue branches are forensic only). Full procedure in
reference.md's Status field semantics.

## 2. Dispatch (a rolling window of W workers)

Every worker drain dispatches runs at the **implementation-worker tier pin**
on attempt 1 (Claude default: `opus`; other runtimes map the pin in their
`runtimes/` profile's Role pins table) — step 3 walks failures up the
ladder: a single relaunch at the frontier tier, then one tournament at that
same frontier tier — and each is told to delegate its own
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

**Rolling window of W workers.** Instead of a strict group barrier (flip
every member in one commit, launch all, wait for all, then merge), drain
keeps up to **W** workers in flight at once and tops the window up on every
verdict. At W=1 this reduces to today's sequential drain: one worker,
admitted alone, merged before the next is admitted; merges stay trivial and
spend stays bounded.

**Window size W.** Default **1** (today's behavior). A `Parallel-window: N`
header in the drained SPEC.md opts the queue in at W=N. An explicit user
request at /drain invocation overrides the header: a request naming a
number sets W to it; a bare throughput request ("in parallel", "for
throughput") sets W=3, the research default. **Hard cap: W ≤ 5**, and W
caps TOTAL live workers, not window bookkeeping (research puts the writer
sweet spot at 3–5; >5 is reserved for read-only fan-outs). The sole
exception is a tournament, which runs its three workers in an
otherwise-empty window (reference.md, "Tournament", R8a).

**Admission (R1).** A pending task enters the window only when all hold:

- `Status: pending` and every `Depends on:` dependency is `done`;
- its `Touch:` list is pairwise-disjoint from the **claim set** — the
  `Touch:` of every task whose committed `Status:` is `in-progress`,
  whether it holds a live window slot or is a suspected zombie (zombies
  keep `Status: in-progress`, so the claim set is computable from committed
  headers alone);
- it is **co-admissible** with every in-flight task: two tasks may be in
  flight together iff some single `Group:` line in the owning spec's
  Parallelization section names both. A pending task named on no `Group:`
  line — or in a spec with no Parallelization section — runs only **alone**:
  admitted when the window is empty, and nothing else is admitted while it
  runs. **"Window empty" means zero live in-flight workers** — a suspected
  zombie does not count against emptiness; its persisting Touch claim gates
  only Touch-overlapping admissions (reference.md, R9.2), so a solo task is
  not starved behind a zombie it does not overlap.

**`Group:` grammar.** The owning spec's Parallelization section pins
co-admissible groups as one line per group, format
`- Group: NN, NN[, NN...]` — comma-and-space-separated two-digit task
numbers matching each task file's `NN-` prefix. Two tasks may run
concurrently only if a single `Group:` line names both; a task on no line
runs alone. This is the grammar pinned in
specs/drain-rolling-window/SPEC.md's Parallelization section and emitted by
/breakdown — drain parses these lines rather than re-deriving independence
from prose, so keep this wording consistent with that spec and breakdown's
producer side. The decision-coupling test still governs what may share a
line (members sharing an undecided design choice serialize even with
disjoint `Touch` lists); drain only consumes the resulting lines.

**Top-up on verdict, not on wave (R2).** After each verdict is collected
and (for DONE) merged + pushed, drain **re-computes admission and refills
the window** to W. There is no wave boundary and no all-members-one-commit
flip: each admission is one committed `Status: in-progress` flip for one
task (below), so the CAS/push hygiene of specs/multi-session-coordination
composes unchanged. Size the live fleet by the task map, never a default
maximum; parallelism multiplies token spend, so it buys wall-clock time,
not efficiency.

**Serial merge queue with mechanical rebase recovery (R3).** Merges stay
strictly serial — one at a time, in verdict-landing order. If a branch's
merge conflicts because a sibling merged after this branch's base was cut,
attempt exactly one `git rebase main`, executed in a
**throwaway scratch worktree** cut for the rebase — the normal path, since
harness-managed
worker worktrees are typically reaped when the worker returns its verdict,
before the serial merge reaches the branch; if the worker's own worktree
happens to survive, drain may reuse it instead. **Never `git checkout` a
task branch in the shared checkout** (composing with
multi-session-coordination's Tier-2 invariant: merges happen on the default
branch, workers live in worktrees). A clean rebase proceeds to the normal
DONE bookkeeping (step 3); a rebase that still conflicts routes to the
existing cross-task interference rule — stop the remaining merges and
report which landed cleanly, never slot-machine, since a fresh attempt
cannot fix an interaction between siblings.

**Runtime Touch enforcement at merge (R4).** Extend the merge-time
whitelist diff (step 3): the branch's changed paths must be a
**subset of the task's `Touch:` list** plus its own task file plus the
spec's
`evidence/` dir. Any path outside that set is a **merge failure** (the
slot-machine path), closing the gap where file ownership was enforced only
at plan time (/breakdown's decision-coupling test + human review) and never
mechanically at runtime.

**The flip is compare-and-swap.** Re-read the task file immediately
before flipping — the flip is an exact-match edit of the literal
`Status: pending` line (a file already flipped by another writer fails
the edit and sends drain back to step 1's inventory instead of
proceeding as if it owned the task). Set `Status: in-progress` and
**commit that edit, path-scoped to the task file** (e.g.
`drain: task 03 in-progress`), then push (guard in step 3) — the
worker's worktree is cut from this commit, so it must contain current
statuses and any `## Answers`. After committing, re-read the file at
HEAD and confirm your own flip is present before dispatching. Then
launch ONE background `implementation-worker` agent (`.claude/agents/implementation-worker.md`
pins the tier structurally — Claude default: `opus` — independent of whatever
model the calling session runs, so this is never a per-dispatch reminder) with
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
  Then **push `main` immediately after this commit** (`git push`) so the
  merged, verifier-PASSED work is backed up the moment it lands rather
  than sitting on local `main` for a human to push by hand. **Push guard
  (canonical; build cites this, and drain's own rolling-window merges follow
  it, extended here to every drain bookkeeping commit — not only DONE
  merges — since a concurrent session's `pull --rebase` has been observed
  to drop unpushed drain commits: docs/memory/concurrent-session-collision.md):**
  push only if `main` has a configured upstream — if none, skip silently;
  never `--force`; a rejected, non-fast-forward, or offline push warns
  and continues. The merge already landed locally, so a failed push
  never fails the task or aborts the run. This same guard applies to the
  owner claim/release commits (step 1), every flip (step 2), and the
  Deferred/Blocked/discovery commits below — push after each, not only
  after a DONE merge. The worker never pushes (reference.md's worker "do
  not push" clause is unchanged) — only the orchestrator session, after
  each of its own commits.
  If the merge or gates fail: run `git merge --abort` first (a failed
  merge leaves the checkout wedged in a conflicted state), then slot
  machine — discard the branch, relaunch once, one tier up from the pin:
  dispatch `implementation-worker` again with an explicit `model` override
  (Claude default: `opus` → `fable` — a retry after a deep-tier attempt
  failed, the frontier-tier sanction in
  `.claude/rules/token-discipline.md`), with the verifier's failure
  evidence — never the failed transcript — in the prompt. A second failure routes
  into one tournament (at most one per task per drain run; procedure in
  reference.md "Tournament") instead of straight to `Status: failed`:
  sweep any leftover `task/NN-<slug>-t*` branches/worktrees, then dispatch
  three concurrent `implementation-worker` agents at that same frontier
  override (Claude default: `fable` — tournament entrants are attempts 3+,
  continuing at the tier the relaunch already justified, now run as 3
  concurrent angle-variant attempts instead of 1), `isolation: worktree`, each on its
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
  `Status: deferred`, commits and pushes (path-scoped; guard above), and
  discards the worker's branch/worktree. Dependents simply never become
  dispatchable.
- **BLOCKED** (technical blocker, no human question) — write
  `Status: blocked` with the reason, commit and push (path-scoped; guard
  above) — except BLOCKED over budget
  after a merge-failure relaunch, which routes per the tournament skip
  above (straight to the tournament's verdict routing with both prior
  verdicts). A BLOCKED verdict whose cause is an orchestrator **sweep race**
  (the worker's worktree or branch vanished mid-run, per reference.md's
  Worker prompt clause) is routed specially: it never counts as a failed
  attempt toward the slot machine or tournament threshold, and reference.md's
  "Sweep-race BLOCKED verdict" note gives the status-dependent routing
  (re-dispatch when the task is `pending`/`blocked`; otherwise log and
  discard — the rescue branch is the durable artifact). A cause naming an
  account-wide runtime death (usage/weekly limit, auth/billing, persistent
  429/5xx) is instead an **environment kill**: drain sweeps every live run
  it owns, resets each to `pending`, and halts with no relaunch —
  reference.md's "Environment kill" note has the detection signal and
  run-wide halt.

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
`## Acceptance`) is in [reference.md](reference.md). Commit both, path-scoped, with
drain's next bookkeeping commit for that task — the verdict flip, or for
DONE workers a commit immediately after the merge — and push (guard
above). Drafts are never
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
preserved in the rescue snapshot when a dead run is swept dirty; deliberately
discarded branches — slot-machine losers, non-winning tournament candidates —
remain discarded. This record survives regardless because drain, the single
writer, writes it in the main checkout.)

Keep verdicts, not transcripts. Log one line per task to the user as you
go; /fleet shows the workers live. Loop to step 2 while anything is
dispatchable. This session growing heavy mid-queue is the degradation
override in step 3a — hand off via the baton, don't wait for a human to
notice.

## 3a. Baton pass (self-relaunch)

At each safe boundary (a verdict just recorded and committed, or a 3b
auto-breakdown attempt) evaluate the relaunch **trigger**:
a generation budget — hand off every 4 recorded verdicts this session (an
auto-breakdown attempt, success or failure, counts as one; default; a
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
dispatch:** (1) reconcile `specs/<slug>/DRAIN-OWNER.md` against the baton
— matching `Run-token:` and `Generation:` — before touching anything
else; a mismatch means this generation is not the legitimate heir, so
fall to step 1's refuse path instead of adopting, (2) read the baton — seeding
3b's in-session attempted-and-failed set from its `Breakdown-failed:` line, so
a spec a prior generation already failed to auto-breakdown is not retried
this generation either — (3) read task files' `Status:` lines, (4) `git log --oneline
-15`, (5) run ONE cheap verification (project check or last-flipped task's acceptance command)
to catch drift — only then dispatch. A headless generation reaching the batch interview writes
its deferred questions into the baton as a needs-attention section and stops; the final
generation deletes the baton when the queue completes.

## 3b. Auto-breakdown (lowest priority)

When step 1's inventory finds nothing dispatchable, nothing in-progress, and
no parked tasks — the same trigger step 4 uses — check for **not-yet-broken-
down specs** in scope before falling into the batch interview: a spec dir
with a `SPEC.md`, no `tasks/` (or an empty one), and a `Breakdown-ready: true`
header line — the token `/critique` writes on a READY verdict against a
`SPEC.md` (`/idea` inherits it, since its adversarial pass now routes through
`/critique` rather than the raw critic agent). This is genuinely the
lowest-priority action drain takes: it only fires once real dispatch is
exhausted, never displacing or reordering a pending task.

Eligible specs are ordered by `Priority` header (absent = P2) then
lexicographic spec path — the same tie-break as step 2. Attempt exactly one
per pass, then loop back to step 1: new tasks may make higher-priority work
dispatchable immediately, and re-scanning after each attempt keeps the
ordering honest if a marker or `Priority` changed mid-run. Attempt each
eligible spec **at most once per drain run — spanning every baton
generation, not just this one:** a failed attempt is added to this
generation's in-session attempted-and-failed set immediately, AND (since a
failed spec's `Breakdown-ready:` marker is never cleared, so it stays
eligible) survives a baton pass via `DRAIN-BATON.md`'s `Breakdown-failed:`
line (reference.md, "Baton pass"), which the next generation reads before
its first 3b pass. A spec that fails is left for the next `/drain`
invocation (a fresh run, not a relaunch) or a human, never retried in a
loop within one run (reference.md, "Auto-breakdown", has the exact
eligibility predicate and verify/commit procedure).

**Claim the target spec's owner lease first.** A spec with no `tasks/` yet
has never had a `DRAIN-OWNER.md` written for it, so the chosen spec's lease
is claimed exactly per step 1 (write it if absent, compare-and-swap re-read
to confirm, refuse and skip to the next eligible spec on a lost race) before
touching anything else — this is what stops two concurrent drains from
racing to auto-breakdown the same spec. This lease is independent of
whatever lease this run already holds for the spec whose tasks it was
dispatching (drain's scope can span multiple specs); release it (delete,
committed) once this spec's breakdown attempt concludes, success or
failure — a no-tasks spec has no queue to keep the lease open for.

Invoke `/breakdown specs/<slug>/SPEC.md` directly via the Skill tool —
`/breakdown` carries no `disable-model-invocation` flag, so this is the same
sanctioned in-session exception `/idea`'s self-chain already relies on (a
light artifact stage that works from the spec file, not a code change
needing worker isolation). Verify the result before committing — reference.md
has the exact diff check — then commit path-scoped and push (guard in step
3), and loop to step 1. Auto-created tasks land `Status: pending` exactly
like human-run `/breakdown` output: they still pass through step 1's
classification gate and step 2's ordinary dispatch/tie-break like any other
task — auto-breakdown grants no exemption from either. A failed attempt
(stray changes outside the expected paths, or zero tasks produced) is
reported in step 4's final report, never persisted into the spec, and never
retried this run.

## 4. The batch interview

When nothing is dispatchable, nothing is running, no tasks are parked
(inside their liveness window), AND 3b finds no eligible not-yet-broken-down
spec, the queue is either drained or waiting on humans. Before entering this
interview, re-run the liveness check
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
- **Specs that failed auto-breakdown this run** (3b): report each with its
  failure reason (stray changes outside the expected paths, or zero tasks
  produced) alongside the other blockers — these need a human `/breakdown`
  or spec amendment, not a retry.

Artifacts: drain mutates task files in the main checkout only (`Status`
lines, `## Deferred questions`, `## Answers`, `## Progress`, and
`Status: draft` stubs for discovered work), committing every mutation,
merges `task/NN-*` branches, and — via 3b — invokes `/breakdown` to create
new `tasks/NN-*.md` files for critic-READY specs. Next pipeline step:
/distill after a drained queue; answered questions loop back into step 1.

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
