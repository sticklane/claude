# Agentic core redesign: one CLI, composed dispatch, beads substrate, budgets over gates

Breakdown-ready: false
Rigor: production

## Problem

A full-system audit (2026-07-21, evidence in EVIDENCE.md) found one root
disease expressed four ways:

1. **Flow control lives in prose.** Code owns the read-side math
   (`drain_frontier.py`, `admission.py` — tested), but the actual run
   loop — dispatch, verdict routing, window top-up, baton arithmetic,
   status CAS, recovery — is ~2,500 lines of drain prose the model
   re-interprets each generation. Every drain incident to date is a
   skipped or misremembered prose step; every fix so far is more prose.
2. **State has no schema.** The machine-readable surface is ~a dozen
   `Key: value` header lines parsed by four separately-maintained
   regexes; verdicts, handoffs, evidence, and memory are free prose
   re-parsed by frontier models, with the same conventions restated
   4–6× across three runtime mirrors. No validator exists anywhere.
3. **Handoffs are hedges.** Five artifacts encode "what next" for one
   drain run (Status headers, DRAIN-BATON.md, DRAIN-OWNER.md, a
   HANDOFF file, HUMAN.md) and can diverge; resume rituals re-derive
   state the artifacts already encode. Drain is "resumable by
   definition" from Status headers — the extra artifacts exist because
   a prose loop loses its place.
4. **Gates sit at category boundaries, not cost boundaries.** 24 draft
   stubs across 9 finished specs are parked on manual promotion; cheap
   revertible actions (/prioritize) carry the same launch ceremony as
   15×-cost fleet launches.

Downstream symptoms: the entire active backlog is the toolkit patching
its own machinery; the mirror chain is 3× hand labor guarded by a gate
that admits it cannot catch the failure modes; ctx — a finished,
validated tool — saw ~1 organic use in 14 sessions and zero subagent
uses ever, because doctrine said "prefer" while grants, caches, and
dispatch prompts all said grep.

The operator context bounds the solution: this is an early, single-user
repo optimized for the maintainer's understanding and productivity. The
one hard requirement is **generic support for any AI agent runtime**.
Big changes are explicitly authorized; enterprise-shaped coordination
machinery is explicitly not required.

## Decided doctrine changes

These supersede the corresponding rules text; the migration (below)
rewrites `.claude/rules/` to match. Each entry names what it replaces.

