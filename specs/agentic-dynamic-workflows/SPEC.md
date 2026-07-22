# agentic dynamic workflows: dispatch, run, watch

Breakdown-ready: true
Rigor: production
Status: waiting
Unblock: run: test -f specs/skills-vs-ultracode-eval/EVIDENCE.md || echo "parked pending the head-to-head verdict (2026-07-22 worth-it review): native ultracode + per-stage model routing + the beads daily skill covers attended dynamic-workflow needs today; build this only if the eval finding or a load-bearing second runtime or recurring cross-session-resume pain justifies it"

## The design in plain statements

What we are building — three verbs and a substrate that replicate
ultracode's full functionality on any agent runtime:

1. `agentic dispatch` is the single-agent primitive: a prompt (or a
   compose envelope), a result JSON Schema, a model tier, an optional
   worktree — in; a validated JSON result file — out. Invalid returns
   are re-prompted a bounded number of times, then fail typed. It
   never writes the tracker, so any number can run concurrently from
   any host script.
2. Orchestration scripts are plain programs — bash or Python calling
   `agentic dispatch` — parallelized with the language's own
   constructs. There is no embedded interpreter: every runtime
   already has a shell, which is what keeps this model-agnostic where
   ultracode is Claude-Code-only.
3. `agentic run <script>` makes those scripts durable: it assigns a
   run ID, journals every dispatch (append-only `started`/`result`
   events keyed by a versioned content hash), and on re-run replays
   the unchanged PREFIX of dispatches from cache — only the first
   changed call and everything after it runs live. Interruption
   recovery is re-running the script.
4. Budgets are one hierarchical ledger: every dispatch charges the
   run's pool (hard refusal at the cap) and, when executing a
   tracker task, that task's own budget. The journal is the hot-path
   meter; the tracker gets start, checkpoint, and final actuals.
5. Model tiers stay aliases — scout / session / deep / frontier —
   resolved by the runtime profile to a concrete model + effort per
   provider. Core files and scripts never name models.
6. `agentic phase <title>` and `agentic log <msg>` append typed
   progress events; `agentic watch [run-id]` renders the live
   terminal tree — phase boxes, one row per agent with label, tier,
   state, queued-vs-started, attempt, last event, tokens, elapsed.
   (Workboard rendering the same stream in the browser is a later
   consumer — DW10 — not a deliverable of this spec.)
7. Every run files a tracker issue (script hash, budget, actuals);
   findings a workflow keeps become tracker tasks linked
   `discovered-from` the run issue. Ultracode results evaporate;
   ours land in the queue with provenance. Because a run writes the
   tracker, `agentic run` executes from the primary checkout and
   refuses to start anywhere else; `dispatch`'s worktree option
   scopes the dispatched agent only, never the run.
8. Workflows may read the queue (`ready`) and, from the primary
   checkout only, execute it (`claim`/`verdict`) — the drain loop is
   ultimately just the first saved workflow, though core task 08
   ships unchanged and any unification comes later.
9. Structure-shaped fan-out comes from ctx: a script derives its
   work list from `agentic ctx tree --json` (one agent per module),
   and dispatch prompts carry composed code-map slices exactly as
   task dispatches do.
