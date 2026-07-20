Priority: P2
Rigor: production

# Drain multi-spec swarm: concurrent drain across non-overlapping specs

Breakdown-ready: true

## Problem

`/drain` holds **at most one spec-level dispatch lease at a time**
(`.claude/skills/drain/SKILL.md:33`) — a no-argument launch works the whole
`specs/` queue, but strictly **one spec at a time in a sequential walk**
(SKILL.md's exhaustion contract). Its per-spec rolling window (`W`, default
1, hard-capped at 5) already parallelizes _tasks within one claimed spec_
via a Touch-disjointness admission check (reference.md's "Rolling-window
admission & merge (R1–R4)"), but that check is scoped to one spec's claim
set only — a scout dispatch this session confirmed **no cross-spec
Touch-disjointness check exists anywhere in drain today**, and no mechanism
lets two specs' leases coexist even when their `Touch:` sets are provably
disjoint.

This wastes throughput: on a queue with several independent, non-competing
specs ready to dispatch (confirmed present right now — e.g.
`commit-message-doctrine`, `drain-session-naming-always-propose`, and
`human-blocker-impact-clarity` all have pending, non-overlapping-Touch work
simultaneously), drain works them one full spec at a time instead of
running them in parallel.

Prior art confirms the right _mechanism_, not just the _want_: a
cross-vendor research pass this session (Anthropic's own Claude Code/Agent
SDK docs, OpenAI Codex, GitHub Copilot coding agent, Cursor Background
Agents, Cognition's Devin, Google Jules, and Steve Yegge's `beads`) found a
unanimous pattern — every one of these isolates concurrent agents at the
worktree/branch/container level and avoids conflicts via **declared
non-overlapping file/task ownership**, never via runtime conflict
detection or automated merge resolution. That is exactly drain's existing
`Touch:`-disjointness admission model, already proven at the intra-spec
task level — this spec widens its scope from "within one spec" to "across
the whole queue," it does not invent a new coordination primitive.

Two concrete hazards from real (unplanned) concurrent-drain incidents are
already documented in `docs/memory/drain-dispatch-lessons.md` and are
folded into this spec's requirements below (R2/R6, R7) rather than deferred:
cross-spec Touch collisions that `/breakdown`'s decision-coupling test
cannot see (lines 64–80) — closed by R2's widened task-admission check, with
R6 confirming no second, redundant mechanism is also built — and
spec-completion review's diff-base recovery double-counting a sibling spec's
changes on a shared file when two specs' merges interleave (lines 134–151),
closed by R7.

## Solution

Widen drain's existing owner-lease and Touch-disjointness admission model
from spec-scoped to queue-scoped, reusing the same git-CAS lease mechanism
(`DRAIN-OWNER.md` per spec, unchanged format) rather than introducing a new
coordination substrate:

- At inventory (SKILL.md step 1), before claiming any lease, drain computes
  each ready spec's Touch footprint (the union of its dispatchable tasks'
  `Touch:` headers) and greedily claims up to **3 simultaneously-held
  spec leases** whose footprints are pairwise disjoint from each other and
  from every already-claimed spec's footprint, using the existing
  Priority-then-path tie-break, applied spec-by-spec.
- The rolling-window admission check (reference.md R1–R4) keeps its
  **same-spec** semantics completely unchanged — Touch-disjointness,
  `Group:`-line co-admissibility, and "runs only alone (window empty)" for
  an ungrouped task all continue to govern exactly as today whether two
  tasks from the SAME claimed spec may run together, with "window empty"
  now defined explicitly as zero OTHER in-flight tasks **from that task's
  own spec** (never the global in-flight set — see R2). A NEW, separate
  cross-spec layer governs tasks from DIFFERENT claimed specs: two tasks in
  different, both-claimed specs co-admit whenever their `Touch:` sets are
  disjoint, full stop — no `Group:` line and no window-empty check apply
  across specs (there is no cross-spec `Group:` line to satisfy, and
  "window empty" is a same-spec concept that is never checked against a
  different spec's in-flight tasks). Without this cross-spec layer the
  widened Touch-disjointness check is vacuous — every cross-spec pair would
  still fail the unwidened, globally-scoped co-admissibility clause and be
  forced to run alone, defeating R1's raised spec-lease cap entirely (the
  gap round-3 and round-4 critique both found). **Two-level cap, stated
  precisely (round-8 fix):** a single claimed spec's own concurrency ceiling
  stays exactly what it is today — its own `W` (hard-capped at ≤5,
  unchanged) bounds how many of THAT spec's own tasks may run at once. What
  is dropped is treating each claimed spec's budget as independently
  summable (3 claimed specs would otherwise sum to up to 15 workers); instead
  all claimed specs' dispatchable tasks compete for **one shared global
  window capped at ≤10 total live workers across every claimed spec
  combined**, admitted via the existing Priority-then-path tie-break across
  the whole pool once it is full — so a single spec can still never exceed
  its own `W`, but the sum across specs can be, and often will be, throttled
  below the naive per-spec sum by the shared ≤10 ceiling.
