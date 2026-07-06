# Rolling-window parallel dispatch for /drain

Status: open
Priority: P0

## Problem

Drain's group throughput mode (drain/SKILL.md, "Group throughput mode") is a
strict barrier: flip every member in one commit, launch all workers in one
message, wait for ALL completion notifications, then merge in task order.
Two costs follow. A slow member idles every finished sibling (wave-tail
latency), and nothing new dispatches until the whole group lands — an
11-task queue with 8 independent cluster tasks (hub's tasks-styling run,
2026-07-05) ran fully sequentially because the barrier's blast radius made
opting in unattractive. Independence is also enforced only at plan time
(/breakdown's decision-coupling test + human review); at runtime the only
mechanical check is the merge-time whitelist diff over tasks/ dirs — a
worker that wanders outside its `Touch:` list is caught late or not at all.

## Research grounding (2026-07-05, verbatim-quoted sources)

- Rolling claim-next over barrier waves is the shipped frontier design:
  Anthropic agent teams use a shared task list where "after finishing a
  task, a teammate picks up the next unassigned, unblocked task on its
  own" (code.claude.com/docs/en/agent-teams).
- Writer-fleet sweet spot: "Start with 3-5 teammates for most workflows…
  Three focused teammates often outperform five scattered ones"; "If you
  have 15 independent tasks, 3 teammates is a good starting point" (same).
  10+ agents only for read-only breadth-first work
  (anthropic.com/engineering/multi-agent-research-system).
- File ownership is the #1 safety criterion: "Two teammates editing the
  same file leads to overwrites. Break the work so each teammate owns a
  different set of files" (agent-teams).
- Integration is serial everywhere: one branch/PR per task (Codex, Jules,
  Cursor); Devin's manager "monitors progress, resolves any conflicts, and
  compiles the results". No lab publishes optimistic concurrent merging;
  community practice is merge sequentially, rebase remaining branches on
  updated main.
- Cost doctrine unchanged: multi-agent ≈ 15× chat tokens; "For routine
  tasks, a single session is more cost-effective" (agent-teams) — so
  parallelism stays opt-in, sized by the task map.
- Cognition's shared-contract warning ("Actions carry implicit decisions,
  and conflicting decisions carry bad results",
  cognition.com/blog/dont-build-multi-agents) is already encoded as
  /breakdown's decision-coupling test and the pinned value-contract rule;
  this spec must not weaken either.

## Solution

Replace the group barrier with a rolling window of W concurrent workers
over the dispatchable set. Drain remains the single queue writer and the
single merger; workers keep the existing prompt contract. Merges stay
strictly serial, in verdict-landing order, with a mechanical
rebase-onto-main recovery before declaring cross-task interference.

## Requirements

- R1 **Window admission.** A task enters the window only when: `Status:
  pending`; every dependency `done`; its `Touch:` list is pairwise-disjoint
  from the **claim set** — the `Touch:` of every task whose committed
  `Status:` is `in-progress`, whether it holds a live window slot or is a
  suspected zombie (zombies keep `Status: in-progress`, so the claim set
  is computable from committed headers alone); and it is co-admissible
  with every in-flight task under the group predicate: **two tasks may be
  in flight together iff some single `Group:` line in the owning spec's
  Parallelization section names both** — a pending task named on no
  `Group:` line, or in a spec with no Parallelization section, runs only
  alone (admitted when the window is empty, and nothing else is admitted
  while it runs). **"Window empty" means zero live in-flight workers** — a
  suspected zombie does not count against emptiness; its persisting Touch
  claim gates only Touch-overlapping admissions (R9.2), so solo tasks are
  not starved behind a zombie they don't overlap. Window size W: default 1
  (today's behavior); a `Parallel-window: N` header in the drained SPEC.md
  opts the queue in; an explicit user request at /drain invocation
  overrides the header — a request naming a number sets W to it, a bare
  throughput request sets W=3 (the research default). Hard cap: W ≤ 5,
  and W caps TOTAL live workers, not window bookkeeping (research: 3–5
  sweet spot; >5 reserved for read-only fan-outs); the sole exception is
  a tournament, which runs per R8a with the window otherwise empty.
- R2 **Top-up on verdict, not on wave.** After each verdict is collected
  and (for DONE) merged + pushed, drain re-computes admission and refills
  the window. Status flips remain one committed flip per task (no more
  all-members-one-commit), so the CAS/push hygiene of
  specs/multi-session-coordination composes unchanged.
- R3 **Serial merge queue with mechanical rebase recovery.** One merge at a
  time, in landing order. If a branch conflicts because a sibling merged
  after its base was cut, attempt one `git rebase main` — **executed in a
  throwaway scratch worktree cut for the rebase (the NORMAL path:
  harness-managed worker worktrees are typically reaped when the worker
  returns its verdict, before the serial merge reaches the branch); if
  the worker's worktree happens to survive, drain may reuse it instead.
  Never `git checkout` a task branch in the shared checkout** (composes
  with multi-session-coordination's
  Tier-2 invariant: merges happen on the default branch, workers live in
  worktrees). A clean rebase proceeds to the normal DONE bookkeeping;
  conflicts route to the existing cross-task interference rule — report,
  never slot-machine.
- R4 **Runtime Touch enforcement at merge.** Extend the merge-time
  whitelist diff: the branch's changed paths must be a subset of the
  task's `Touch:` list plus its own task file (plus the spec's `evidence/`
  dir). A violation is a merge failure (slot-machine path), closing the
  gap where file ownership was enforced only at plan time.
