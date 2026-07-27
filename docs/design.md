# Design of the agentic toolkit

This document reconstructs the design from the skill bodies, agent
definitions, and enforcement scripts as they stand on 2026-07-27. It asks what
the system assumes about its own components, what it holds invariant, what it
traded away, and where those choices now conflict with each other.

It complements [architecture.md](architecture.md), which maps components and
traces the pipeline, and
[architecture-pivot-2026-07-22.md](architecture-pivot-2026-07-22.md), which
records the largest single decision. Neither states the operating premise the
mechanisms are built on, and neither names the places where two mechanisms now
disagree. That is this document's job.

## The premise

The system treats a language model as a component with four specific
liabilities: it forgets, it is expensive, it is unreliable, and it games its
own success criteria. Almost every mechanism in the repo maps to one of those
four, and reading the design that way explains choices that otherwise look
like overhead.

The fourth liability is the one that makes this toolkit unusual. Most agent
frameworks defend against the first three. This one is built by someone who
watched workers satisfy acceptance criteria without implementing the
requirement, and who then designed against it in four separate places.

## Designing around forgetting

Nothing durable is reconstructed from conversation. bd holds task status,
dependencies, claims, and provenance; `specs/<slug>/` holds the work
definitions; `specs/<slug>/evidence/<name>.md` holds the verifier's full
report; the task file's `## Decisions` section holds reversible calls taken
mid-run. Resume is a `bd ready` query, which is why `/drain` can state that
interrupting it loses nothing.

Two rules make the single-writer property hold. Task-file `Status:` headers
are frozen display, read by no live procedure — the dual-source version
drifted, and the fix was to demote one source to decoration rather than
synchronize two. And task definitions are immutable after registration:
`agentic register-spec` reads the authored headers once to create issues and
edges, then bd owns everything. The verifier enforces this mechanically with
an append-only task-file check that diffs `*/tasks/*.md` path-scoped against
the base and fails on any edit outside a small allowed set — checkbox ticks,
evidence lines, the plan comment block. A worker-written `## Progress` section
is an automatic FAIL.

`/distill` closes the loop by routing a session's learnings to shared
guidance, a `docs/memory/` topic file, or a new skill — with an explicit
"Nowhere — write nothing" row and the gate "would removing this line cause a
future agent to make a mistake?" It is pinned `model: opus`, which inverts
naive cost optimization: the step that decides what the system permanently
believes gets the strongest model available.

## Designing around cost

The tier ladder is the visible half: scout on Haiku at low effort, ordinary
judgment on the session model, `implementation-worker` and `critic` pinned to
Opus in their own frontmatter so a dispatch tier survives whatever the calling
session happens to be running. The pins are structural rather than advisory
for a measured reason — an untyped general-purpose agent inherits the
session's frontier model and ran dearer per call than the Opus-pinned worker.

The less obvious half is that the system memoizes expensive judgment against a
freshness key, in three places with the same shape:

- `/critique` hashes the SPEC.md bytes and records the verdict in
  `specs/<slug>/critique-findings.md`. A byte-identical re-run skips the critic
  dispatch entirely and relays the recorded verdict. An absent or unparseable
  hash always means run it.
- `/idea` checks `docs/` for a topically matching `Verified:` stamp inside a
  90-day window before dispatching any research agent, and refreshes the stamp
  when it does research.
- `/critique` stamps `Breakdown-ready: true` into the spec at READY, and
  `/drain`'s auto-breakdown phase greps for exactly that line. The artifact
  carries its own gate token.

Cost discipline also shows up as skip gates keyed to risk. `/build`'s
pre-commit review stages everything, diffs per-path line counts against the
step-0 base, classifies paths as product or non-product by glob, and skips the
review outright for docs-only, tests-only, or under-25-line product diffs,
recording `review skipped: <reason>` as the evidence. `/work`'s
`preflight_fanout.sh` refuses above 20 agents without `--override`, and the
skill is explicit that the printed token estimate is context for judgment
while the count is the gate.

Dispatch itself is context-economical. `/drain` delivers its worker prompt by
path-pointer — the worker is told to read `reference.md` and follow it
verbatim, never handed the pasted body — which keeps every dispatch call small
and single-sources the contract at once.

Finally, the pipeline is instrumented from inside the prompt. `/build` emits
`<!-- agentprof:stage=load -->`, `=plan`, `=implement`, `=verify`,
`=close-out` verbatim at each step, and `agentprof` reads those markers out of
the transcript to attribute tokens and dollars per stage. The agent narrates
its own state transitions so a downstream profiler can bill them.

## Designing around unreliability

Fresh-context adversarial review is the backbone: `critic` before
implementation, `verifier` after. The mechanism is amnesia, not skepticism — a
context that never took the shortcut cannot rationalize it, and the verifier is
told in as many words not to trust the implementer's claims, including any
"verified ✓" notes in the task file.

