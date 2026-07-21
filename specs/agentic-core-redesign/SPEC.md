# agentic: a tested CLI that runs the agent work pipeline

Breakdown-ready: false
Rigor: production

## What we are building

`agentic` — one tested command-line program (Python v0) that owns the
mechanical half of agent-driven development, plus the small set of
pieces around it. The CLI:

- tracks work as a dependency graph, wrapping the beads issue tracker
  (`bd`, version-pinned) behind our own interface — agents and skills
  never call `bd` directly;
- computes what is ready to work, claims it atomically, and records
  worker results as JSON verdicts validated against a schema;
- composes every worker dispatch: the prompt, an injected code-map
  slice, tool grants, the model tier, the verdict schema, an
  injection screen, and a spend check, in one envelope;
- runs the drain loop as code — dispatch, collect, record, repeat —
  with the model appearing only inside workers and at explicit
  judgment points;
- enforces spend budgets, refusing to dispatch past a cap;
- syncs all tracker state through ordinary git: every write commits a
  JSONL export, and a fresh clone rebuilds from it with one command.

Around the CLI: a thin adapter per agent runtime (Claude Code,
Antigravity, Codex) that shells out to it; one human inbox for
questions, vetoes, budget changes, and priorities; and a scheduled
behavior audit that measures whether the machinery is actually being
used and files regressions as tracker issues.

What stays hand-written: judgment prompts (what good work looks
like), context-management guidance, and the untrusted-data rule.
Everything procedural lives in the CLI and its tests.

## Why

Four measured failures of the current prose-based machinery (all
numbers and pointers in EVIDENCE.md):

1. The run loop is ~2,500 lines of skill prose a model re-interprets
   every generation, and it skips steps: every drain incident to date
   is a missed prose step, and every fix so far has been more prose.
   Code cannot skip a step; prose demonstrably does.
2. State has no schema — a dozen header lines parsed by four
   separately-maintained regexes, everything else free prose that
   frontier models re-parse on every pass, restated 4–6× across three
   hand-mirrored runtime trees. There is no validator anywhere.
3. Resumption is five overlapping artifacts (Status headers, baton,
   lease file, handoff file, HUMAN.md) that exist because a prose
   loop loses its place. A code loop's resume is a query.
4. Human approval gates sit at category boundaries instead of cost
   boundaries: 24 ready drafts are parked on manual promotion while
   cheap revertible actions carry launch ceremony. For a solo
   operator, spend caps protect better than approvals and don't
   block the queue.

The binding constraint: any AI agent runtime with shell access must
be able to run the whole pipeline. That is why the core is a CLI and
runtime-native features are optional accelerators.

## How

Standard tools, standard patterns, as little invention as possible:

- **Buy the tracker, own the interface.** beads provides the
  dependency graph, ready-work computation, atomic claims,
  `discovered-from` provenance edges, and memory compaction. Our
  wrapper owns the schema (Touch/Rigor/Budget in bd's typed metadata
  field), validation on write, screening, and budgets — so the
  substrate is swappable and its quirks are contained.
- **Design decisions are recorded as decisions** (below, ADR-style:
  decision, context, consequence) — not doctrine prose scattered
  across rules files.
- **Industry practice over bespoke convention:** JSON Schema for
  verdicts and dispatch envelopes; conventional CLI shape
  (subcommands, `--json`, meaningful exit codes); a single-writer
  data topology instead of distributed-write cleverness; pinned
  dependencies with a reproducible bootstrap; unit + integration
  tests in CI for every mechanical path (the same discipline that
  already covers `drain_frontier.py` and `admission.py`, extended to
  the loop those modules feed).
- **Git is the only transport.** Tracker state travels as a committed
  JSONL export and rebuilds from it. bd's embedded Dolt storage
  engine is an internal implementation detail of bd; its remote-sync
  machinery (`bd dolt push`, `bd bootstrap`, Dolt remotes) is not
  used at all (decision D9).

## Design decisions

Each: the decision, why, and what it costs. These supersede the
corresponding rules text; migration step 8 rewrites `.claude/rules/`
to match.

- **D1 — Spend budgets replace approval gates.** Why: solo operator;
  approvals blocked the queue (24 parked drafts) without preventing
  the measured cost leaks. Consequence: a mis-set cap can overspend
  before a human looks; mitigated by conservative defaults,
  over-counting meters, and hard refusal at cap (R-M).
- **D2 — Procedure lives in code; prose is for judgment and context
  guidance.** Why: 0% compliance with prose "prefer X" hints;
  skipped prose steps caused every drain incident. Consequence: a
  bug in shared code hits every run — accepted because deterministic
  failures are testable and fixed once; obligates first-class tests.
