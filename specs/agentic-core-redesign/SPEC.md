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
  Requirement R-C below states it; beads' documented modes (embedded
  single-writer with flock queueing; `dolt sql-server` for true
  multi-writer) are the satisfying mechanisms, selected at integration
  time.
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
- Schema enforcement on write: Touch/Rigor/Budget ride bd labels under
  a wrapper-validated grammar (exact grammar fixed by the battery
  results); acceptance criteria use bd's native field. Hand-editing
  tracker state is out; the CLI is the sole writer (validator for
  free).
- Sync + escape: a post-write hook commits a `bd export` JSONL, so
  full tracker state is recoverable from ordinary git alone, and
  fresh-clone bootstrap follows the battery-verified recipe.
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
- budget metering: the composer refuses to emit when the run's spend
  cap is exhausted.

The composer is where doctrine 2 and 4 become mechanical: tier pins,
injection, grants, screens, and caps stop being rules text and become
one tested code path. Skills shrink to judgment prompts that call it.

### 3. Drain as a code loop

`while (t = agentic ready --claim-next): compose → dispatch → collect
verdict → agentic verdict`. The loop is a script; the model appears
only inside workers and at judgment escalations (tournament, spec
review). Baton, generation counters, flip-commit recovery, and the
five continuity artifacts are deleted — resume is `agentic resume` in
a fresh session. Deferred questions batch into the inbox as today, but
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
- **R-C: 5–10 concurrent workers** against tracker state on one
  machine (worktrees + shared checkout) without corruption; queueing
  acceptable, lost writes not. Mechanism selected at integration time
  (embedded flock vs `dolt sql-server`).
- **R-L: per-command tracker latency** must fit a dispatch loop that
  makes tens of calls per session — budget set from measured battery
  numbers (see below), with a stated ceiling per call.
- **R-B: fresh-clone bootstrap ≤ 2 commands** before `agentic ready`
  works, scriptable in a SessionStart/setup hook.
- **R-E: state recoverable from ordinary git alone** (the committed
  JSONL export), verified by a round-trip test in CI.
- **R-S: untrusted-data screening** at the compose boundary for all
  tracker-sourced text.
- **R-V: version-pinned substrate**; upgrades are deliberate,
  migration-tested events.

## Substrate verification (hands-on battery, bd v1.1.0)

PENDING — battery running at authoring time; results land here before
this spec leaves draft. Sections: label-grammar fit (A), graph/ready
semantics (B), single-process latency (D7), export/import fidelity
(E), ops footprint (F), git-integration behavior (G: what a normal
push/clone carries; the fresh-clone recipe feeding R-B).

## Migration sequence

Ordered; each step usable on its own. The queue re-triage happens
FIRST so no further effort lands on subsumed work.

1. **Re-triage the open queue** against this design: every open
   spec/task marked keep / subsumed / fold-into-design. Known
   subsumed: mirror-procedure machinery, drain self-patch cluster,
   ctx-dispatch-adoption's prompt-stanza tasks (composer replaces).
2. **`agentic` v0**: ready/claim/verdict/resume wrapping a pinned bd;
   JSONL export hook; migrate the ~37 live items (8 open, 5 blocked,
   24 drafts). Done/archived specs stay as markdown history.
3. **Composer v0** with verdict schema + grants + ctx map injection +
   screen + budget cap; /build switches to it.
4. **Drain loop v0** over agentic; baton/owner/handoff artifacts
   retired; evals updated to assert loop behavior.
5. **Gates→budgets**: rules rewrite (delete launch contracts, add cap
   config), inbox v0 with veto-window promotion.
6. **Behavior-CI v0**: scheduled audit + auto-filed findings.
7. **Rules shrinkage**: classify every rules line per doctrine 2;
   delete or mechanize; target end-state ≈ untrusted-data + context
   antipatterns + CLI pointers.

## Risks

- **Upstream churn (beads).** Storage layer changed twice in 5 months;
  live migration footguns exist. Mitigation: version pin (R-V), sole
  access through the wrapper, committed JSONL (R-E). Accepted residual:
  a future forced migration costs a bounded integration sprint.
- **Label-grammar strain.** Structured fields in labels is
  string-stuffing with a validator. Mitigation: grammar owned and
  enforced by the wrapper only; if it strains, escalate upstream
  (custom-fields request) before building around it. Battery results
  bound this risk before breakdown.
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
  a mis-set cap can overspend. Mitigation: conservative default caps,
  spend surfaced in the inbox, hard refusal at cap in the composer.

## Open questions

- Wrapper language: Python (matches existing tested modules; slower
  startup) vs Go/Rust (single static binary; rewrite cost). Leaning
  Python v0 absorbing existing code, revisit only if R-L fails.
- Verdict transport: file-based JSON vs stdout capture per runtime —
  adapter-level detail, decided during composer v0.
- Whether ctx folds into `agentic` as a subcommand (one binary) or
  stays sibling with shared conventions.

Next stage: /critique this spec (adversarial pass), then /breakdown
(human-launched).