10. Saved workflows are committed files under `scripts/workflows/`;
    the model may author a bespoke script per problem — the model
    owns decomposition, the script owns the loop (decision D2's
    division, which is ultracode's own split).
11. The operator controls live runs: `agentic runs` lists running
    and recent runs; `agentic stop <run-id>` signals a run to halt
    after in-flight dispatches settle (the TaskStop equivalent
    ultracode parity requires); a stopped run resumes later by
    prefix replay, losing nothing journaled.

Why: the queue loop covers pipeline work, but ad hoc orchestration
graphs — fan out N finders, adversarially verify each finding, dedup,
synthesize — need structure invented per problem. Ultracode proves
the shape works and what it needs (schema'd agents, shared budget,
replay, live progress); it is also harness-locked, tracker-blind, and
separately metered — three things this design fixes.

## Live evidence (instrumented runs, 2026-07-22)

Two real ultracode runs were executed and inspected for this design
(full observations in EVIDENCE.md). Facts that shaped decisions:

- Schema enforcement is a StructuredOutput tool injected into the
  subagent, validated at the tool layer with retries. Our portable
  equivalent is validate-and-reprompt at the dispatch layer.
- Tier aliases resolve harness-side (`haiku` → the concrete model
  ID). Ours resolve profile-side — same contract, portable.
- Every workflow agent is a BLANK context: a probe agent flatly
  denied being in a workflow. Prompts must be self-contained — which
  is the composer's existing principle.
- The budget pool is shared with the main conversation and its unit
  is output-scale (inferred from one run's spent() deltas — recorded
  as inference, not load-bearing: the agentic meter is independent);
  `budget.total` is null unless a directive sets it.
- The per-agent floor was ~36k input tokens even for trivial probes —
  fan-out is never free; caps and tiering matter at the floor, not
  just at the frontier.
- The journal is append-only `started`/`result` JSONL with versioned
  content-hash keys; `started` without `result` marks in-flight work.
- Resume is PREFIX replay, verified live: after editing one mid-
  script call, everything before it replayed from cache (zero
  tokens, `cached: true`) and everything after it re-ran even where
  prompts were identical — conservative against dataflow between
  calls. The resume run cost 108,560 tokens vs the original 253,672.
- The progress stream is typed events (phase, agent) carrying label,
  phase index, model, state, queued/started timestamps, attempt,
  last tool, tokens, duration, result preview — the exact field set
  `watch` renders.

## Design decisions

- **DW1 — Host-language scripts, no interpreter.** The orchestration
  layer is bash/python calling CLI primitives. Why: R-G — every
  runtime has a shell; shipping an interpreter re-creates ultracode's
  lock-in in our own binary. Cost: scripts must keep their own
  determinism discipline for replay to help (DW3).
- **DW2 — dispatch is tracker-silent, and that invariant is
  tested.** It meters and journals but never writes bd, so
  concurrency needs no lock and D8's single writer holds. Only `run`
  start/finish/checkpoint and `verdict` touch the tracker, through
  the existing write path from the primary checkout. RW-N exists
  because this is the load-bearing concurrency invariant — a future
  "just log it to bd" convenience must fail a test, not a review.
- **DW3 — Prefix replay, exactly as observed.** Content-hash keys
  identify calls; validity is positional — a changed call
  invalidates everything after it. Why: conservative against
  hidden dataflow (an earlier result can shape a later prompt); it
  is what ultracode ships and it verified live. Cost: identical
  post-edit calls re-run; accepted — correctness over cache hits.
  Scripts get a determinism note (no timestamps/randomness in
  prompts) or they forfeit replay, nothing worse.
- **DW4 — One ledger, hierarchical, token-canonical.** The clash
  with today's mechanisms resolves as: `Budget: N turns` task
  headers become an adapter-derived enforcement detail (a
  tokens-per-turn factor in the profile); the canonical budget is
  `budget_tokens` in task metadata plus the run pool; the meter
  records output tokens plus the estimate where telemetry is absent
  (R-M unchanged), and the cap binds on the recorded measure. The
  13 merged core tasks keep their turn headers — the shadow sync
  maps them; no retroactive edits. The tokens-per-turn factor is
  calibrated from measured session telemetry (agentprof's per-turn
  token distribution), recorded in the profile with its source, and
  re-measured by the audit job — a factor nobody measures is a fudge
  factor.
- **DW5 — Structural caps replace prose fleet doctrine.** Enforced
  in the CLI, configured in the profile: per-run concurrency
  (default 10), dispatch depth (AGENTIC_RUN_DEPTH, max 2), per-run
  agent lifetime cap (default 200). The token-discipline fleet
  windows and nesting bans become config the rules-shrinkage task
  deletes as prose. Ultracode's own caps (16-concurrent, 1000
  lifetime, one nesting level) are the precedent that enforced
  beats advised; our defaults sit deliberately below them — a
  solo-operator repo with an observed ~36k-token floor per agent
  has no business at 1000 — and they are provisional profile
  values, tunable without touching this spec.
