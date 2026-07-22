# agentic dynamic workflows: dispatch, run, watch

Breakdown-ready: false
Rigor: production

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
   state, queued-vs-started, attempt, last event, tokens, elapsed —
   and workboard renders the same stream in the browser.
7. Every run files a tracker issue (script hash, budget, actuals);
   findings a workflow keeps become tracker tasks linked
   `discovered-from` the run issue. Ultracode results evaporate;
   ours land in the queue with provenance.
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
- The budget pool meters output tokens and is shared with the main
  conversation; `budget.total` is null unless a directive sets it.
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
- **DW2 — dispatch is tracker-silent.** It meters and journals but
  never writes bd, so concurrency needs no lock and D8's single
  writer holds. Only `run` start/finish/checkpoint and `verdict`
  touch the tracker, through the existing write path.
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
  maps them; no retroactive edits.
- **DW5 — Structural caps replace prose fleet doctrine.** Enforced
  in the CLI, configured in the profile: per-run concurrency
  (default 10), dispatch depth (AGENTIC_RUN_DEPTH, max 2), per-run
  agent lifetime cap (default 200). The token-discipline fleet
  windows and nesting bans become config the rules-shrinkage task
  deletes as prose. Ultracode's own caps (16-concurrent, 1000
  lifetime, one nesting level) are the precedent that enforced
  beats advised.
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
  for doing work.
- **DW9 — Tier aliases only.** `--tier scout|session|deep|frontier`
  maps to model+effort in the runtime profile; a profile without a
  pin inherits the session default. Matches the existing
  tier-language convention and the observed alias resolution.
- **DW10 — The progress stream is part of the contract.** Typed
  events with the observed field set, appended beside the journal;
  `watch` is a file-tailing renderer, so it works over SSH, in any
  terminal, and in workboard, with no coupling to any harness UI.
- **DW11 — Caps, not opt-in keywords.** A dynamic run needs no
  ultracode-style keyword: it is allowed by default under its pool
  (D1 extended), and the injection screen applies to any
  tracker-sourced text entering a dispatch prompt (R-S at this
  boundary too).
- **DW12 — Native ultracode is an adapter accelerator only.** On
  Claude Code, tracker-free research fan-outs MAY use the native
  Workflow tool; anything that files tasks, claims work, or must be
  cost-attributed runs through `agentic` so there is exactly one
  ledger and one provenance chain (D11 applied).

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
  enforced with clean errors, values from the profile.
- **RW-V:** `watch` renders a recorded fixture stream to a stable
  golden output (phases, rows, states); live mode is the same
  renderer tailing the file.
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
      exit 0.
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
      task-scoped dispatch refuses on exhausted budget_tokens.
- [ ] RW-C: `tests/test_agentic_run_caps.sh` — depth-3 nesting
      refused; concurrency above the profile cap queues, not
      launches; agent-cap crossing refuses.
- [ ] RW-V: `tests/test_agentic_watch.sh` — renders the committed
      fixture progress stream; diff against golden output is empty.
- [ ] RW-T: unit test — tier alias resolves per fixture profile;
      unknown tier warns and uses the session default.
- [ ] RW-D: `tests/test_agentic_run_tracker.py` — a fixture run
      files its run issue, writes final actuals to metadata, and a
      kept finding lands `discovered-from` the run issue.

## Sequencing

Depends on core tasks 04 (verdict machinery, write path) and 07
(composer, meter, screen); breakdown should be run only after those
are done or in flight. Convergence noted: this feature IS arm S′
from specs/skills-vs-ultracode-eval — once `run` exists under caps,
the follow-up measurement compares like with like.

Next stage: /critique specs/agentic-dynamic-workflows/SPEC.md, then
/breakdown (human-launched, after core tasks 04 and 07 land).