- Spec-level lease claiming (R1) is a mechanism independent of the
  per-spec task rolling-window's "these rules bind only when W > 1"
  preamble (reference.md's admission-rule section opening) — R1 claims up
  to 3 non-overlapping specs and each newly-claimed spec dispatches its
  first eligible task immediately, even when drain runs at its default
  W=1. `W` continues to govern only how many tasks run concurrently
  WITHIN one already-claimed spec; it never gates whether multiple specs
  can be claimed and worked simultaneously — this is why no-argument
  `/drain` (default W=1) still swarms across specs by default (R4).
- Two ready specs whose Touch footprints actually intersect are never
  claimed simultaneously — the lower-priority one waits for the
  higher-priority one's lease to release, mirroring the existing
  within-spec admission rule at spec granularity (R1–R4's own logic,
  reused, not reinvented).
- No-argument `/drain` defaults to this behavior — swarm claiming is not a
  separate flag; a queue with only one claimable spec, or with every ready
  spec's Touch footprint overlapping every other, degrades to today's
  exact single-spec behavior with zero visible change.
- `.claude/rules/token-discipline.md`'s existing "cap the fleet at a 3–5
  concurrent-writer window" rule gets an explicit swarm-mode carve-out
  citing this spec, rather than being silently violated.
- `.claude/skills/drain/SKILL.md` is already over its 500-line budget (505
  lines, pre-existing, unrelated to this spec) — this spec's new
  step-1/step-2 prose goes into `reference.md` (extending the existing
  "Rolling-window admission & merge (R1–R4)" section), with only a short
  pointer added to SKILL.md, and existing SKILL.md body content is
  relocated to reference.md as needed to bring SKILL.md back to ≤500 lines
  as part of this spec's own work — not left for a later spec to hit the
  same size-gate merge-blocker `commit-message-doctrine` task 02 just
  flagged.
- Task 04's original plan (a single-threaded bash re-implementation of the
  algorithm, `tests/test_drain_swarm_admission.sh`) is superseded before
  implementation begins, per round-10 scope revision: the algorithm it
  would have re-derived in bash is instead extracted as an authoritative,
  live-invoked Python module, `.claude/skills/drain/admission.py`,
  following the existing live-invocation pattern this repo already proves
  works — `.claude/skills/prioritize/SKILL.md:35` instructs the agent to
  `run python3 <this skill dir>/prioritize_scan.py` directly, and
  `specs/drain-frontier-scanner` (a sibling, not-yet-landed spec) is
  wiring the same pattern for `.claude/skills/drain/drain_frontier.py`.
  `admission.py` composes with `drain_frontier.py` rather than duplicating
  it — `drain_frontier.py` computes each spec's own per-spec
  dispatchable/admissible/blocked sets (read-only, no lease writes, no
  cross-spec cap — explicitly out of scope for that spec); `admission.py`
  consumes that JSON as input and layers R1's cross-spec Touch-disjoint
  spec-claim eligibility and R2's two-level cap on top, plus implements the
  DRAIN-OWNER.md git-CAS lease-claim protocol (reference.md's existing
  claim algorithm, mechanically unchanged) as callable code instead of
  hand-executed prose. Because `admission.py` depends on
  `drain_frontier.py`'s interface, this spec's admission-module work is
  blocked on `specs/drain-frontier-scanner` task 01 landing first (R17).
  Live `/drain` execution on Claude Code is rewired to invoke `admission.py`
  for the two checks it now owns (R15); the same-spec rolling-window
  mechanics (`Group:` lines, per-task Touch-disjointness within one
  already-claimed spec) are unchanged and stay prose-driven. A new test,
  `.claude/skills/drain/test_admission_concurrency.py`, replaces task 04's
  single-threaded simulation with real concurrent Python processes
  (`multiprocessing`) racing against shared fixture git repos — proving the
  lease-claim CAS and two-level cap hold under genuine OS-level race
  conditions, not just correct sequential logic (R16). None of this
  requires launching `/drain` itself or a human present, per CLAUDE.md's
  authoring conventions on unattended-worker tool limits.

## Requirements