- **D3 — beads is the tracker; no shadow rebuild.** Why: it solves
  ready/claim/provenance/compaction better than our markdown
  machinery, and our own churn record in this layer is worse than
  upstream's. "bd-lite" is dead including as a named fallback; the
  insurance is the owned interface plus the JSONL in git.
  Consequence: upstream churn risk (storage changed twice in five
  months), contained by version pinning (R-V).
- **D4 — Adoption is engineered, never requested.** Injection,
  grants, and schemas instead of "prefer" prose. Why: the ctx case
  study — a finished tool at near-zero utilization because every
  surface defaulted to grep. Consequence: the composer must exist
  before the habits it replaces can be deleted.
- **D5 — The CLI is the source of truth; runtime directories are
  thin adapters.** Why: three hand-mirrored prose trees drift, and
  the guard machinery admits it can't catch the failure modes.
  Consequence: the mirror chain and its guards are deleted, and
  `.claude/` loses its privileged status.
- **D6 — Single session, single task is the default; the multi-agent
  pipeline is opt-in for parallel queues.** Why: multi-agent costs
  ~15× tokens and most personal work is coupled, not parallel.
- **D7 — Machine-consumed artifacts get schemas; the human gets one
  inbox.** Why: models read these artifacts tens of times per human
  read; prose optimized for a reader who rarely shows up.
- **D8 — One tracker writer.** Workers return verdict JSON; only the
  orchestrator's loop writes state, from the primary checkout. Why:
  eliminates the multi-writer problem instead of solving it, and
  keeps worker worktrees free of tracker side effects. Consequence:
  a future multi-session topology needs bd's server mode, validated
  then (R-C).
- **D9 — Git is the only sync transport; the Dolt remote path is
  rejected.** Why: it is a second sync system, unverified against
  real (non-Dolt) origins, and the committed JSONL already carries
  full state losslessly. Consequence: none for a solo single-machine
  operator; revisit only if a genuinely distributed topology appears.
- **D10 — No pilot; hands-on verification instead.** The substrate
  was exercised against the real binary the same day (battery below);
  anything it falsifies amends these decisions rather than silently
  shipping. Concurrency is a stated requirement (R-C), not a day-one
  experiment.
- **D11 — Runtime-native task/team features (Claude Code teams,
  Workflow tool) are adapter accelerators, never the core.** Why:
  they fail the any-runtime constraint.

## Target architecture

Six components. The first two carry almost all of the leverage.

### 1. `agentic` — the CLI

- `agentic ready` — Touch-disjoint admissible set over `bd ready`
  (absorbs `drain_frontier.py`'s ordering + co-admission).
- `agentic claim <id>` — atomic claim via bd, stamped with run
  identity (absorbs the per-task CAS status flip and lease logic).
- `agentic verdict <id> --json` — validates the worker verdict
  against its JSON Schema (DONE/BLOCKED/DEFERRED, typed Unblock,
  Discovered list), writes tracker state, files discovered work with
  `discovered-from` edges.
- `agentic resume` — prints frontier + in-flight claims; replaces the
  baton, drain's handoff files, and the flip-commit grep.
- `agentic compose <task-id>` — the composer (component 2).
- `agentic init` — controlled bootstrap: wraps `bd init` (curating
  its side effects), imports the committed JSONL, gitignores bd's
  telemetry file.
- Schema on write: Touch/Rigor/Budget in bd's metadata JSON (typed,
  queryable, lossless through export — battery A3); acceptance
  criteria in bd's native field; the CLI is the sole writer, so
  validation happens at the only write path.
- Sync: every tracker write commits a fresh `bd export` JSONL to the
  primary branch from the primary checkout — never from worker
  worktrees, so drain's whitelist merge is untouched. No Dolt
  remotes (D9).
- ctx stays a sibling binary with the same surface conventions;
  folding it in later is optional.

### 2. The composer

`agentic compose <task-id>` emits the complete dispatch envelope:

- worker prompt assembled from the task body + judgment framing,
- tool grants derived per-dispatch (not frozen in agent frontmatter),
- injected context: a token-budgeted ctx map slice scoped to the
  task's Touch paths — pushed into the prompt, not offered as a tool,
- model/effort tier from config,
- the verdict JSON Schema the worker must return,
- untrusted-data screening of task-sourced text before it becomes a
  prompt,
- spend check: compose refuses once the run's cap is crossed. The
  spend signal is layered so the cap binds on every runtime: harness
  telemetry where available, otherwise the wrapper's own conservative
  estimate (it composes every prompt and collects every verdict;
  ceil(bytes/4) per dispatch, over-counting by design) — R-M.

Grant enforceability is runtime-tiered: enforced where the runtime
has a permission primitive; recorded as UNENFORCED in the envelope
where it doesn't. The floor that holds everywhere is what the
composer itself controls: injection, schema validation of returns,
and budget refusal. Behavior-CI measures bypass rates.