1. **Budgets, not gates.** Spend caps + irreversibility checks replace
   launch-authorization contracts and approval gates
   (docs/human-gates.md's framework retires). Human surfaces converge
   to one inbox: answer, veto, budget, prioritize.
2. **Procedure lives in code; prose is for judgment and
   context-management doctrine only.** A rule that can be mechanized
   moves into the CLI/composer/hooks; one that can't is either context
   doctrine (keep) or dead letter (delete).
3. **Buy the commodity; build only the judgment layer; every bought
   component sits behind an owned interface with its data recoverable
   from git.** Tracker: beads. No shadow rebuilds — "bd-lite" is
   explicitly dead, including as a named fallback; the insurance is
   data portability + the wrapper interface, not a standby
   implementation.
4. **Defaults are the only doctrine that executes.** Adoption is
   engineered — injection, grants, schemas — never requested in prose.
   (Empirical basis: 0% compliance with "prefer ctx" hints.)
5. **One CLI surface, runtime-generic.** All runtime directories —
   including `.claude/` — become thin adapters over the CLI. Nothing is
   hand-mirrored; the port chain and its guard machinery are deleted.
6. **Lightweight by default; the pipeline is for queues.** One session,
   one task, direct build is the default path; multi-agent drain is the
   opt-in for genuinely parallel queues (multi-agent ≈ 15× tokens).
7. **Write for the actual reader.** Machine-consumed artifacts get
   schemas; the human gets one small inbox surface. "Human-readable
   prose everywhere" mis-identified the reader — most artifacts are
   read by models tens of times per human read.
8. **Unchanged:** untrusted-data screening; fresh contexts resumable
   from disk; tiering-as-config; TDD for machinery code; behavior-CI
   measures all of the above.

## Decision record

- **Substrate: beads (`bd`), wrapper-fronted.** Considered: continue
  markdown-only (rejected: it is the no-schema status quo), build our
  own tracker ("bd-lite", rejected: rebuilds a maintained commodity,
  and our own machinery-churn record is worse than upstream's), adopt
  beads directly with agents calling `bd` (rejected: no home for our
  load-bearing fields; no seam to swap or screen). Chosen: all agents
  talk to `agentic`, which fronts a version-pinned `bd` and owns the
  schema extensions, verdicts, admission, screening, and budgets.
- **No pilot program; hands-on verification instead.** The maintainer
  struck the multi-week pilot; in its place a same-day battery against
  the real binary (v1.1.0) verified schema fit, ready/graph semantics,
  per-command latency, export fidelity, and git-integration behavior.
  Results in "Substrate verification" below; anything the battery
  falsifies amends this record rather than silently shipping.
- **Concurrency is a design requirement, not a day-one experiment.**
  Requirement R-C below states it; the architecture additionally keeps
  tracker writers at one process (see component 3), so beads' embedded
  single-writer mode suffices until a topology change adds writers.
- **Claude Code-native task/team features are adapters, not the core**
  — they fail the any-runtime requirement. Same for the Workflow tool.

## Target architecture

Six components. The first two carry almost all of the leverage.

### 1. `agentic` — the one CLI

A single tested binary/package fronting all agent-facing machinery.
Tracker verbs wrap `bd`; nothing else in the system may invoke `bd`
directly.

- `agentic ready` — Touch-disjoint admissible set over `bd ready`
  (absorbs `drain_frontier.py`'s ordering + co-admission; the window
  math survives, re-pointed).
- `agentic claim <id>` — atomic claim via bd, stamped with run
  identity (absorbs the per-task CAS status flip; DRAIN-OWNER lease
  logic reduces to what bd cannot express, if anything).
- `agentic verdict <id> --json` — validates a schema'd worker verdict
  (DONE/BLOCKED/DEFERRED + typed Unblock + Discovered list), writes
  tracker state, files discovered work as issues with
  `discovered-from` edges.
- `agentic resume` — prints the current frontier + in-flight claims;
  replaces DRAIN-BATON.md, HANDOFF machinery for drain, and the
  flip-commit grep. Resume is a query.
- `agentic compose <task-id>` — see composer, below.
- Schema enforcement on write: Touch/Rigor/Budget live in bd's native
  `--metadata` JSON field (typed arrays/ints, queryable via
  `--metadata-field`, lossless through export — battery A3), with
  optional `rigor:`/`budget:` mirror labels only where cheap
  OR-filtering helps; acceptance criteria use bd's native field.
  Hand-editing tracker state is out; the CLI is the sole writer
  (validator for free).
- Store topology + sync: the bd store lives ONLY in the primary
  checkout (`bd` resolves worktrees to it — battery F12); worker
  worktrees never carry tracker writes. All writes happen in the
  primary checkout, where a post-write hook commits a `bd export`
  JSONL to the primary branch — never inside worker worktrees, so
  drain's whitelist merge is untouched. The committed JSONL is the
  canonical publish/bootstrap path (ordinary git suffices);
  `bd dolt push`/`bd bootstrap` is an optional accelerator where a
  Dolt remote exists.
- ctx remains its own binary for now but adopts the same surface
  conventions; folding it into `agentic` as a subcommand is a later,
  optional unification.

### 2. The composer

One typed module through which every dispatch passes —
`agentic compose <task-id>` emits the complete dispatch envelope:

- worker prompt assembled from the task body + judgment framing,
- tool grants (derived per-dispatch, not frozen in agent frontmatter —
  the ctx lesson),
- injected context: a token-budgeted ctx map slice scoped to the
  task's Touch paths (push, not pull — the Aider lesson),
- model/effort tier from config,
- the verdict JSON schema the worker must return,
- untrusted-data screening of task-body text before it becomes a
  prompt (the stub screen, relocated to the one boundary that
  matters),
- budget metering: the composer refuses to emit once the run's spend
  cap is crossed. The spend signal is layered so the cap binds on
  every R-G runtime and never silently no-ops: true harness telemetry
  where the runtime exposes it (Claude Code transcripts / agentprof),
  otherwise the wrapper's own conservative estimate — it composes
  every prompt and collects every verdict, so it meters
  ceil(bytes/4) per dispatch, over-counting rather than
  under-counting by design (requirement R-M).

The composer is where doctrine 2 and 4 become mechanical: tier pins,
injection, grants, screens, and caps stop being rules text and become
one tested code path. Skills shrink to judgment prompts that call it.

Grant enforceability is runtime-tiered: where the runtime has a
permission primitive (Claude Code settings/frontmatter; adapter
equivalents elsewhere), grants are enforced; on a bare-shell runtime
with none, grants degrade to prompt text and the envelope records them
as UNENFORCED. The floor that holds on every runtime is the composer's
own boundaries — what it injects, schema validation of returns, budget
refusal — none of which depend on a runtime permission system.
Behavior-CI measures bypass rates on unenforced runtimes.

### 3. Drain as a code loop

`while (t = agentic ready --claim-next): compose → dispatch → collect
verdict → agentic verdict`. The loop is a script; the model appears
only inside workers and at judgment escalations (tournament, spec
review). Workers compute and return verdict JSON; only the
orchestrator's loop writes the tracker (`agentic verdict`, primary
checkout) — so tracker writers stay at ONE process regardless of
fleet size, which is what lets R-C ride embedded single-writer mode.
Baton, generation counters, flip-commit recovery, and the five
continuity artifacts are deleted — resume is `agentic resume` in a
fresh session. Deferred questions batch into the inbox as today, but
as tracker records, not prose sections.

### 4. Runtime adapters

`.claude/`, `antigravity/`, and `codex/` each carry: (a) a thin skill/
workflow set that frames judgment and shells out to `agentic`, (b) the
runtime's native hook wiring, (c) an onboarding snippet (the `bd
onboard` pattern). The mirror-procedure rules, the phrase manifest,
parity gates, and mirror-verification sweeps are deleted with the
prose they guarded. `.claude/` loses source-of-truth status; the CLI
is the source of truth.

### 5. The human inbox

One surface (workboard evolution) listing: questions awaiting answers,
items in veto windows (e.g. auto-promoted drafts), budget approvals,
and priority decisions. HUMAN.md's agent-filed section, deferred-
question batches, and draft-promotion queues converge here. Draft
stubs auto-promote on critic READY with a veto window (doctrine 1),
inverting today's opt-in bottleneck (24 parked drafts).

### 6. Behavior-CI

The transcript-review that produced this spec's evidence, productized:
a scheduled cheap-tier audit measuring doctrine compliance — index-vs-
grep ratio, tier violations, verdict-schema conformance, spend against
budgets — filing findings as tracker issues with `discovered-from`
provenance. A default only stays a default if regressions get caught.

## Design requirements

- **R-G (hard): any-agent genericity.** Every workflow must be
  executable by any agent runtime with shell access; runtime-native
  features are optional accelerators only.
- **R-C: 5–10 concurrent workers** on one machine (worktrees + shared
  checkout) with zero lost tracker writes. The architecture keeps
  tracker writers at one process (component 3: workers return
  verdicts, never write), so embedded single-writer mode suffices; if
  a future topology adds writers (multi-session, swarm), the
  documented escalation is `dolt sql-server`, validated then. A claim
  race test guards the claim path at drain-loop integration.
- **R-L: per-command tracker latency ceiling 1s.** Measured (v1.1.0
  embedded, warm, ~15-issue DB): ~0.3s reads, ~0.5s writes — ≈1.5s CLI
  overhead per claim+show+update cycle. Dolt latency is size-sensitive,
  so the acceptance check re-measures at ≥500 issues. The wrapper
  batches where bd allows (`--deps` at create, multi-id update) and
  treats a >1s single call as a regression.
- **R-B: fresh-clone bootstrap ≤ 2 commands** before `agentic ready`
  works, scriptable in a SessionStart/setup hook. Canonical recipe
  works over ordinary git alone: `git clone <url> && agentic init`
  (wrapper-controlled `bd init` + `bd import` of the committed JSONL).
  The battery's `bd bootstrap` (~1s) was verified only against a
  co-located Dolt remote — plain GitHub origins host no Dolt server —
  so it is an optional accelerator, never the canonical path.
- **R-E: state recoverable from ordinary git alone** (the committed
  JSONL export), verified by a round-trip test in CI.
- **R-M: the spend cap binds everywhere.** A live spend signal exists
  on every R-G runtime — harness telemetry where present, the
  composer's conservative estimate otherwise; a dispatch that cannot
  be metered is refused, not run unmetered.
- **R-S: untrusted-data screening** at the compose boundary for all
  tracker-sourced text.
- **R-V: version-pinned substrate**; upgrades are deliberate,
  migration-tested events.

## Substrate verification (hands-on battery, bd v1.1.0, 2026-07-21)

Run live in this container against the real binary (embedded Dolt
backend). Full transcript summarized in EVIDENCE.md.

- **Schema fit: PASS, via metadata not labels.** Labels survive our
  exact strings (`/ * : . -` all safe, exact-match filtering works)
  but silently truncate at 255 chars and comma-split at create;
  `--label-pattern` is broken. bd's `--metadata` JSON field stores
  typed structures (`{"touch":[...],"rigor":"prototype",
"budget_tokens":120000}`), round-trips losslessly, and filters via
  `--metadata-field` / `--has-metadata-key` — the wrapper carries
  Touch/Rigor/Budget there. `acceptance_criteria` is a native field
  and round-trips multiline markdown verbatim; `--design`, `--notes`,
  `--estimate`, `--spec-id` fields also exist.
- **Graph/ready: PASS.** All needed dep types incl. `discovered-from`
  (non-blocking, as required for provenance) and `parent-child`
  (blockage propagates transitively; parent unblocked ⇒ children
  ready). `bd ready --json` is priority-sorted, filterable, and
  `--explain` prints per-issue reasoning. `bd ready --claim` is the
  documented atomic-claim primitive (race behavior untested — R-C).
- **Latency: measured** — see R-L numbers (~15-issue DB; scale check
  deferred to acceptance). `bd init` 3.5s one-time.
- **Export/import: PASS, lossless.** JSONL export carries labels,
  metadata, acceptance criteria, dep types, closed status, and
  preserved IDs; export → fresh init → import → re-export diffed to
  zero differing records. The escape hatch is real (R-E holds). Export
  excludes Dolt branch/commit history — acceptable; issues are the
  contract.
- **Git integration: verified, with one scope caveat.** Tracker state
  is invisible to normal git (clean separation) and does NOT ride
  normal `git push`/`git clone`. `bd dolt push` + `bd bootstrap`
  (~1s) worked against a bare LOCAL remote auto-configured from git
  origin; a plain GitHub origin hosts no Dolt server, so that path is
  unverified off-machine — which is why the committed-JSONL import is
  the canonical publish/bootstrap path (R-B/R-E) and Dolt remotes
  remain an optional accelerator. A fetch refspec for `refs/dolt/*`
  does NOT substitute — bd reads its materialized store, not git refs.
- **Ops caveats the wrapper must own:** `bd init` writes AND
  auto-commits AGENTS.md, CLAUDE.md, `.claude/settings.json`, and
  `.codex/` config into the host repo — the wrapper performs init in
  controlled form and diffs/curates these; `.beads/interactions.jsonl`
  is tracked telemetry that dirties `git status` on every command —
  gitignore it at adoption; npm install is 137M. No daemon lingers;
  no stale locks observed.
- **Not verified (by decision):** multi-writer race behavior — carried
  as requirement R-C with a single-writer architecture that avoids it,
  escalation mechanism validated only if a topology change needs it.

## Migration sequence

Ordered. Each step leaves the system working — steps 2–3 run in shadow
mode precisely so nothing flips until step 4's cutover. The queue
re-triage happens FIRST so no further effort lands on subsumed work.

1. **Re-triage the open queue** against this design: every open
   spec/task marked keep / subsumed / fold-into-design. Known
   subsumed: mirror-procedure machinery, drain self-patch cluster,
   ctx-dispatch-adoption's prompt-stanza tasks (composer replaces).
2. **`agentic` v0 (shadow mode)**: ready/claim/verdict/resume wrapping
   a pinned bd; controlled init (curated side-effect diff,
   `interactions.jsonl` gitignored); JSONL export hook; import the ~37
   live items (8 open, 5 blocked, 24 drafts). Markdown headers REMAIN
   source of truth — the wrapper one-way syncs markdown→bd, and every
   existing reader keeps working unchanged. Done/archived specs stay
   as markdown history.
3. **Composer v0** with verdict schema + grants + ctx map injection +
   screen + budget cap (R-M metering); /build switches to it. From
   this step onward, mirror-manifest rows covering files being
   replaced are marked retired rather than maintained against
   soon-deleted prose.
4. **Drain loop v0 + cutover**: the code loop runs over `agentic`; bd
   becomes source of truth and headers become wrapper-generated;
   markdown-header readers (drain_frontier, list_specs, status.sh,
   prioritize_scan) re-point into the wrapper or retire;
   baton/owner/handoff artifacts retired; evals updated to assert
   loop behavior; the R-C claim race test lands here.
5. **Runtime adapters**: antigravity/ and codex/ convert to thin
   adapters over `agentic` (skills shell out; native hook wiring;
   onboarding snippet); the mirror machinery — procedure manifest,
   parity gates, verification sweeps, both mirror rules files —
   retires in the SAME step.
6. **Gates→budgets**: rules rewrite (delete launch contracts, add cap
   config), inbox v0 with veto-window promotion.
7. **Behavior-CI v0**: scheduled audit + auto-filed findings.
8. **Rules shrinkage**: classify every rules line per doctrine 2;
   delete or mechanize; target end-state ≈ untrusted-data + context
   antipatterns + CLI pointers.

## Acceptance criteria

Spec-level runnable checks, one per requirement; breakdown tasks
derive their `## Acceptance` from these. Anchors verified against
current state: no `agentic` entrypoint and no `tests/test_agentic_*`
file exists in the repo today, so none of these can pass vacuously.

- [ ] R-G: `tests/test_agentic_generic.sh` exercises
      ready→claim→compose→verdict→resume end-to-end in a bare shell
      (no MCP, no runtime-native tools); exit 0.
- [ ] R-C: `tests/test_agentic_claim_race.sh` races 8 concurrent
      `agentic claim` calls on one issue; asserts exactly one winner
      and zero lost writes from post-state; lands with migration
      step 4.
- [ ] R-L: `tests/test_agentic_latency.sh` seeds ≥500 issues; median
      `agentic ready` wall time over 5 runs < 1s.
- [ ] R-B: `tests/test_agentic_bootstrap.sh` clones into a temp dir,
      runs the documented ≤2-command recipe, asserts `agentic ready`
      exits 0 reporting the imported issue count.
- [ ] R-E: `tests/test_agentic_roundtrip.sh` rebuilds the tracker
      from the committed JSONL alone (fresh init + import); re-export
      diffs to zero differing records.
- [ ] R-M: unit test — with harness telemetry absent, the estimate
      meter accumulates and `agentic compose` hard-refuses once the
      cap is crossed.
- [ ] R-S: `tests/test_agentic_screen.sh` feeds `agentic compose` an
      issue whose description embeds a screen-stub fixture injection
      string; compose refuses or neutralizes, asserted on output.
- [ ] R-V: unit test — the wrapper refuses to run against a bd
      version other than the pin, with a clear upgrade pointer.

## Risks

- **Upstream churn (beads).** Storage layer changed twice in 5 months;
  live migration footguns exist. Mitigation: version pin (R-V), sole
  access through the wrapper, committed JSONL (R-E). Accepted residual:
  a future forced migration costs a bounded integration sprint.
- **Schema-fit residuals (battery-bounded).** The label plan's risks
  materialized in testing (silent 255-char truncation, comma-split,
  broken `--label-pattern`) and are AVOIDED by carrying structured
  fields in bd's metadata JSON instead; labels are optional mirrors
  only. Residual integration hazards the wrapper must own: `bd init`'s
  uninvited writes + auto-commit into the host repo, and the tracked
  `interactions.jsonl` telemetry (gitignored at adoption).
- **Composer as single point of failure.** A composer bug affects
  every dispatch (vs stochastic prose failures). Accepted
  deliberately: deterministic, testable, fixable-once beats
  stochastic-and-invisible — but it obligates unit tests + evals on
  the composer path as first-class, not afterthought.
- **Adoption of `agentic` itself.** The ctx failure mode applies to
  our own CLI. Mitigation is structural, not prose: the composer is
  the only dispatch path, grants are composed in, and behavior-CI
  measures bypass rates from day one.
- **Solo-operator budget errors.** Budgets replace approval gates;
  a mis-set cap can overspend, and estimate-based metering (R-M) can
  drift from true cost. Mitigation: conservative default caps,
  over-counting estimates, spend surfaced in the inbox, hard refusal
  at cap in the composer.

## Open questions

- Wrapper language: Python (matches existing tested modules; slower
  startup) vs Go/Rust (single static binary; rewrite cost). Leaning
  Python v0 absorbing existing code; bd itself costs 0.3–0.5s/call, so
  wrapper startup is not the bottleneck — revisit only if R-L fails.
- Verdict transport: file-based JSON vs stdout capture per runtime —
  adapter-level detail, decided during composer v0.
- Whether ctx folds into `agentic` as a subcommand (one binary) or
  stays sibling with shared conventions.

Next stage: /breakdown specs/agentic-core-redesign/SPEC.md
(human-launched, after Breakdown-ready flips on review of the
critique-fix pass).