Independence is enforced by topology rather than instruction. Agent nesting is
one level, so a drain worker cannot spawn its own reviewer; the review-gate
verdict it can produce is stamped `self-review`, and the orchestrator is
structurally the only place an independent read can happen. `/drain` therefore
owns the verifier/critic barrier and the worker is told, in the dispatch
prompt, not to spawn build's verifier at all.

Around that sit mechanical prechecks that halt before any judgment runs. The
verifier's worktree-integrity precheck compares `HEAD` to the branch ref and
refuses on any dirt, including untracked files, because a verifier dispatched
without being told which worktree to use lands in the shared checkout and
would otherwise grade content the branch does not carry. Its empty-diff
precheck stages everything, restricts the diff to `Touch:` when present, and
returns FAIL on an empty result before running a single acceptance command.
The verifier is explicitly forbidden from repairing a mismatch: a mismatch it
did not cause may be a concurrent-session collision the human needs to see
intact.

Retry policy is matched to failure class rather than applied uniformly. A
worker or verifier FAIL relaunches once, one tier up. A verifier INCOMPLETE
re-dispatches once into the resolved worktree and never escalates tier —
"a higher tier cannot fix a location fault." A second failure of either kind
records the cause and leaves the issue open rather than thrashing. `/build`
stops after two failed fix attempts on the same issue on the stated grounds
that repeated correction in a degraded context is the known failure mode.

Gate placement follows the same economy. Workers and fix rounds run acceptance
commands and directly relevant targeted tests only; the orchestrator runs the
repository's canonical `scripts/check.sh` exactly once, on the reviewed
branch, at the merge barrier — because repeating a multi-minute suite inside
every round is not additional evidence.

## Designing around specification gaming

This is the part that distinguishes the design, and it appears at four
separate stages.

**At authoring.** `/idea` runs an anchor check on every grep- or count-based
criterion the moment it drafts it: run the count against current on-disk
state, confirm the expected result actually differs from today's, and record
the outcome inline. It then rejects any criterion whose target phrase is a
byproduct of the spec's own requirements — the self-referential trap, where a
worker satisfies the check by typing the literal search string without
implementing the behavior.

**At classification.** Every criterion is ranked on a depth ladder: L0 text
presence, L1 artifact structure, L2 behavior, L3 end-to-end. The rule is
deepest-feasible rather than default-to-grep. What makes this honest rather
than aspirational is the escape: a requirement that genuinely bottoms out at
L0/L1 carries a `Depth ceiling:` annotation stating why deeper is infeasible
and naming the behavioral complement. The skill says plainly that prose skills
— most of this toolkit — legitimately bottom out at L0/L1, and that the
annotation "legalizes that ceiling instead of letting a grep pose as
behavioral proof."

**At review.** The critic runs a three-question attack on each criterion:
gameable by literal, anchor still differs from disk, deepest feasible level
reached. A gameable criterion with no depth-ceiling annotation blocks READY
with the same force as an unmapped requirement. And `/critique`'s finding
triage routes gameable criteria to JUDGMENT specifically so they cannot be
auto-fixed — "swapping what a criterion checks changes what the spec
verifies."

**At verification.** The verifier checks for overfitting to the checks: were
test files modified after the failing tests were committed, does the
implementation special-case the exact test inputs, would it survive a
reasonable variation. An implementation that games its acceptance criteria is
a FAIL even when every command passes. Its mandatory per-requirement
criteria-adequacy line asks whether the passing criteria actually *entail* the
requirement, and a behavioral requirement evidenced solely at L0 is INCOMPLETE
rather than PASS.

## The privilege architecture

Authority is separated from throughput. The drain worker — isolated in its own
worktree, running on the deep tier, doing the actual implementation — is
deliberately de-privileged. It never pushes, never calls bd, never writes
`HUMAN.md`, never spawns a subagent, never creates a task or issue for
something it discovered. It returns a capped verdict with fixed sections:
`DONE`/`BLOCKED`/`DEFERRED`, per-criterion evidence, `Decisions:`,
`Discovered:`, and for a blocked stop a typed `Unblock: run:` / `agent:` /
`ask:` line. Every state mutation is the orchestrator's, and the separation is
backed structurally — a worker that wrote `HUMAN.md` would fail drain's
merge-time `Touch` whitelist.

`Touch:` itself carries three jobs from one declaration: it is the concurrency
key (disjointness is what lets issues run in the same window), the scope
boundary the verifier tests for creep, and the repair authority — `/build`
fixes a review finding only if it is a correctness defect *and* the fix stays
inside `Touch`, otherwise surfacing or filing it.