### 3. The drain loop

`while (t = agentic ready --claim-next): compose → dispatch → collect
verdict → agentic verdict`. A script owns the loop; workers return
verdict JSON and never write the tracker (D8). Baton, generation
counters, flip-commit recovery, and the five continuity artifacts are
deleted — resume is `agentic resume` in a fresh session. Deferred
questions become tracker records surfaced in the inbox.

### 4. Runtime adapters

Per runtime: a thin skill/workflow set that frames judgment and
shells out to `agentic`; native hook wiring; an onboarding snippet.
The mirror-procedure rules, phrase manifest, parity gates, and
verification sweeps are deleted with the prose they guarded.

### 5. The human inbox

One surface (workboard evolution): questions awaiting answers, items
in veto windows, budget approvals, priority decisions. HUMAN.md's
agent-filed section, deferred-question batches, and draft promotion
converge here. Drafts auto-promote on critic READY with a veto
window (D1), inverting today's opt-in bottleneck.

### 6. Behavior-CI

A scheduled cheap-tier audit measuring whether the machinery is used:
index-vs-grep ratio, tier violations, verdict-schema conformance,
spend vs budgets — filing findings as tracker issues with
`discovered-from` provenance.

## Design requirements

- **R-G (hard): any-agent genericity.** Every workflow executable by
  any agent runtime with shell access; runtime-native features are
  optional accelerators only.
- **R-C: 5–10 concurrent workers** on one machine with zero lost
  tracker writes. The architecture keeps tracker writers at one
  process (D8), so bd's embedded single-writer mode suffices; the
  documented escalation for a future multi-writer topology is bd's
  server mode, validated then. A claim race test lands with the
  drain-loop integration.
- **R-L: per-command tracker latency ceiling 1s.** Measured (v1.1.0,
  warm, ~15-issue DB): ~0.3s reads, ~0.5s writes — ≈1.5s overhead per
  claim+show+update cycle. Dolt latency is size-sensitive, so
  acceptance re-measures at ≥500 issues. The wrapper batches where bd
  allows and treats a >1s call as a regression.
- **R-B: fresh-clone bootstrap ≤ 2 commands**: `git clone <url> &&
agentic init` — ordinary git only, rebuilt from the committed JSONL
  (D9). Scriptable in a setup hook.
- **R-E: state recoverable from ordinary git alone**, verified by a
  round-trip test in CI.
- **R-M: the spend cap binds everywhere.** A live spend signal exists
  on every R-G runtime — telemetry where present, the composer's
  estimate otherwise; a dispatch that cannot be metered is refused.
- **R-S: untrusted-data screening** at the compose boundary for all
  tracker-sourced text.
- **R-V: version-pinned substrate**; upgrades are deliberate,
  migration-tested events.

## Substrate verification (hands-on battery, bd v1.1.0, 2026-07-21)

Run live against the real binary (embedded backend). Full summary in
EVIDENCE.md.

- **Schema fit: PASS, via metadata not labels.** Labels survive our
  exact strings but silently truncate at 255 chars and comma-split at
  create; `--label-pattern` is broken. The `--metadata` JSON field
  stores typed structures, round-trips losslessly, and filters via
  `--metadata-field` — Touch/Rigor/Budget live there.
  `acceptance_criteria` is a native field; `--design`, `--notes`,
  `--estimate`, `--spec-id` also exist.
- **Graph/ready: PASS.** `discovered-from` is non-blocking (right for
  provenance); `parent-child` blockage propagates transitively;
  `bd ready --json` is priority-sorted and filterable with
  `--explain`; `bd ready --claim` is the documented atomic claim
  (race untested — R-C).
- **Latency: measured** — R-L numbers; `bd init` 3.5s one-time.
- **Export/import: PASS, lossless.** JSONL carries labels, metadata,
  acceptance criteria, dep types, closed status, preserved IDs;
  export → fresh init → import → re-export diffs to zero records.
  R-E holds. Export excludes Dolt-internal history — fine; issues are
  the contract.
- **Git integration.** Tracker state is invisible to normal git and
  does not ride normal push/clone. bd's own remote sync worked only
  against a co-located local Dolt remote; plain git origins host no
  Dolt server. Design consequence: D9 — the Dolt remote path is
  rejected, committed JSONL is the only transport.
- **Ops caveats the wrapper owns:** `bd init` writes and auto-commits
  AGENTS.md/CLAUDE.md/settings files into the host repo (curated by
  `agentic init`); `.beads/interactions.jsonl` telemetry dirties git
  status (gitignored at adoption); npm install is 137M. No daemon
  lingers; no stale locks observed.
- **Not verified (by decision, D10):** multi-writer race behavior —
  avoided architecturally (D8), escalation validated only if needed.