- R1: Drain's step-1 owner-lease claim procedure claims up to 3
  simultaneously-held spec leases (not 1). A candidate spec is eligible only
  when its dispatchable-task Touch footprint is pairwise disjoint from every
  OTHER CURRENTLY-CLAIMED spec's footprint — the greedy runtime claim
  decision, evaluated against the claimed set as it is built up (mirroring
  how task-level admission already compares against the current in-progress
  set, never the whole queue). The exact phrase "At most one dispatch lease
  is held at a time" is removed from SKILL.md and replaced with a one-line
  pointer to the widened rule's full statement in reference.md — never the
  full rule inline in SKILL.md (R9 governs the line budget).
- R2: The rolling-window admission check (reference.md's "Rolling-window
  admission & merge (R1–R4)") keeps its same-spec semantics — Touch-
  disjointness, `Group:`-line co-admissibility, and "runs only alone
  (window empty)" — fully unchanged for a pair of tasks from the SAME
  claimed spec, with "window empty" now defined as zero OTHER in-flight
  tasks from that task's OWN spec specifically (never the global in-flight
  set across all claimed specs — this is the explicit fix for the
  round-4 finding that an unscoped "window empty" would still force every
  ungrouped task to wait for a global empty window). It gains a NEW
  cross-spec layer: two tasks in DIFFERENT, both-claimed specs are
  co-admissible whenever their `Touch:` sets are disjoint, full stop — no
  `Group:` line and no window-empty check apply across specs (a `Group:`
  line names tasks only within its owning spec's Parallelization section,
  so it cannot apply across specs, and "window empty" per the above is
  never evaluated against a different spec's in-flight set). **Two-level
  cap (round-8 precision fix):** a single claimed spec's own `W` (hard-capped
  at ≤5, unchanged) still bounds how many of THAT spec's own tasks may run
  concurrently — this is not dropped. What IS dropped is treating each
  claimed spec's budget as independently summable across specs; instead all
  claimed specs' dispatchable tasks compete for one shared global window
  capped at ≤10 total live workers across every claimed spec combined,
  admitted via the existing Priority-then-path tie-break across the whole
  pool once it is full — a single spec can never exceed its own `W`, but
  the cross-spec sum is throttled to ≤10 rather than the naive per-spec
  sum. This IS the mechanized fix for the cross-spec task-collision gap
  documented in
  `docs/memory/drain-dispatch-lessons.md:64-80` ("there is no mechanized
  cross-spec check" today) — no separate detection mechanism is needed.
- R3: `.claude/rules/token-discipline.md`'s "cap the fleet at a 3–5
  concurrent-writer window" rule gains an explicit carve-out sentence
  naming drain's multi-spec swarm mode and citing this spec, so the raised
  ≤10 cap is a documented exception rather than a silent doctrine
  violation.
- R4: No-argument `/drain` claims spec leases greedily up to the 3-spec cap
  using the existing Priority-then-path tie-break applied at spec
  granularity; a queue with only one claimable non-overlapping spec
  produces a single claim identical to today's single-spec path (the
  claim-count/identity property the acceptance simulation actually checks —
  a live dispatch-behavior comparison needs a real `/drain` run, which is
  out of reach for an unattended verifier).