Where containment actually matters, the design drops out of the agent
framework entirely. A dispatch declaring `write-deny-paths` must not use a
native spawn or subagent path; it runs headless through `dispatch-worker.sh`
into `write-deny.sh`, which applies an OS write denial inherited by the agent
and all its child processes — Seatbelt on macOS, bubblewrap on Linux. If the
platform backend is unavailable the wrapper exits nonzero before the worker
starts and drain records BLOCKED. The instruction is unambiguous: never
substitute a prompt-only prohibition. That is the mechanism-over-prose
principle taken to its conclusion, and it costs the native fast path to get
there.

The untrusted-data boundary has a mechanical implementation too:
tracker text bound for a worker prompt is written to a temp file and screened
by `screen-stub.sh`, exit 0 clean and exit 1 refused, with exit 2 explicitly
defined as a usage error never to be treated as clean.

## The artifact protocol

Stages communicate through typed tokens in files rather than through prose
handoffs, which is what lets them run in separate sessions.

| Token | Written by | Read by |
| --- | --- | --- |
| `Breakdown-ready: true` | `/critique` at READY | `/drain` auto-breakdown |
| content hash + verdict in `critique-findings.md` | `/critique` | `/critique` re-run skip |
| `Verified: <date>` in `docs/` | `/idea` research step | `/idea` freshness check |
| `Depends on:`, `Touch:`, `Budget:`, `Rigor:` | `/breakdown` | `register-spec`, then bd |
| `DONE`/`BLOCKED`/`DEFERRED` + typed `Unblock:` | worker | drain orchestrator, gate hook |
| `PASS`/`FAIL`/`INCOMPLETE` | verifier | drain routing |
| `READY`/`READY WITH NITS`/`NOT READY` | critic | drain routing |

Two details show the protocol has been debugged against real failures. A final
message beginning with `DEFERRED`, `BLOCKED`, or `INCOMPLETE` passes the gate
Stop hook even while checks are red — unattended workers stop mid-red by
contract, and blocking them would trap them in a loop. And drain is told to
route on the critic's verdict line only, never to grep its findings for
severity words, because the critic emits 0–100 confidence scores and no
severity labels at all.

The confidence threshold itself is set by stage economics: the critic reports
only findings at 80+ on a diff, but admits 60–79 on a spec, because ambiguity
is cheap to fix before implementation and expensive after.

## Two dials that scale the process

`Rigor:` scales the gates. Absent means production: TDD red-first, the full
verifier spawn, everything. `Rigor: prototype` skips red-first and skips the
verifier, substituting a mechanical acceptance-command run as the reported
signal so drain's verdict routing still works unchanged. Commit hygiene,
runnable criteria, and the untrusted-data rules never scale. The one-way door
is explicit: prototype code never merges into production-rigor work without
flipping the header and treating the existing code as untested input to a
normal task.

Reversibility scales escalation. A mid-task decision with a reversible default
is taken, logged as (decision, default, how to reverse), and work continues.
A decision with no reversible default — or anything on the irreversible,
blast-radius, spend, or authority list — stops. Attended `/build` asks the
human; an unattended worker parks it as `DEFERRED`. Deferred questions can
even carry `Contradicts-premise: true` with a verbatim excerpt, so the batch
interview can substring-match it against the artifact's current text and skip
re-opening a question the artifact has since answered.

## What the design optimizes for that most don't

`/design`'s selection criteria rank requirements fit first, then **verification
story — could an agent test this well?**, then on-distribution, then
simplicity. Fast deterministic checks, low-noise output, and typed APIs score
high, and the skill calls this "the tiebreaker that matters most for agentic
development." Technology is chosen for agent-verifiability rather than
developer experience. The companion principle is to stay on distribution —
prefer what the model already knows deeply, because "an exotic choice means
every future session pays a teaching tax."

The same instinct governs whether to use a model at all. `/design` classifies
each part of an AI-embedding feature on a code-vs-LLM ladder, defaults to the
lowest rung meeting the requirements, and requires any higher rung to name the
failing per-part test that justifies it. `/idea` applies it to itself: a
one-sentence diff gets done, not specced, and a mechanical transform a
deterministic tool can perform "gets a script, not a spec."

Skills are tested as software. An evalset scenario builds a fixture repo, runs
the skill headlessly, and grades the artifacts. Beyond that, **trigger
scenarios grade the routing decision** — the prompt describes the task in a
user's words and never names the skill, and the grader reads activation from
the transcript, accepting either a Claude `Skill` call or a Codex/Antigravity
read of `SKILL.md` so one scenario grades under any runtime. Every evalset
with trigger coverage carries negative cases, because "a positive-only set
cannot catch the failure that costs the most: a description broad enough to
pull the skill into a neighbour's work." The conclusion drawn is precise:
trigger failures are description failures, so fix the frontmatter, not the
body. Coverage is governed by a tier table and enforced model-free by
`lint-eval-coverage.sh`, which fails on any skill missing from the table.