- **DW6 — No batons, stated as a closed question.** Batons existed
  because a model orchestrator ages — context accumulates, caches
  re-prime, generations cap at 10. A script orchestrator does not
  age: interruption recovery is prefix replay, pacing is the ledger,
  and there is nothing to hand off. The baton/generation machinery
  (already deleted at core task 09) has no successor in this design
  on purpose; the wake-budget doctrine survives only as guidance for
  attended human sessions.
- **DW7 — beads is the durable half of every run.** Run issues carry
  script hash, pool, and actuals in metadata; kept findings become
  issues `discovered-from` the run issue; the journal and progress
  stream are gitignored derived state (the ctx storage pattern); the
  committed JSONL export carries run history at issue granularity.
  Cost attribution, provenance forensics, and inbox visibility all
  fall out of the tracker for free.
- **DW8 — ctx shapes and briefs the fan-out.** Work lists derive
  from structure queries; dispatch prompts carry Touch-scoped code
  maps via the composer's existing injection. ctx queries are not
  metered — reading the index must never compete with the budget
  for doing work — and RW-B's acceptance asserts a ctx query leaves
  the meter unchanged.
- **DW9 — Tier aliases only, default-cheap inside runs.** `--tier
scout|session|deep|frontier` maps to model+effort in the runtime
  profile. Defaults are position-aware: a tier-less dispatch INSIDE
  a run resolves to scout-tier — fan-out is exactly where the
  inverted tier ladder burned money (the measured
  frontier-model-running-grep incidents) — while a tier-less
  standalone dispatch inherits the session default, since a single
  ad hoc dispatch carries the session's intent. Script authors
  override per stage; the workflow-author skill teaches the
  stage-type mapping (mechanical → scout, judgment → session/deep),
  which is where that guidance lives after rules shrinkage retires
  its prose home. Cost: a judgment-shaped fan-out whose author
  forgets the override gets cheap-model answers — visible in watch
  and the run issue, recoverable by editing the script and
  re-running (prefix replay makes the retry cheap).
- **DW10 — The progress stream is part of the contract; the
  terminal renderer is the deliverable.** Typed events with the
  observed field set, appended beside the journal; `watch` is a
  file-tailing renderer with no coupling to any harness UI.
  Workboard consuming the same stream is a named later consumer, not
  a criterion here — this spec's acceptance covers the terminal path
  only.
- **DW11 — Caps, not opt-in keywords.** A dynamic run needs no
  ultracode-style keyword: it is allowed by default under its pool
  (D1 extended), and the injection screen applies to any
  tracker-sourced text entering a dispatch prompt (R-S at this
  boundary too).
- **DW12 — Native ultracode is an adapter accelerator only, with a
  crisp boundary.** On Claude Code, a fan-out MAY use the native
  Workflow tool only when it is tracker-free in this exact sense: it
  files no issues, claims no tasks, and keeps no findings. The
  moment a result is worth keeping, it enters through `agentic`
  (typically a follow-up `dispatch` or a manually filed issue) — so
  the native path can never quietly become a second ledger or an
  unprovenanced work source (D11 applied; yes, such runs are
  separately metered, which is exactly why they may not touch the
  tracker).

## Requirements

- **RW-G:** dispatch/run/watch runnable end-to-end in a bare shell on
  any runtime with a worker command; no harness-native dependency.
- **RW-P:** dispatch enforces the result schema with ≤2 re-prompts,
  then fails typed; the failure is journaled, never silent.
- **RW-J:** re-running an unchanged script+args replays 100% from
  cache (zero live agents); an edit mid-script re-runs exactly the
  suffix from the first changed call.