- R5 **Machine-readable groups from /breakdown.** The Parallelization
  section's concurrent-safe groups gain a fixed grammar (one `Group:` line
  per group naming task numbers) so drain parses membership instead of
  re-deriving prose; R1's co-admissibility predicate consumes exactly
  these lines. /breakdown's template and its SKILL.md examples updated to
  emit the grammar, with the decision-coupling test deciding what may
  share a line.
- R6 **Doctrine updates.** token-discipline's fleet-sizing bullet cites the
  3–5 writer window and rolling top-up; the research quotes land in
  docs/external-playbooks.md (cited, not restated, from skills).
- R7 **Ship gates.** drain is an ultra-path skill: antigravity mirror +
  plugin.json bump in a closing task's Touch, `bash
  evals/lint-ultra-gate.sh` green, /evals drain scenario updated for the
  window semantics.
- R8 **Baton passes only at window-empty quiescence.** Background workers
  notify only the session that launched them, so a successor generation
  cannot adopt in-flight workers. When a baton trigger fires (verdict
  count or degradation override), drain enters **drain-down**: it stops
  admitting, waits for every in-flight worker's verdict, records and
  commits each per step 3, and only then — window empty, no live workers —
  writes the baton and relaunches. The baton's verdict counter counts
  recorded verdicts regardless of window size; parked-task liveness
  checks run per in-flight worker, unchanged. A drain-down that itself
  stalls (a parked worker) rides the existing liveness machinery — window
  extensions, then zombie escalation — after which the baton is written
  with the zombie recorded as a needs-attention entry.
- R8a **Tournaments run in an emptied window.** When a task qualifies for
  a tournament, drain holds all new admissions and waits for every
  in-flight sibling to land (collecting each verdict per step 3), then
  dispatches the tournament's three workers into the otherwise-empty
  window. Total live workers during a tournament is exactly 3, regardless
  of W (this matches today's sequential drain, where a tournament's three
  workers are already the only ones running — including at W=1, where 3
  is a deliberate, pre-existing exception to the cap). Admissions resume
  after the tournament's verdict routing completes. Latency cost accepted:
  tournaments are rare (at most one per task per run) and the emptied
  window removes every cap/slot ambiguity.
- R9 **Termination obligations (no deadlock, no livelock).** The scheduler
  is deadlock-free by construction and the skill text must preserve the
  three properties that make it so:
  1. **No hold-and-wait cycle.** Admission is the only wait, and it waits
     only on in-flight runs; a worker never waits on queue state, another
     worker, or a merge — so the wait graph is bipartite (tasks → runs)
     and acyclic by shape. The skill must never add a worker-side wait on
     a sibling (e.g. "pause until task N merges"); cross-task needs are
     dependency edges, resolved at admission.
  2. **Every in-flight run terminates.** Guaranteed by the existing
     bounds — Budget ceiling, stale-lock sweep, and the 4-extension
     zombie escalation. A zombie-escalated task releases its window SLOT
     (drain keeps dispatching) but its `Touch:` claim persists, since its
     worker may still be writing. The claim needs no separate store: the
     zombie's committed `Status:` stays `in-progress`, and R1's claim set
     is defined over exactly that — so overlapping tasks are refused
     admission mechanically, and reported "blocked by suspected zombie
     <task>" in the final report rather than silently starving. This is
     starvation surfaced to a human, the same terminal shape as
     `blocked`, not a hang. At escalation drain also appends the
     suspected-zombie `## Progress` entry (its normal stopping-point
     record), so the state survives a baton pass.
  3. **The pending set shrinks or the run ends.** Admission must detect an
     unsatisfiable remainder — a `Depends on:` cycle, or all remaining
     pending tasks depending (transitively) on tasks that cannot complete
     this run (blocked/failed/deferred, or `in-progress` without a live
     window slot, i.e. a suspected zombie) — and route to the batch
     interview / final report instead of waiting for a dispatch that can
     never come. The check is mechanical: committed headers give statuses
     and dependency edges; the run's own window membership (state drain
     already holds) distinguishes live in-progress from zombie. **Trigger
     precisely:** it runs only when admission is ACTIVE — never while
     admissions are held for an R8 drain-down or an R8a tournament, where
     free slots are deliberate — and only when the admission function,
     actually evaluated, returns empty. Suppressed admission is policy,
     not starvation; the check re-arms when the hold lifts.
  Livelock is excluded by the existing hard caps, which R1–R3 must not
  loosen: one mechanical rebase per branch, one slot-machine relaunch and
  one tournament per task per run, one re-dispatch after a sweep-race
  BLOCKED, four liveness-window extensions per parked task, ten baton
  generations. Every retry path is a bounded counter, never a
  wait-and-retry-forever. The scheduler is a deterministic function of
  two inputs — committed task headers, plus the run's in-flight window
  membership (which supplies slot counts and live-vs-zombie) — so
  repeated re-computation cannot oscillate: admission order is the
  deterministic tie-break, and a task refused admission is refused for a
  reason that only monotonically resolves (an in-flight task lands, or
  the run ends).