## Migration sequence

Ordered. Each step leaves the system working — steps 2–3 run in
shadow mode so nothing flips until step 4's cutover. Queue re-triage
happens FIRST so no further effort lands on subsumed work.

1. **Re-triage the open queue** against this design: every open
   spec/task marked keep / subsumed / fold-into-design. Known
   subsumed: mirror-procedure machinery, drain self-patch cluster,
   ctx-dispatch-adoption's prompt-stanza tasks.
2. **`agentic` v0 (shadow mode)**: ready/claim/verdict/resume over a
   pinned bd; `agentic init`; JSONL export hook; import the ~37 live
   items. Markdown headers REMAIN source of truth — one-way sync
   markdown→bd; every existing reader keeps working.
3. **Composer v0**: verdict schema, grants, ctx map injection,
   screen, spend metering (R-M); /build switches to it. From here,
   mirror-manifest rows covering files being replaced are marked
   retired.
4. **Drain loop v0 + cutover**: the code loop runs; bd becomes source
   of truth; headers become wrapper-generated; markdown-header
   readers re-point into the wrapper or retire; baton/owner/handoff
   artifacts retired; evals assert loop behavior; the R-C race test
   lands.
5. **Runtime adapters**: antigravity/ and codex/ convert to thin
   adapters; the mirror machinery retires in the same step.
6. **Budgets + inbox**: rules rewrite (delete launch contracts, add
   cap config), inbox v0 with veto-window promotion.
7. **Behavior-CI v0**: scheduled audit + auto-filed findings.
8. **Rules shrinkage**: classify every rules line per D2; delete or
   mechanize; end-state ≈ untrusted-data + context guidance + CLI
   pointers.

## Acceptance criteria

One runnable check per requirement; breakdown tasks derive their
`## Acceptance` from these. Anchors verified against current state
(no `agentic` entrypoint, no `tests/test_agentic_*` file exists
today), so none can pass vacuously.

- [ ] R-G: `tests/test_agentic_generic.sh` exercises
      ready→claim→compose→verdict→resume end-to-end in a bare shell
      (no MCP, no runtime-native tools); exit 0.
- [ ] R-C: `tests/test_agentic_claim_race.sh` races 8 concurrent
      `agentic claim` calls on one issue; exactly one winner, zero
      lost writes; lands with migration step 4.
- [ ] R-L: `tests/test_agentic_latency.sh` seeds ≥500 issues; median
      `agentic ready` wall time over 5 runs < 1s.
- [ ] R-B: `tests/test_agentic_bootstrap.sh` clones into a temp dir,
      runs `git clone && agentic init`, asserts `agentic ready`
      exits 0 reporting the imported issue count.
- [ ] R-E: `tests/test_agentic_roundtrip.sh` rebuilds the tracker
      from the committed JSONL alone; re-export diffs to zero
      differing records.
- [ ] R-M: unit test — with harness telemetry absent, the estimate
      meter accumulates and `agentic compose` hard-refuses once the
      cap is crossed.
- [ ] R-S: `tests/test_agentic_screen.sh` feeds `agentic compose` an
      issue whose description embeds a screen-stub fixture injection
      string; compose refuses or neutralizes, asserted on output.
- [ ] R-V: unit test — the wrapper refuses to run against a bd
      version other than the pin, with a clear upgrade pointer.

## Risks

- **Upstream churn (beads).** Storage changed twice in 5 months; live
  migration footguns exist. Mitigation: pin (R-V), sole access via
  the wrapper, committed JSONL (R-E). Accepted residual: a forced
  migration someday costs a bounded integration sprint.
- **Schema-fit residuals (battery-bounded).** Label hazards (silent
  truncation, comma-split, broken `--label-pattern`) avoided via
  metadata; remaining integration hazards — `bd init` side effects,
  tracked telemetry file — owned by `agentic init`.
- **Composer as single point of failure.** A bug hits every dispatch;
  accepted per D2, obligating first-class tests and evals on that
  path.
- **Adoption of `agentic` itself.** The ctx failure mode applies to
  our own CLI. Mitigation is structural: the composer is the only
  dispatch path, grants are composed in, behavior-CI measures bypass
  from day one.
- **Budget errors.** A mis-set cap can overspend; estimates can drift
  from true cost. Mitigation: conservative defaults, over-counting
  meters, spend surfaced in the inbox, hard refusal at cap.

## Open questions

- Verdict transport: file-based JSON vs stdout capture per runtime —
  adapter-level detail, decided during composer v0.
- Whether ctx folds into `agentic` as a subcommand (one binary) or
  stays sibling with shared conventions.

Next stage: /breakdown specs/agentic-core-redesign/SPEC.md
(human-launched, after Breakdown-ready flips on review).
