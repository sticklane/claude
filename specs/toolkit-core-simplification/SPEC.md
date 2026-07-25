# Evidence-safe improvements to the agentic toolkit

Rigor: production
Breakdown-ready: true

## Problem

The toolkit has confirmed live contradictions and incomplete mechanics:
markdown task headers are documented as frozen while live procedures still
write or trust them; live files cite deleted executables and completed
one-off workflows; four advertised CLI commands exit as stubs; the canonical
test runner discovers tests by glob, so deleting a test can silently delete an
invariant; and cost, issue, verdict, review, gate, retry, and reopen events
cannot be joined into one run. Broad deletion is unsafe because current skill
count does not measure default-context cost or capability value, and the
ratified architecture makes bd—not `agentic`—the public tracker authority.

## Solution

Improve the existing architecture in four ordered phases. First, freeze and
review a complete inventory of live capabilities and the behavioral tests
that protect them. Second, repair only confirmed contradictions, dead
references, one-off workflows, and unconditional CLI stubs without removing
working optional capabilities. Third, add a stable cross-runtime run-event
schema and reproducible scorecard. Fourth, define and test one native-
orchestration conformance contract for Claude, Codex, and Antigravity. The
contract standardizes observable state and safety boundaries; each runtime
continues to use its own agent manager. The scorecard may recommend later
retirement or packaging, but this spec moves or deletes no functioning skill
solely because its invocation rate is low.

## Architecture decisions

- **D1 — bd remains public and canonical.** Humans, skills, and maintenance
  tooling may call bd directly. `agentic` wraps only operations for which it
  adds tested locking, composition, verdict validation, or telemetry. No raw
  bd call is removed without an operation-by-operation parity test.
- **D2 — Inventory before deletion.** A reviewed baseline lists every current
  skill, agent, rule, hook, workflow, CLI command, runtime profile, and
  canonical test. Each row records dependents, behavioral evidence, and one
  disposition: `retain`, `repair`, `hide-stub`, `retire-dead`, or
  `measure-before-decision`. The baseline hash is frozen before cleanup.
- **D3 — Confirmed-dead is narrower than low-use.** A missing executable,
  completed-spec-specific workflow, contradictory authority statement, or
  unconditional stub is repairable now. A working on-demand skill is retained
  until measured evidence and a separate reviewed decision say otherwise.
- **D4 — Native engines, one conformance contract.** The ratified 2026-07-22
  pivot remains in force: Claude Workflow, Codex collaboration subagents, and
  Antigravity native subagents are the execution engines. A shared protocol
  schema and trace validator specify claim state, isolation, denied-path
  handling, verdicts, independent review, final-gate placement, close, and
  cleanup. They validate native behavior; they do not dispatch workers or
  centralize the three runtimes.
- **D5 — Observational metrics stay observational.** The scorecard reports
  adoption, cost, delivery, prevention, and unknown outcomes. It does not
  claim causal productivity improvement.
- **D6 — Tracker registration is create-only.** New task files may seed new
  beads once, but never advance or reopen existing bead state. Ongoing
  markdown-to-bd synchronization is retired.

## Requirements

1. **R1 — Frozen capability inventory.** `BASELINE.json` contains every live
   surface and canonical test present at the baseline commit, its SHA-256
   content hash, dependents, disposition, rationale, replacement if any, and
   behavioral test pointers. A gate rejects unclassified rows, duplicate
   identities, missing evidence for `retain`/`repair`, or deletion/move of a
   non-`retire-dead` row. `BASELINE.json` is immutable after its reviewed
   commit. A surface added later must be classified in a uniquely named
   additive fragment under this spec's `surface-inventory/` in the same
   change; the gate evaluates the frozen baseline plus all fragments and
   rejects an unclassified new surface.
2. **R2 — Explicit retained-test runner.** `scripts/check.sh` executes a
   versioned test inventory rather than relying only on `tests/test_*.sh`.
   The runner fails when an inventoried test is missing and when an executable
   test exists but is neither inventoried nor explicitly quarantined with a
   reason.