- **RW-B:** the pool cap refuses further dispatch when crossed; a
  task-scoped dispatch also refuses when the task's budget_tokens is
  exhausted; both units recorded per dispatch.
- **RW-C:** depth, per-run concurrency, and per-run agent caps are
  enforced with clean errors, values from the profile; the queueing
  assertion uses controlled-sleep stub workers and the journal's
  queuedAt/startedAt fields, never wall-clock racing.
- **RW-N:** dispatch is tracker-silent — concurrent dispatches
  produce zero tracker writes, proven on the store, not assumed.
- **RW-O:** `agentic runs` lists live/recent runs; `agentic stop`
  halts a run after in-flight dispatches settle; the stopped run
  resumes by prefix replay.
- **RW-F:** a `Budget: N turns` task header resolves through the
  profile's calibrated tokens-per-turn factor to the expected
  `budget_tokens`, verified against a fixture profile.
- **RW-V:** `watch` renders a recorded fixture stream to a stable
  golden output. Determinism is specified, not hoped for: the
  fixture carries frozen timestamps plus a pinned stream-end clock
  (elapsed is computed against it, never against now), and the
  renderer runs under pinned `COLUMNS` and `NO_COLOR` for the test.
  Live mode is the same renderer tailing the file.
- **RW-T:** tier aliases resolve from the profile; unknown tier or
  bare profile falls back to the session default with a warning.
- **RW-D:** every run files its tracker issue and final actuals;
  kept findings land as `discovered-from` issues.

## Acceptance criteria

Anchors verified absent today: no `agentic dispatch|run|watch` verb
exists (the core package itself is still landing), and no
`tests/test_agentic_dispatch*`, `test_agentic_run*`, or
`test_agentic_watch*` file exists.

- [ ] RW-G: `tests/test_agentic_dynamic_generic.sh` runs a 3-dispatch
      fixture workflow (stub workers) end-to-end in a bare shell;
      exit 0 AND all three result files exist and validate against
      their schemas — an exit code alone is not the behavior.
- [ ] RW-P: `tests/test_agentic_dispatch.py` — schema pass, schema
      fail with 2 re-prompts then typed failure, journal records the
      failure; asserted on the journal file.
- [ ] RW-J: `tests/test_agentic_run_replay.sh` — run a 5-dispatch
      fixture; re-run unchanged → journal shows 5 cached, 0 live;
      edit dispatch 3's prompt; re-run → journal shows exactly 2
      cached, 3 live (prefix semantics, the observed ultracode
      behavior).
- [ ] RW-B: `tests/test_agentic_run_budget.py` — a pool sized for 2
      of 3 dispatches refuses the third with the typed cap error;
      task-scoped dispatch refuses on exhausted budget_tokens; an
      `agentic ctx` query between dispatches leaves the meter
      reading unchanged (DW8).
- [ ] RW-C: `tests/test_agentic_run_caps.sh` — depth-3 nesting
      refused; with controlled-sleep stub workers, dispatches above
      the profile concurrency cap show journal queuedAt strictly
      before startedAt (queued, not launched); agent-cap crossing
      refuses.
- [ ] RW-N: `tests/test_agentic_dispatch_silent.sh` — export the
      tracker, run 8 concurrent dispatches, re-export; the diff is
      empty, and the write-lock's attempt counter (a facility the
      lock exposes for exactly this test) reads zero.
- [ ] RW-O: `tests/test_agentic_run_stop.sh` — stop a running
      fixture mid-run: in-flight dispatches settle, the journal is
      clean, `agentic runs` shows the stopped state, and a resume
      replays the completed prefix.
- [ ] RW-F: unit test — a fixture task with `Budget: 6 turns` and a
      fixture profile factor of 9000 tokens/turn resolves to
      `budget_tokens: 54000` in the shadow-synced metadata.