- R5: Two ready specs whose Touch footprints intersect are never
  simultaneously claimed; drain serializes only the overlapping pair
  (lower-priority spec's claim waits) while continuing to run every other
  non-overlapping ready spec concurrently.
- R6: R1 (spec-claim eligibility) and R2 (task-admission eligibility)
  together are the complete, sole mechanism for cross-spec Touch collision
  detection — an implementation of this spec must NOT introduce a third,
  separate cross-spec check (e.g. inside `/breakdown`'s own
  decision-coupling test) beyond R1+R2; that would duplicate the same
  algorithm a second way and risk the two diverging.
- R7: When dispatching the spec-completion-review worker (reference.md's
  "Spec-completion review worker") for a spec whose cumulative diff range
  overlaps a path another concurrently-claimed spec has already covered in
  its own committed `evidence/spec-review.md` this run, drain's dispatch
  prompt explicitly names which lines/sections are attributable to THIS
  spec, cites the sibling's `evidence/spec-review.md` by path, and instructs
  the worker to exclude anything that file already covers — never handing
  the full ref-range diff and trusting the worker to guess spec boundaries
  on shared files. This is the exact fix prescribed in
  `docs/memory/drain-dispatch-lessons.md:134-151`, adopted verbatim; the
  diff-base recovery mechanism itself (`merge-base(<pinned flip commit>,
main)..main`) is unchanged.
- R8: Merges across different claimed specs land through one single global
  serial merge queue in commit-arrival order — two specs' DONE verdicts
  arriving near-simultaneously never race on the push, using the same
  "merges stay serial in landing order" guarantee already documented for
  intra-spec merges today.
- R9: `.claude/skills/drain/SKILL.md` ends this spec's implementation at
  ≤500 lines; the new admission-rule prose lives in reference.md's
  "Rolling-window admission & merge (R1–R4)" section (renamed or extended
  to cover R5+ for the cross-spec rules), with SKILL.md carrying only a
  short pointer — never the full widened rule stated inline in SKILL.md.
- R10: The change mirrors per this repo's mirror-procedure-discipline —
  `antigravity/.agents/workflows/drain.md` and
  `codex/.agents/skills/drain/SKILL.md` reflect the same widened
  procedure (load-bearing runtime differences excepted), and
  `.claude-plugin/plugin.json`'s version is bumped. This mirror scope
  covers both the original R1–R12 prose AND, once R15 lands, `admission.py`'s
  live invocation — antigravity's workflow shell-out and codex's real
  SKILL.md invoke `admission.py` the same way they already/will invoke
  `drain_frontier.py` (task 03 ports both waves, sequenced by its own
  `Depends on:`, not a second mirror task).
- R11: Spec-level lease claiming (R1) operates independent of the per-spec
  task rolling-window's "these rules bind only when W > 1" preamble
  (reference.md's admission-rule section opening) — R1 claims up to 3
  non-overlapping specs and each newly-claimed spec dispatches its first
  eligible task immediately, even when drain runs at its default W=1. `W`
  continues to govern only how many tasks run concurrently WITHIN one
  already-claimed spec; it never gates whether multiple specs can be
  claimed and worked simultaneously — without this, an implementer could
  faithfully nest R1 inside the "bind only when W > 1" preamble and ship a
  version where default (W=1) `/drain` never swarms, contradicting R4.
- R12: `.claude/skills/drain/SKILL.md`'s existing "**Hard cap: W ≤ 5** on
  TOTAL live workers" statement (its current single source of truth for
  the total-worker ceiling) is edited to state the per-spec `W ≤ 5`
  ceiling (unchanged, still governs concurrency within one already-claimed
  spec) plus the new shared global `≤10` pool across all claimed specs —
  whether this statement stays in SKILL.md or is relocated into
  reference.md per R9's "relocated as needed," it must not ship
  unreconciled with R2's ≤10 shared-pool cap in either location.
- R13: Task 04's originally-specified single-threaded bash simulation
  (`tests/test_drain_swarm_admission.sh`) is retired without being written —
  the algorithm it would have re-implemented is instead extracted as the
  authoritative, live-invoked Python module `.claude/skills/drain/admission.py`,
  exposing R1's spec-claim eligibility check, R2's two-level cross-spec
  admission cap, and the DRAIN-OWNER.md git-CAS lease-claim protocol
  (reference.md's existing claim algorithm, mechanically unchanged) as
  callable code rather than prose an agent hand-executes.
- R14 (round-10 critique fix): `admission.py` consumes `drain_frontier.py`'s
  JSON output for what that scanner actually emits — the per-spec
  `dispatchable`/`admissible`/`blocked` task lists and their
  Priority/unblocking-power/lexicographic tie-break ordering — so
  `admission.py` never re-derives dependency resolution or per-spec window
  arithmetic. It does NOT source R1's cross-spec Touch-footprint data from
  that JSON: `drain_frontier.py`'s schema (per `specs/drain-frontier-scanner`'s
  own R1) carries only path/priority/tie-break rationale, no per-task
  `Touch:` sets, so footprint computation cannot be sourced from it (round-10
  critique finding — the original wording claimed otherwise and was
  infeasible). Instead, `admission.py` reads each candidate spec's
  dispatchable-task `Touch:` headers directly — the same on-disk source
  `drain_frontier.py` itself reads — and computes the per-spec footprint
  union and pairwise cross-spec disjointness check via a Touch-disjointness
  predicate factored into a new shared helper,
  `.claude/skills/_shared/touch_disjoint.py` (this repo's existing
  `_shared/` convention for cross-skill Python helpers, alongside
  `headers.py`/`viz.py`/`spec_readiness.py`), so this spec's implementation
  does not carry a second, independently-maintained copy of glob-prefix
  Touch-disjointness logic that could silently diverge from
  `drain_frontier.py`'s own internal comparison. `drain_frontier.py` itself
  is not required to adopt this shared helper by this spec (that scanner's
  own spec is already READY and out of this spec's Touch); the shared
  module exists so a future change can converge the two without this spec
  blocking on `specs/drain-frontier-scanner` accepting a new requirement.
- R15: Live `/drain` execution on Claude Code invokes `admission.py` for
  spec-lease claim decisions (R1) and the cross-spec/two-level cap decision
  (R2) — replacing the hand-executed version of those two checks
  specifically. The same-spec rolling-window mechanics (`Group:` lines,
  per-task Touch-disjointness within one already-claimed spec) are
  unchanged and stay prose-driven, exactly as today. SKILL.md's step-1
  prose is rewired to instruct the agent to run `admission.py` by path,
  mirroring `.claude/skills/prioritize/SKILL.md:35`'s proven
  `prioritize_scan.py` invocation pattern; the invocation's supporting
  detail lives in reference.md, with only a short pointer added to
  SKILL.md, so R9's ≤500-line budget is not reopened.
- R16 (round-10 critique fix — scope narrowed to what genuine OS
  concurrency can actually test): A new test,
  `.claude/skills/drain/test_admission_concurrency.py`, uses real OS-level
  concurrency (Python's `multiprocessing`, not simulated sequencing) to spawn
  multiple actual concurrent processes racing against shared fixture git
  repos exercising `admission.py`'s lease-claim CAS protocol — the one part
  of this spec's mechanism that is genuinely subject to multi-process races
  (the hazard this guards against is real: two independent `/drain`
  invocations, or a hung session plus a fresh relaunch, racing against the
  same `DRAIN-OWNER.md` files — the exact scenario
  `docs/memory/concurrent-session-collision.md` documents). It asserts
  under genuine race conditions: (a) two processes racing to claim the SAME
  spec's `DRAIN-OWNER.md` lease — exactly one wins, the loser detects the
  winner's committed claim via the existing re-read-at-HEAD CAS check and
  backs off cleanly (never both proceeding as if they'd won); (b) multiple
  processes racing to claim DIFFERENT specs simultaneously — every
  pairwise-Touch-disjoint spec is admitted up to the 3-spec cap even when
  claims race concurrently, while a colliding pair still serializes (R5)
  under the race, not just in sequential simulation; (c) two processes both
  racing to reclaim the SAME stale lease simultaneously — exactly one
  reclaim commits, matching reference.md's "ALL STALE" reclaim rule (round-10
  fix: the original wording paired a passive, non-racing "holder" against a
  reclaimer, which races against nothing — a genuine reclaim race is two
  simultaneous reclaimers of one stale lease).
  **The shared ≤10 global cap is explicitly NOT part of this multi-process
  test** (round-10 critique finding): unlike the per-spec lease, the ≤10 pool
  is single-orchestrator in-memory bookkeeping — Out of scope already
  forbids persisting it in a new file, and there is only ever one drain
  orchestrator process making admission decisions within one run, so there
  is no second process to race against and no shared, lockable state to CAS
  a count through. That property is proven deterministically instead, by
  task 04's own fixture case (e) (a single-process, sequential assertion
  that the cap throttles correctly) — asserting it via `multiprocessing`
  would either be vacuous (nothing to race) or force `admission.py` to
  invent a persisted counter this spec's Out of scope explicitly rejects.
  This test supersedes task 04's original "Orchestrator-resolvable
  simulation" acceptance criterion (retired below) for the lease-claim CAS
  properties specifically, since it proves them under genuine concurrency
  rather than single-threaded simulated sequencing, while still requiring
  no `/drain` invocation and no human presence.
- R17: This spec's `admission.py`/rewiring work (R13–R16) carries an
  explicit cross-spec dependency on `specs/drain-frontier-scanner`'s task 01
  (`specs/drain-frontier-scanner/tasks/01-scanner-and-tests.md`, the
  `drain_frontier.py` scanner) landing first — the corresponding task files
  below name this dependency in their own `Depends on:` headers using the
  cross-spec path form drain's dependency parsing already supports. If
  `drain-frontier-scanner` is not yet merged when these tasks would
  otherwise be dispatchable, they stay blocked rather than reimplementing
  or guessing at `drain_frontier.py`'s interface. `drain-frontier-scanner`
  task 02 also grows `.claude/skills/drain/SKILL.md` (its own scanner
  invocation, landing before this spec's task 06 per task 06's own
  `Depends on:`) with no `wc -l` acceptance check of its own — round-10
  critique finding: R9's ≤500-line budget is the reconciling backstop for
  BOTH specs' growth, not just this one's, and task 06's `wc -l ≤ 500`
  acceptance check (below) is the one place that bound is actually
  verified after both waves have landed.

## Out of scope

- Building the SQLite atomic-claim coordination layer researched in
  `docs/task-tracking-design-research-2026-07.md` / the not-yet-written
  `specs/task-tracking-hardening` spec. This spec keeps today's git-CAS
  lease mechanism (re-read-before-flip, exact-match edit, commit,
  push, re-confirm at HEAD) and only widens its claim count — it does not
  adopt a new coordination substrate. A future spec may build the SQLite
  layer as a throughput optimization on top of this one; not a
  prerequisite.
- Runtime/automated conflict detection or merge-conflict resolution between
  concurrently-running agents. Per this session's cross-vendor research,
  no reviewed product (Anthropic, OpenAI Codex, Copilot, Cursor, Devin,
  Jules, beads) does this — the avoidance-via-declared-ownership model
  (Touch: disjointness) is the industry-wide answer, and is what this spec
  extends, not replaces.
- `beads`-style DAG/epic fan-out (`bd swarm`) as a new dependency-modeling
  primitive. This repo's `Depends on:` header plus the existing
  dispatchability check already model task dependencies; this spec extends
  concurrency at the spec-claiming layer, not the dependency-graph model.
- Raising the cap beyond ≤10 total workers / 3 simultaneous specs, or
  making the cap budget-governed (`Workflow`-tool-style
  `budget.remaining()`) instead of a fixed number. A fixed, modest cap is
  the deliberate first step; a follow-up spec can revisit if the ≤10/3
  ceiling proves too conservative in practice.
- Any change to the per-spec `DRAIN-OWNER.md` file format itself (R1's
  fields are unchanged) — the cross-spec footprint is recomputed by
  scanning all currently-present `DRAIN-OWNER.md` files and their specs'
  task Touch headers at each admission decision, not persisted in a new
  file.

## Acceptance criteria

- [ ] `grep -c "At most one dispatch lease is held at a time" .claude/skills/drain/SKILL.md`
      → 0 (currently 1, verified absent-after per R1)
- [ ] `grep -ci "swarm" .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md`
      → combined count ≥ 3 (currently 0 in both, per R1/R2/R4)
- [ ] `grep -c "up to 3 simultaneously-held spec leases" .claude/skills/drain/reference.md`
      → ≥ 1 (the pinned phrase from this spec's own R1/Solution wording,
      currently 0 — no discretion on phrasing)
- [ ] `grep -c "≤10\|<= 10\|10 total" .claude/skills/drain/reference.md`
      → ≥ 1 (the raised worker cap is stated explicitly)
- [ ] `wc -l < .claude/skills/drain/SKILL.md` → ≤ 500 (currently 505, per R9)
- [ ] `grep -li "swarm\|cross-spec\|multi-spec" antigravity/.agents/workflows/drain.md codex/.agents/skills/drain/SKILL.md`
      → both files listed (R10 mirror check)
- [ ] plugin.json version is greater than its value at this spec's base
      commit (R10)
- [ ] `grep -A5 -i "already-green" .claude/skills/drain/reference.md | grep -ci "spec-review.md"`
      → ≥ 1 (currently 0 — tightens the R7 check beyond a bare
      "already-green" token match: the sibling-citation instruction in the
      review-fix worker's dispatch-prompt template must co-occur with a
      reference to citing `evidence/spec-review.md` by path, per
      `docs/memory/drain-dispatch-lessons.md:134-151`'s "already-green
      `evidence/spec-review.md`" phrasing — round-4 nit, a bare token match
      was gameable without implementing R7's actual structure)
- [ ] `grep -c "in-flight tasks from that task's OWN spec" .claude/skills/drain/reference.md`
      → ≥ 1 (currently 0, verified — round-5 fix: round-4's original
      pattern `"own spec\|OWN spec"` was vacuous, matching the pre-existing
      unrelated substring "auto-breakd**own spec**s" at reference.md:1570;
      this anchors on a distinctive new literal instead. R2's window-empty
      re-scoping: "window empty" for an ungrouped task must be stated as
      scoped to that task's own spec's in-flight set, never the global set
      — per round-4's finding that an unscoped definition would still
      defeat cross-spec concurrency for ungrouped tasks)
- [ ] `grep -c '"Window empty" means zero live' .claude/skills/drain/reference.md`
      → 0 (currently 1, verified — round-6 fix: round-5's anchor included
      "in-flight workers" on the same grep line, but the phrase wraps
      across a line break in the file (`reference.md:1652-1653`), so the
      full-phrase pattern never matched any single line and returned 0
      before any edit — silently vacuous. This single-line substring is
      confirmed present exactly once today. The existing globally-scoped
      "Window empty" sentence must itself be edited to the re-scoped
      wording above, not left standing unqualified alongside new
      same-spec-scoped prose added elsewhere; round-5 finding — an
      unedited original sentence would contradict the new cross-spec layer
      exactly as round-3/round-4 found for the `Group:` clause)
- [ ] `grep -c "with every in-flight task — two tasks may run together" .claude/skills/drain/reference.md`
      → 0 (currently 1, verified — the existing globally-scoped
      co-admissibility sentence must itself be edited to state the
      `Group:` clause is spec-scoped, not left standing unqualified;
      round-5 finding, same rationale as the window-empty subtractive
      check above)
- [ ] `grep -c "fires independent of the per-spec" .claude/skills/drain/reference.md`
      → ≥ 1 (currently 0, verified — round-5 fix: round-4's original
      pattern's `regardless of W` alternative was vacuous, matching
      pre-existing unrelated tournament-sizing and baton-counter text at
      reference.md:927 and :1132; this anchors on a distinctive new
      literal instead. R11: spec-level lease claiming is stated explicitly
      as firing independent of the per-spec task rolling-window's "bind
      only when W > 1" gate — per round-4's finding that nesting R1 under
      that gate would leave default (W=1) `/drain` never swarming,
      contradicting R4)
- [ ] `grep -c "Hard cap: W ≤ 5.*on TOTAL" .claude/skills/drain/SKILL.md`
      → 0 (currently 1, verified present at SKILL.md:144 — R12: SKILL.md's
      existing authoritative "Hard cap: W ≤ 5 on TOTAL live workers"
      statement is the current single source of truth for the total-worker
      ceiling and directly contradicts the new ≤10 shared-pool cap;
      round-5 finding — reference.md alone stating ≤10 is not enough while
      SKILL.md still asserts ≤5 on TOTAL, whether that statement stays put
      or is relocated verbatim into reference.md per R9's "relocated as
      needed." It must be edited to state the per-spec W≤5 (unchanged,
      governs concurrency within one already-claimed spec) plus the new
      shared global ≤10 pool across all claimed specs)
- [ ] `grep -c "on TOTAL" .claude/skills/drain/reference.md`
      → 0 (currently 0, verified — round-7 nit: R12's relocation branch
      (the line moving verbatim into reference.md per R9 rather than being
      edited in place) had no acceptance coverage; AC13 alone only checks
      SKILL.md, so a relocated-but-unreconciled "on TOTAL" statement could
      land in reference.md uncaught. This is a same-value guard: 0 today,
      and it must stay 0 after the change too, since the reconciled
      statement's own wording — per-spec `W≤5` plus a separate shared
      global `≤10` pool — never needs the phrase "on TOTAL")
- [ ] `grep -ci "shared global window\|one shared global\|shared pool" .claude/skills/drain/reference.md`
      → ≥ 1 (the ≤10 cap is stated as one shared pool across all claimed
      specs, replacing the assumption that each claimed spec's budget sums
      independently — currently 0, per round-4's cap-composition finding)
- [ ] `grep -c "W ≤ 5" .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md`
      → combined count ≥ 1 (currently 1, all from SKILL.md:144, verified —
      round-8 fix: the reconciled cap statement must still assert a single
      claimed spec's own `W ≤ 5` ceiling SOMEWHERE, whether it stays in
      SKILL.md or is relocated into reference.md per R9; R2's "two-level
      cap" wording is only correctly implemented if a spec's own
      concurrency limit survives the ≤10 shared-pool change rather than
      being silently dropped — a worker that ships a flat ≤10 window with
      no surviving per-spec ceiling would otherwise pass every other
      criterion in this section, since AC13/AC-on-TOTAL only check that the
      OLD combined "on TOTAL" phrasing is gone, never that a per-spec
      ceiling replaces it)
- [ ] `grep -ci "swarm.*10\|10.*swarm\|drain-multi-spec-swarm" .claude/rules/token-discipline.md`
      → ≥ 1 (currently 0, verified — round-5 nit: R3's carve-out must
      co-occur with either the raised cap figure or this spec's slug, not
      merely contain the bare word "swarm" with no reference to the cap it
      authorizes or the spec that authorizes it)
- [ ] `grep -ci "single global serial merge queue\|one single global" .claude/skills/drain/reference.md`
      → ≥ 1 (R8's explicit statement)
- [ ] Every project gate this repo runs at merge time
      (`specs/status.sh`, `claude plugin validate .`, every
      `tests/test_*.sh`, `./bin/check-agent-model-pins`,
      `evals/lint-ultra-gate.sh`, `evals/lint-skill-size-gate.sh`) exits 0
      after the change lands.
- [ ] **Real-concurrency test, not a `/drain`-gated end-to-end check
      (R13–R16; unattended workers cannot launch an execution-stage skill,
      per CLAUDE.md's authoring conventions).** `test -f
.claude/skills/drain/admission.py` and `test -f
.claude/skills/drain/test_admission_concurrency.py` → both exist
      (neither exists today, verified 2026-07-19). `python3
.claude/skills/drain/test_admission_concurrency.py` → exits 0, and its
      stdout separately names each of the THREE lease-claim race scenarios
      it asserted (round-10 fix: narrowed from four to three — the global
      cap moved to task 04's deterministic test, see below)
      (`grep -co 'scenario:'` or equivalent per-case marker → 3), mirroring
      task 04's original "no case passes vacuously" runnable-form
      convention.
- [ ] Same-spec lease contention (R16a): the test spawns two real concurrent
      processes (Python `multiprocessing`, not sequential calls) racing to
      claim the SAME spec's `DRAIN-OWNER.md` lease against a shared fixture
      git repo; the script asserts exactly one process's claim is ever
      committed and the loser's own return value reports the CAS rejection
      (never both processes reporting success).
- [ ] Cross-spec simultaneous claims (R16b): the test spawns processes
      racing to claim 3 mutually Touch-disjoint fixture specs plus a 4th
      overlapping one, concurrently; asserts all 3 disjoint specs admit
      (R1/R4) and the colliding pair still serializes (R5) even though the
      claims raced rather than running in sequence.
- [ ] Stale-lease reclaim race (R16c, round-10 respecification): the test
      spawns TWO processes simultaneously racing to reclaim the SAME stale
      fixture lease (not a passive holder against one reclaimer — that pair
      races against nothing); asserts exactly one reclaim commits, matching
      reference.md's "ALL STALE" reclaim rule.
- [ ] The global ≤10 worker cap (task 04's fixture case (e), NOT part of
      `test_admission_concurrency.py` — round-10 finding: this bound is
      single-orchestrator in-memory bookkeeping with no persisted shared
      state to race against, and Out of scope forbids inventing one) stays
      covered by task 04's own deterministic acceptance criteria (unchanged
      from the original task-04 fixture case (e)).
- [ ] `admission.py` consumes `drain_frontier.py`'s JSON output rather than
      recomputing per-spec dispatchable/admissible sets itself (R14) — a
      unit test (in `admission.py`'s own test file or
      `test_admission_concurrency.py`) asserts `admission.py` is invoked
      with (or itself invokes) `drain_frontier.py` and fails loudly if
      `drain_frontier.py` is absent, rather than silently falling back to a
      duplicate per-spec computation.
- [ ] `grep -c "admission.py" .claude/skills/drain/SKILL.md
.claude/skills/drain/reference.md` → combined count ≥ 2 (currently 0
      in both, verified 2026-07-19 — R15's live-invocation rewiring)
- [ ] `wc -l < .claude/skills/drain/SKILL.md` → ≤ 500 after R15 lands (R9's
      budget is not reopened by the admission.py pointer)
- [ ] R6's negative constraint: `git diff --name-only <base-commit>..HEAD |
grep -c '.claude/skills/breakdown/\|antigravity/.agents/workflows/breakdown\|codex/.agents/skills/breakdown/'`
      → 0 — this spec's implementation touches no `/breakdown` files at all,
      confirming no second cross-spec detection mechanism was added there.

## Open questions

(none — resolved via interview: architecture = extend /drain directly;
overlap handling = serialize only the colliding pair; scope = fold in
drain-dispatch-lessons hazards; rigor = production; cap = ≤10 workers / ≤3
specs, doctrine carve-out required)

## Parallelization

Task 01 (the core admission-model rewrite in `.claude/skills/drain/{SKILL.md,reference.md}`,
design fully pinned — round-10 nit: its `Status:` header is `pending` on
`main` as of this revision, since its implementation landed on the separate
`drain-orchestrator-run` branch and has not yet merged back; tasks 03/06
below correctly stay blocked on it until that merge happens) is
Touch-disjoint from task 02 (`.claude/rules/token-discipline.md`) —
neither shares undecided design, since the algorithm is fully pinned by this
spec after 9 critique rounds. Round-10 revision (R13–R17) reshapes the rest
of the queue:

- Task 04 (revised: `.claude/skills/drain/admission.py`) carries a
  cross-spec `Depends on:` against `specs/drain-frontier-scanner`'s task 01
  (R17) — it cannot start until `drain_frontier.py` exists, since
  `admission.py` consumes its JSON output (R14). It is otherwise
  Touch-disjoint from task 02.
- Task 05 (new: `test_admission_concurrency.py`) depends on task 04 — the
  concurrency test exercises `admission.py`, so it cannot be written first.
  Touch-disjoint from task 02.
- Task 06 (new: SKILL.md/reference.md invoke `admission.py`) depends on
  task 01, task 04, and carries a cross-spec `Depends on:` against
  `specs/drain-frontier-scanner`'s task 02 — both tasks touch the same
  step-1 prose in `.claude/skills/drain/{SKILL.md,reference.md}`, so they
  must sequence rather than land as conflicting concurrent edits.
- Task 03 (mirrors + version bump) now depends on task 01 AND task 06 — it
  ports both the original R1–R12 prose and, once task 06 lands,
  `admission.py`'s invocation. Still Touch-disjoint from task 02 and task 05.

- Group: 01, 02
- Group: 02, 04
- Group: 02, 05 (after 04 lands)
- Group: 02 alone once 04/05/06/03 are serialized behind their own
  cross-spec and same-file dependencies