3. **R3 — Authority contradictions removed.** Live instructions consistently
   say bd owns task state and dependencies; markdown `Status:` headers are
   frozen display only. The public replacement for `shadow-sync` is
   `agentic register-spec <spec-dir>`, a create-only registrar:
   - it reads task identity, title/goal, dependency declarations, Touch,
     Budget, and Rigor, but ignores `Status:`;
   - the definition hash is SHA-256 of sorted-key, whitespace-free JSON
     containing schema version, repo-relative path, title, goal, sorted Touch,
     Budget, Rigor, and sorted prerequisite external references;
   - under the existing repo write lock, phase one creates every absent issue
     with external reference `spec-task:<repo-relative-path>`, definition hash,
     and registrar-owned `registration_state=pending`; phase two creates each
     absent typed `blocks` edge in the direction
     `task issue → prerequisite issue`, then marks each registrar-owned state
     `complete`;
   - on a same-hash rerun, it verifies all registrar-owned edges, creates any
     missing edge left by an interrupted phase two, and marks registration
     complete before returning success. A different hash or an existing edge
     with conflicting type/endpoints is a reported conflict and exit 1. It
     never deletes or changes an existing edge, and it never updates status,
     priority, assignee, comments, or metadata outside `registration_state`;
   - `breakdown` invokes it after writing task files.
   `shadow-sync` becomes a hidden compatibility alias that performs no
   mutation, emits the retirement diagnostic in R4, and exits 2. Direct bd
   usage remains supported.
4. **R4 — Dead and stub surfaces resolved.** References to deleted
   `drain_frontier.py`, retired specs, and completed one-off workflows are
   removed from live discovery or explicitly marked historical. CLI
   disposition is fixed here rather than delegated to implementers:

   | Command | Shipped disposition | Exact replacement | Compatibility behavior | Removal |
   | --- | --- | --- | --- | --- |
   | `compose` | hidden retired stub | runtime-native `/work`, `/build`, or `/drain` | exit 2: `agentic compose: retired by the native-orchestration pivot; use /work, /build, or /drain` | delete alias in `agentic` 2.0 |
   | `ctx` | hidden retired wrapper stub; standalone `ctx` remains | `ctx <args...>` | exit 2: `agentic ctx: wrapper not shipped; use ctx directly` | delete alias in `agentic` 2.0 |
   | `inbox` | hidden retired stub | `bd ready` and `bd human list` | exit 2: `agentic inbox: retired; use bd ready and bd human list` | delete alias in `agentic` 2.0 |
   | `demote` | hidden retired stub | `bd update <id> --status deferred` | exit 2: `agentic demote: retired; use bd update <id> --status deferred` | delete alias in `agentic` 2.0 |
   | `shadow-sync` | hidden non-mutating compatibility alias | `agentic register-spec <spec-dir>` for first registration; bd thereafter | exit 2: `agentic shadow-sync: retired; task state lives in bd; use register-spec only for new tasks` | delete alias in `agentic` 2.0 |

   Hidden aliases are accepted only when their exact name is invoked; they are
   absent from top-level help, completion metadata, README command lists, and
   live skill recommendations.
5. **R5 — Stable run-event schema.** Every orchestrated run has one
   UUIDv7 `run_id`, created at successful claim. Reopen creates a new run with
   `prior_run_id`; retries keep `run_id` and increment `attempt`. The
   orchestrator writes the ID to a bd comment, exports `AGENTIC_RUN_ID` where
   the runtime supports environment propagation, and includes it in compact
   prompts and every verdict/review/gate record. A `session-link` event maps
   runtime session IDs to the run so existing agentprof samples can join
   without inventing runtime support.

   Events are append-only JSON under
   `<git-common-dir>/agentic/run-events/YYYY-MM.jsonl`, shared by linked
   worktrees and never committed. Each record contains `schema_version`,
   `event_id`, `run_id`, `prior_run_id`, `timestamp_utc`, `producer`,
   `runtime`, `repo_id`, `issue_id`, `attempt`, `stage`, `parent_event_id`,
   `session_id`, `base_commit`, `result_commit`, `artifact_paths`,
   `finding_fingerprint`, `disposition`, and `reason`; unavailable values are
   the JSON string `"unknown"`, not omitted. The writer takes a per-month file
   lock, encodes one record of at most 64 KiB, appends it with one
   `O_APPEND` write, and fsyncs before releasing the lock. Readers reject a
   malformed non-final record and quarantine/ignore only an incomplete final
   record. Event-write failure warns and marks that run unknown but does not
   alter tracker state. Raw events are retained for 90 days; the scorecard
   prunes older files only after writing a monthly aggregate.