- [ ] RW-V: `tests/test_agentic_watch.sh` — renders the committed
      fixture progress stream; diff against golden output is empty.
- [ ] RW-T: unit test — tier alias resolves per fixture profile;
      unknown tier warns and uses the session default.
- [ ] RW-D: `tests/test_agentic_run_tracker.py` — a fixture run
      files its run issue, writes final actuals to metadata, and a
      kept finding lands `discovered-from` the run issue; invoking
      `agentic run` from a git worktree (non-primary checkout) exits
      with the typed refusal before any dispatch launches
      (statement 7's guard, tested).

## Sequencing

Depends on core tasks 04 (verdict machinery, write path) and 07
(composer, meter, screen); breakdown should be run only after those
are done or in flight. Convergence noted: this feature IS arm S′
from specs/skills-vs-ultracode-eval — once `run` exists under caps,
the follow-up measurement compares like with like.

Breakdown obligation, carried forward from the base spec's
breakdown-requirements contract: the coverage table must map every
plain statement (1–11), every DW decision cost, and every RW
requirement to at least one task.

## Parallelization

Groups follow the decision-coupling test and the `- Group:` grammar
pinned in `specs/drain-rolling-window/SPEC.md`'s Parallelization
section (cited, not restated). The spec-level waiting gate was
replaced at breakdown by task-level `Status: blocked` + `Unblock:
run:` headers on the four tasks that genuinely need core work
(01 → core 02, which creates the package and scripts/check.sh
everything here lands in; 02 → core 07; 05 → core 04; 07 → core 05) — nothing auto-flips those; a human or later session re-runs
each check and flips the status. Task 01 becomes the first
dispatchable task the moment core 02 lands. Task 09 is a draft
awaiting human promotion, deliberately.

- Group: 04, 05, 06

## Breakdown coverage

Required by the base spec's breakdown-requirements contract: every
plain statement, decision cost, and requirement maps to a task.

| Item                               | Task(s)                              |
| ---------------------------------- | ------------------------------------ |
| S1 dispatch primitive              | 02                                   |
| S2 host-language scripts           | 08 (example proves the model)        |
| S3 run + prefix replay             | 03                                   |
| S4 hierarchical ledger             | 04                                   |
| S5 tier aliases                    | 02                                   |
| S6 phase/log + watch               | 01, 06                               |
| S7 run issues + checkout guard     | 05, 03 (guard)                       |
| S8 queue bridge / loop-as-workflow | 08; 09 (draft, the unification)      |
| S9 ctx-shaped fan-out              | 08 (example), 02 (map injection)     |
| S10 saved workflows                | 08                                   |
| S11 runs/stop                      | 06                                   |
| DW1 no interpreter                 | 08                                   |
| DW2 tracker-silent + tested        | 02, 04 (RW-N)                        |
| DW3 prefix replay                  | 03                                   |
| DW4 ledger + turns factor          | 04, 07                               |
| DW5 structural caps                | 04                                   |
| DW6 no batons                      | 03 (replay is the successor)         |
| DW7 beads durable half             | 05                                   |
| DW8 ctx briefs + unmetered         | 02, 04                               |
| DW9 tier aliases                   | 02                                   |
| DW10 progress contract             | 01                                   |
| DW11 caps not opt-ins              | 04 (pool default-allow), 02 (screen) |
| DW12 native boundary               | 08 (docs + workflow-author rewrite)  |
| RW-G                               | 08                                   |
| RW-P, RW-T                         | 02                                   |
| RW-J                               | 03                                   |
| RW-B, RW-C, RW-N                   | 04                                   |
| RW-O                               | 06                                   |
| RW-F                               | 07                                   |
| RW-V                               | 01                                   |
| RW-D                               | 05                                   |

Next stage: /build specs/agentic-dynamic-workflows/tasks/01-progress-schema-watch.md or
/drain specs/agentic-dynamic-workflows (human-launched; tasks 02, 05,
07 stay blocked until their core-task gates clear).