## Where the design strains

**Prose is being used as a programming language, and only the model type-checks
it.** `/build`'s close-out step is roughly a hundred lines of branching
English: a skip gate with a glob list and a numeric threshold, a
fix-iff-in-Touch conditional, a fallback chain when native skill invocation is
unavailable, carve-outs for drain-worker mode and bare-SPEC runs. It is a
program whose interpreter is a language model. Individual branches are rarely
exercised, no test covers most of them, and the failure mode is silent
divergence rather than an error. The skill-size convention caps bodies at 500
lines, which bounds the file but not the branching.

**The doctrine is densely cross-referential and the citations are not
link-checked.** "Cite it, don't restate it" is the governing convention, and
it works — it kept CLAUDE.md at 210 lines and the rules at 737. The cost is
that a worker's actual obligations are spread across a citation graph: a skill
cites a rule, which cites a `docs/memory/` topic, which cites an archived
spec. Nothing verifies those targets still exist or still say what the citing
line claims. The pivot document already flags entries in `docs/memory.md` that
describe retired mechanisms; that decay has no automatic detector, and
`/distill`'s manual prune is named in the skill as "the layer's only decay
mechanism."

**The frozen-surface guard has become the main source of stalls.** Five of the
17 open blockers in `HUMAN.md` — and five of the six most recent, all filed
2026-07-26 — are the same collision: a task whose acceptance requires editing
a test the inventory pins as immutable `retain`. Each implementation passes
its own checks and fails only the frozen-content inventory. The guard is
working as specified; the defect is upstream, since immutability is enforced
at commit time but never consulted at task-authoring time. `/breakdown`
already classifies criteria for privileged-access infeasibility and flags
those tasks MANUAL at authoring time — the same pre-flight applied to the
surface inventory would close this, and a bd memory currently patches it with
a reminder instead.

**Routing complexity grows faster than the skill count.** Eight skills now
share the prose domain, and their descriptions carry explicit mutual-exclusion
clauses — `/prose-review` not for external deliverables, `humanizer` not for
first drafts, `grounding` not a style pass, `/critique` by artifact type
rather than by request wording. Negative trigger evals exist precisely because
these boundaries are non-obvious, and the critique/prose-review split is the
worked example in the eval doctrine. The mitigation is real, but the cost of
each additional skill in a crowded domain is a routing test against every
neighbour, not just its own evalset.

**Distribution lags source, silently and consequentially.** This session
opened with the installed plugin at 0.18.7 against a source repo at 0.18.12.
`docs/memory/verifier-tier-leak.md` records what that costs: a shipped
agent-definition fix appeared not to work because the immutable plugin-cache
snapshot was still serving the old `model: inherit` pin — a correctness and
cost defect from deployment lag alone. A staleness hook warns; nothing
reconciles.

**The queue's steady state is human-gated.** bd shows 18 open, 19 blocked,
zero ready. The `/drain` design is deliberate here — there is no human-watched lane,
and sensitive work raises the scrutiny bar rather than routing to a person, so
the only things that reach `HUMAN.md` are genuinely unresolvable by an agent.
That is the pipeline working. It also means throughput is bounded by one
person's decision rate, and four of those blockers are pure residue from the
2026-07-03 tracker exit being reversed on 2026-07-22 for this repo only,
leaving four sibling repos holding contradictory instructions.

**The system is its own only serious customer.** 131 specs in 24 days, nearly
all about the toolkit. The feedback loop is fast and honest — every mechanism
is exercised by the work of building the next one, and `docs/memory/` reads
like a system that learns from incidents. It is also the classic overfitting
risk, and the cross-repo rollout blockers are the first evidence that what
fits here needs a decision at each destination.

## What would falsify this

The design rests on testable claims, and keeping them testable is worth more
than defending them.

If the anti-gaming machinery never fires — if no criterion is ever rejected as
gameable and no verifier ever returns INCOMPLETE on an L0-only behavioral
requirement — then the ladder is ceremony and the simpler check was enough. If
the tier pins do not show up in `agentprof` attribution, the pinning is
ceremony too. If memoized critique verdicts are ever relayed against a spec
whose meaning changed without its bytes changing, hash-keying was the wrong
freshness key. If fresh-context verification passes work that later breaks,
the amnesia argument is weaker than assumed and review needs to move earlier.

And if the human blocker queue keeps growing faster than it drains, the
bottleneck is not agent capability but adjudication rate — in which case the
highest-leverage work is reducing the number of decisions that reach a person,
not increasing the number of tasks that reach an agent.

The head-to-head eval harness (`specs/skills-vs-ultracode-eval`) was built on
this principle, and the pivot document states the standard plainly: if the
data disagrees with the document, the data wins.