6. **R6 — Reproducible scorecard.** A scorecard accepts a fixed UTC
   `[start,end)` window only when every declared raw source covers the whole
   window and `start` is within the 90-day run-event retention boundary.
   Otherwise it exits 1 and lists the missing source/range; it never blends a
   partial raw window with aggregates. Full-calendar monthly aggregates are
   historical reports, not inputs for new arbitrary-window calculations. For
   an accepted window, the scorecard reports:
   - adoption = eligible sessions containing at least one correctly triggered
     invocation / eligible sessions, with both counts. A session is eligible
     for a skill only when it contains an explicit invocation or at least one
     user turn that `agentprof skillcheck` first identifies by the skill's
     deterministic trigger-phrase matcher and then judges applicable against
     the shipped skill description. Self-chains do not create a new eligible
     session. “Correctly triggered” is skillcheck's existing judged class.
     Skillcheck persists exactly one frozen judgment per
     `(formula_version, session_id, skill)` under
     `<git-common-dir>/agentic/skill-judgments/YYYY-MM.jsonl`, containing
     matcher version, skill-content hash, judge model, judge-prompt version,
     eligibility verdict, trigger verdict, and evidence record IDs. Explicit
     invocations persist `eligibility=explicit`; reruns consume the frozen
     record and never silently re-judge it;
   - verified outcome rate = closed runs with final gate PASS and reviewer
     acceptance / runs reaching review;
   - prevention = unique reviewer or gate findings followed by an artifact
     change before merge, deduplicated by run/finding fingerprint. The
     fingerprint is SHA-256 over canonical
     `(producer, rule_id, repo-relative path, normalized message template)`;
     normalization strips line/column numbers, addresses, and repeated
     whitespace. A finding counts only when the accepted
     `base_commit..result_commit` changes that path and a later disposition
     event says `fixed`; waived, duplicate, out-of-scope, or unlinked changes
     do not count;
   - delivery = median and p90 create-to-close duration, plus
     DONE/BLOCKED/DEFERRED/reopen counts;
   - discovery ratio = discovered-from issues / closed parent runs;
   - marginal cost = attributed API-equivalent cost / verified closed runs;
   - event-unknown rate = schema-valid events with one or more event fields
     required for their stage equal to `"unknown"` / all schema-valid events;
   - run-unknown rate = instrumented runs missing one or more fields in the
     verified-run join below / all instrumented runs.
   The required join for a verified run is `run_id + issue_id + claim +
   session-link + worker verdict + reviewer acceptance + final-gate PASS +
   close + result_commit`; cost additionally requires an agentprof sample for
   a linked `session_id`. Missing elements stay in the denominator and raise
   the per-metric and overall unknown counts. Delivery uses bd
   `created_at/closed_at` for instrumented issues; status-transition events
   supply BLOCKED/DEFERRED/reopen counts. Discovery requires a bd
   `discovered-from` edge. Monthly aggregates retain the formula version,
   UTC window, input-file hashes, numerators, denominators, and unknown counts
   indefinitely as reports only; their input hashes prove the report that was
   produced but do not imply deleted raw inputs remain available. Raw cost,
   judgments, and run events follow their declared existing/90-day retention
   policies.
7. **R7 — Native-orchestration conformance scenario.** A hermetic fixture
   drives each shipped native profile—Claude, Codex, and Antigravity—through
   the same protocol callbacks and validates its normalized trace. The happy
   path is ready, atomic claim, compact screened prompt, runtime-appropriate
   isolation, worker verdict, parallel independent verifier/critic barrier,
   exactly one passing final gate, merge, close, and worktree/claim cleanup.
   Negative traces cover lock contention, malformed or missing verdict,
   denied write, reviewer rejection, final-gate failure, and interrupted
   cleanup. The fixture supplies fake runtime callbacks; no production module
   launches or schedules an agent.
8. **R8 — Façade conformance without centralization.** `/work`, `/build`, and
   `/drain` retain their different user intents and native orchestration.
   Each emits the R7 protocol events at its existing boundaries and passes the
   trace validator for every supported runtime. Contract helpers may validate
   schemas, acquire tracker locks, and append events; they may not select
   work, create workers, schedule retries, merge branches, or choose models.
   No nested verifier or duplicate canonical gate returns. Codex continues to
   use the Codex ultracode-equivalent collaboration shape; Antigravity
   continues to use native subagents; tier selection remains stage-based.
9. **R9 — Context budget and evidence report.** Default-loaded AGENTS/rules
   have an enforced line and estimated-token budget. Skill bodies remain
   on-demand. A dated report records before/after live contradictions, dead
   references, shipped stubs, canonical test count, default-context size,
   gate duration, scorecard unknown rate, and default skill count. This spec
   sets no skill-count reduction target.

## Migration order

1. Commit and critic-review `BASELINE.json`, its schema, and the explicit test
   inventory. No deletion or move is allowed before this gate lands.