## Out of scope

- Cross-session write protocol — specs/multi-session-coordination owns
  owner leases, CAS flips, and push hygiene. **This spec depends on it
  landing first**: window top-ups commit to main more often, so the write
  hygiene must already be in place.
- Optimistic concurrent merges, worker-side conflict resolution, >5
  writers, auto-promotion of draft tasks.
- Changing the human gate on /drain itself (disable-model-invocation
  stays; docs/human-gates.md reason cited).

## Acceptance criteria

- [ ] drain/SKILL.md group-mode section replaced by rolling-window text
      carrying R1–R4 verbatim semantics; `grep -c 'Parallel-window'
      .claude/skills/drain/SKILL.md` ≥ 1.
- [ ] /breakdown SKILL.md emits the `Group:` grammar; `grep -c '^- Group:'
      .claude/skills/breakdown/SKILL.md` ≥ 1.
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0.
- [ ] multi-session-coordination's grep gate over drain/SKILL.md (the
      compare-and-swap / exact-match dispatch-step text its spec pins)
      still passes after the rolling-window rewrite — the rewrite edits
      the dispatch step that spec also edits, and must retain its
      protocol text verbatim.
- [ ] `claude plugin validate .` → pass, plugin.json version bumped.
- [ ] Antigravity mirror updated in the same commits — exact paths:
      `antigravity/.agents/workflows/drain.md` (drain is human-only, its
      body IS the workflow) and
      `antigravity/.agents/skills/breakdown/SKILL.md` (breakdown is
      model-invocable, its mirror is the skill body; its 5-line workflow
      pointer needs no edit).
- [ ] A model-free scheduler test (shell, mirroring
      test_drain_owner_protocol.sh's style) simulates admission: given
      task headers with overlapping/disjoint Touch and a W=3 window,
      asserts admission order and refusal of overlapping Touch — plus:
      co-admissibility only within a single `Group:` line (a no-group
      task admitted only alone), the R9 termination cases (a `Depends
      on:` cycle terminates with a report, not a hang; a zombie-claimed
      Touch surfaces "blocked by suspected zombie" instead of waiting),
      and admission held while a simulated tournament is open (R8a).

## Open questions

- ~~Default W without a `Parallel-window` header~~ — RESOLVED per R1:
  default stays 1; breakdown writes the header explicitly when the map
  supports it, so the choice is made at plan time by a human-read
  artifact.
- Should dispatch-time admission also consider in-flight tasks from OTHER
  specs in the same repo (drain currently drains one queue)? Deferred to
  multi-session-coordination's advisory tier.

## Parallelization

To be written by /breakdown. Expected shape: skill-text tasks (drain,
breakdown, rules/docs) are decision-coupled on the window grammar —
serialize or pin the grammar in this spec before splitting; the scheduler
test task is independent once the grammar is pinned (it tests the pinned
grammar, not the prose).