2. Repair R3 and R4 rows classified `repair`, `hide-stub`, or `retire-dead`.
3. Add R5 event producers and golden cross-process fixtures, then R6 formulas.
4. Land the R7 protocol schema, trace validator, and fake-runtime fixtures;
   it must contain no worker-dispatch API.
5. Instrument `/work`, then `/build`, then `/drain` and validate each runtime
   profile against R7. Native orchestration remains in place throughout.
6. Emit the R9 report. Any optional-pack or retirement proposal becomes a new
   spec using the measured report; it is not self-authorized here.

## Out of scope

- Replacing bd, hiding direct human bd usage, or changing bd storage/sync.
- Deleting or moving functioning optional skills.
- Deleting archived specs, evidence, or historical cost profiles.
- Rewriting ctx internals.
- Claiming causal productivity gains.
- Changing external runtime APIs that cannot carry the complete event schema;
  such fields remain `unknown`.
- Building a composer, common work loop, scheduler, retry controller, or
  cross-runtime execution engine.

## Acceptance criteria

- [ ] `python3 scripts/inventory-core-surface.py --check
  specs/toolkit-core-simplification/BASELINE.json` passes on the real tree and
  fails fixtures for an unclassified surface, missing retained test, altered
  frozen hash, deletion of a non-retired row, and a duplicate/conflicting
  additive fragment. Covers R1 at L2.
- [ ] `bash tests/test_check_inventory.sh` proves `scripts/check.sh` rejects a
  missing inventoried test and an unclassified executable test, while honoring
  an explicitly reasoned quarantine. Covers R2 at L2.
- [ ] `bash tests/test_live_surface_retirement.sh` passes behavioral fixtures
  proving create-only `register-spec` idempotence/conflict behavior, zero
  `Status:` influence, recovery after interruption between issue and edge
  phases, exact `task → prerequisite` edges, hidden stub help, each exact
  exit-2 compatibility diagnostic, and absence of live
  deleted-executable/workflow references. Covers R3–R4 at L2.
- [ ] `python3 -m pytest tests/test_agentic_events.py
  tests/test_agentic_scorecard.py -q` passes golden numeric fixtures for every
  R6 formula, retry/reopen attribution, deduplication, fixed UTC boundaries,
  frozen eligibility judgments, separate event/run unknown denominators,
  explicit unknowns, and rejection of a window outside raw-source coverage.
  Covers R5–R6 at L2.
- [ ] `python3 -m pytest tests/test_native_orchestration_contract.py -q`
  passes the full R7 happy path and every named negative trace for
  `claude-code`, `codex`, and `antigravity` in isolated temporary repositories,
  and fails a fixture whose contract helper attempts dispatch or scheduling.
  Covers R7 at L2.
  Depth ceiling: fake callbacks deliberately do not launch proprietary native
  agent managers — behavioral complement is a manual-pending three-runtime
  `evals/run.sh drain` journey recorded in `REPORT.json`.
- [ ] `bash tests/test_agentic_facade_conformance.sh work build drain` proves
  each façade/runtime pair emits a schema-valid trace with equivalent tracker
  state, review disposition, one final gate, and complete cleanup while
  retaining the profile's native primitive. Covers R8 at L2.
  Depth ceiling: deterministic façade fixtures cannot exercise every native
  agent manager hermetically — behavioral complement is the same
  manual-pending three-runtime journey.
- [ ] `bash tests/test_context_budget.sh` passes real-tree and over-budget
  fixtures; `python3 scripts/report-toolkit-outcomes.py --check
  specs/toolkit-core-simplification/REPORT.json` validates the dated R9
  measurements without requiring a skill-count reduction. Covers R9 at L2.
- [ ] `bash scripts/check.sh` passes from a clean checkout with every
  inventoried retained test executed exactly once. Covers R1–R9 at L3.

## Open questions

None.

## Parallelization

Task 01 lands first because every later change relies on its frozen surface and
test inventory. Task 02 follows because it fixes the task-registration and CLI
authority boundary used by later work. After Task 02, Tasks 03, 04, and 05 are
safe in parallel: they respectively touch live skill authority, dead
documentation/workflows, and the event substrate. Once Task 05 lands, Tasks 06
and 07 are safe in parallel because scorecard aggregation and protocol
validation share only the already-fixed event schema. Task 08 waits for Tasks
03–05 and 07 because it instruments the native façades against those settled
contracts. Task 09 is the final measured report and context gate, after all
behavioral changes and the scorecard have landed.
