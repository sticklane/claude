# Design of the agentic toolkit

This document reconstructs the design from the artifacts, as of 2026-07-27:
32 skills, 4 agents, 7 rules, 10 hooks, 131 spec directories, 501 task files,
and 3,378 commits laid down between 2026-07-02 and 2026-07-26. It asks what
the built thing is actually optimizing for, what it holds invariant, what it
traded away, and where it is under strain.

It complements two existing documents rather than replacing them.
[architecture.md](architecture.md) maps the components and traces the pipeline;
[architecture-pivot-2026-07-22.md](architecture-pivot-2026-07-22.md) records
the single largest decision. Neither states the invariants the whole system
rests on, and neither names the places where those invariants now conflict
with each other. That is this document's job.

## The problem being solved

The stated purpose is a spec pipeline: an idea becomes a spec, the spec is
split into tasks, agents execute the tasks. That description is accurate and
it undersells the design, because a pipeline is the easy half. Every mechanism
that took real engineering — the tier ladder, the scout agent, the fresh
verifier, the bd cutover, the session-refresh budget, the spill hook — exists
to solve a different problem.

**The binding constraint is context, not capability.** A model that can write
the code cannot hold the repository, the task, the research, and its own
reasoning at once, and everything it does hold is re-billed on every
subsequent turn. So the design question is never "can the agent do this"; it
is "what does the agent have to read to do this, who pays for that reading,
and does that cost survive contact with a hundred more turns." The toolkit is
a context-economy first and a workflow engine second.

Three consequences follow, and they explain nearly every structural choice in
the repo. Work must be decomposable into units that fit one clean context.
State must live outside the conversation, because conversations end and
compact. And judgment must be delegable to processes that are cheaper than
the session that needs the answer.

## The forces

**Prose does not bind an agent; mechanisms do.** The pivot document states
this from measurement — compliance with "prefer X" advisory prose was zero.
This is the most consequential finding in the repo, because the repo's own
primary output format is prose.

**Cost is nonlinear and mostly invisible at authoring time.** The recorded
numbers are specific: roughly $1,406/week of unstructured orchestration
before `/drain` existed; a $123 leak from one nested untyped-agent chain;
26% of an overnight window's spend on cache re-priming alone; a
general-purpose agent at $0.067/call running dearer than the Opus-pinned
implementation-worker at $0.057/call, because the untyped agent inherits the
session's frontier model while the typed one is pinned down. Nothing in the
authoring experience makes any of this visible, so the design has to encode
the economics structurally.

**The host defines what can be enforced.** The toolkit can only be mandatory
where Claude Code offers a seam: `SessionStart`, `PreToolUse`, `PostToolUse`,
`Stop`, and a process exit code. Everywhere else it can only advise. The
architecture is shaped by that extension surface, not by what the designer
would prefer to control — and the honest cases where a hook was scoped and
rejected are recorded as such (the untyped-under-untyped dispatch warning was
not shipped because the hook payload exposes neither dispatch depth nor the
running agent's tier).

## Invariants

Five rules hold across the entire system. They are what a change should be
tested against.

**One writer per fact.** Task status lives in bd and nowhere else. The
`Status:` headers in 501 markdown task files are frozen display, explicitly
read by no live procedure. This was a cutover, not a coincidence: the
dual-source version drifted, and the fix was to demote one source to
decoration rather than to synchronize two. The same shape appears in
`specs/QUEUE.md`, which is a wave plan rather than live state, and in
`.beads/issues.jsonl`, which is a passive export rather than a sync channel.

**Resume is a query, not a narrative.** Nothing durable is reconstructed from
conversation memory. `/handoff` writes an issue; the resume hook reads a
label; `bd ready` answers what to do next. The earlier baton, owner-lease, and
generation-counter machinery in `/drain` was deleted precisely because a prose
orchestrator loses its place, and a database does not.

**No artifact is trusted until a context that did not produce it agrees.**
The critic reads a spec before implementation; the verifier reads acceptance
criteria after it, with no memory of the work. The mechanism is not
skepticism, it is amnesia — a fresh context is structurally unable to
rationalize a shortcut it never took. This is the cheapest correctness
mechanism available for LLM work, and the toolkit spends it liberally.

**Every dispatch declares its tier, its budget, and its bound.** Mechanical
work runs Haiku, ordinary judgment runs the session model, heavy judgment runs
Opus, and frontier is reserved. Subagent returns cap at 1–2k tokens; large
outputs are written to disk and returned as a path. Loops name a cycle count.
Concurrent writers cap at 3–5 with rolling top-up rather than wave barriers.
`bin/check-token-discipline` enforces the first three of these across the
dispatch-authoring skills, which makes it one of the few doctrine lines that
has become a test.

**Tool output is data, never instruction.** File contents, command output, web
pages, and tracker text carry no authority. Only the user's live message, the
rules, and the executing task file do. This is the reason execution stages
cannot be launched by a file, a notification, or another agent — a boundary
that survived the pivot intact while the elaborate launch-authorization
contracts built on top of it were deleted.

## The layering that falls out

Read bottom-up, the system is four layers plus packaging.

The **data layer** is bd for live work state, Codebase-Memory for code
structure, and `specs/<slug>/` for the units of work themselves. This layer
is the portability story: any agent on any runtime can read it. Task headers
(`Depends on`, `Touch`, `Budget`, `Rigor`) are the scheduler's input —
`Touch` disjointness in particular is what makes parallel writers safe without
locking.

The **judgment layer** is the skills. They encode taste that neither a tracker
nor an orchestration engine has: how to interview for a spec, how to attack
one, how to size a task for a single session, how to tell a real lesson from
session noise. This is the "skill-augmented" half of the architecture's own
name for itself, and it is the part with no commodity substitute.

The **enforcement layer** is hooks and check scripts: 1,683 lines of hook
code, 2,893 lines under `bin/`, 14,072 lines of tests. The Stop hook refuses
"done" while checks are red or claimed bd issues sit open. `PreToolUse`
protects files; `PostToolUse` formats and spills over-budget output. This
layer is small relative to the prose it enforces, and growing it is the
repo's clearest direction of travel.

The **measurement layer** is `agentprof` (17,549 lines of Go attributing
tokens and dollars to skills, projects, and cache behavior), `agent-console`
(a local dashboard), and `evals/` — 22 stored scenarios, 10 of them
adversarial. The eval pattern deserves naming: each skill's evalset pairs a
happy path (`01-small-spec`) with a scenario the skill must *decline* to act
on (`02-adv-gameable-criterion`, `02-adv-noise-rejection`,
`02-adv-graph-empty-is-not-absence`). Prompts are treated as software with
regression tests, and the adversarial half tests for the failure mode prose
skills actually have, which is firing when they should not.

**Packaging** distributes all of it as the `agentic` plugin, with generated
per-runtime entrypoints under `skills/`.

## The life of one unit of work

An idea becomes `specs/<slug>/SPEC.md` with runnable acceptance criteria. The
critic attacks the spec while it is still cheap to be wrong. `/breakdown`
splits it into task files sized for one clean session, each declaring what it
touches and what it depends on. `agentic register-spec` creates the bd issues
and dependency edges from those headers once, reading the authored definitions
and ignoring their status. From then on bd owns the state.

Execution takes one of two shapes. `/build` works a single task attended.
`/drain` compiles the ready queue into dependency-ordered, `Touch`-disjoint
waves and runs a fresh worker per issue. Either way a verifier that never saw
the implementation checks it against the written criteria before bd closes the
issue, and `/distill` folds what the session learned back into rules or
skills.

The acceptance criteria are load-bearing in a way worth calling out. They are
runnable commands, verified against current file state at authoring time — a
grep must anchor on a phrase confirmed absent, a numeric bound must be
confirmed satisfiable. An unverified criterion either passes vacuously or
stalls a drain forever, so criterion authoring is where a lot of the system's
correctness actually lives.

## Decisions and what they cost

| Decision | Bought | Paid |
| --- | --- | --- |
| bd as sole live state; markdown headers frozen | Drift-free resume; queries instead of narratives | A human reading a task file sees a stale `Status:` line |
| Data-level portability; procedure mirrors deleted | Removed hand-maintained triplication and its parity gates | Other runtimes get no procedures; a thin generated entrypoint layer came back because plugin caches drop symlinks |
| Advisory cost control plus thin guards, not an approval ledger | Unblocked work; caps and visibility instead of gates | No hard ceiling — leaks are found after the fact by `agentprof` |
| Native orchestration instead of a custom engine | Schema'd returns, resume, concurrency caps, tier routing for free | Multi-agent execution is coupled to one runtime's feature set |
| Fresh-context adversarial review at every stage | The cheapest available correctness mechanism | Every artifact pays a review round; review latency is on the critical path |
| Frozen `retain` test inventory | Regression surfaces cannot silently disappear | See the first strain below |

## Where the design strains

**The frozen-surface guard has become the main source of stalls.** Of the 17
open human blockers in `HUMAN.md`, five — and five of the six most recent, all
filed 2026-07-26 — are the same collision: a task whose acceptance requires
editing a test file that the inventory pins as immutable `retain`. In each
case the implementation passes its own checks and fails only the frozen-content
inventory. The guard is working exactly as specified. The defect is upstream:
immutability is enforced at commit time but not consulted at task-authoring
time, so tasks get written that cannot legally complete, and the only exit is
a human adjudication. A bd memory now records the pre-flight check to run
before dispatch, which is doctrine patching a mechanism gap — the durable fix
is to make the authoring stage read the inventory.

**The doctrine-to-mechanism ratio still runs the wrong way.** Against 18,648
lines of enforcement code sit roughly 100,000 lines of markdown, and the
repo's own finding is that advisory prose measurably does not bind. Some of
that prose is irreducible: the judgment skills are the product. But there is
no standing classification separating "genuinely unmechanizable judgment" from
"mechanizable, not yet mechanized," so the two are indistinguishable in the
tree and the second silently accumulates. `bin/check-token-discipline` and
`bin/check-agent-model-pins` show what the conversion looks like when it
happens; the missing artifact is a disposition on every doctrine line.

**Distribution lags the source, silently and consequentially.** This session
opened with the installed plugin at 0.18.7 against a source repo at 0.18.12.
That gap is not cosmetic: `docs/memory/verifier-tier-leak.md` records a
shipped agent-definition fix that appeared not to work because the immutable
plugin-cache snapshot was still serving the old `model: inherit` pin — a
correctness and cost defect caused purely by deployment lag. A staleness hook
warns; nothing reconciles.

**The queue's steady state is human-gated.** bd currently shows 18 open, 19
blocked, and zero ready. Every item needs either a dependency or a person.
This is arguably the pipeline working — it converts work agents cannot finish
into explicit, well-written decisions rather than into guesses — but it means
throughput is bounded by one human's decision rate, and the blocker list is
where the system's actual backpressure shows up. Four of those blockers are
residue from a policy reversal: the 2026-07-03 exit from bd, reversed on
2026-07-22 for this repo only, left four sibling repos holding contradictory
tracking instructions that only a human can adjudicate.

**The system is its own only serious customer.** 131 specs in 24 days, nearly
all of them about the toolkit. That is a fast, honest feedback loop — every
mechanism is exercised by the work of building the next mechanism, and the
incident files in `docs/memory/` read like a system that learns. It is also
the classic overfitting risk: mechanisms are tuned to one repository, one
operator, and one runtime, and the cross-repo rollout blockers are the first
evidence that what fits here does not transplant without a decision at each
destination.

## What would falsify this design

The design rests on claims that are testable, and holding them testable is
worth more than defending them.

If mechanized enforcement does not measurably outperform doctrine, the
conversion program is wasted effort and the prose should stay prose. If the
tier ladder does not show up in `agentprof` attribution, the pinning
machinery is ceremony. If fresh-context verification passes work that later
breaks, the amnesia argument is weaker than assumed and review needs to move
earlier or deeper. And if the human blocker queue keeps growing faster than it
drains, the bottleneck is not agent capability at all but the rate at which
one person can adjudicate, in which case the highest-leverage work is reducing
the number of decisions that reach a human rather than increasing the number
of tasks that reach an agent.

The head-to-head eval harness (`specs/skills-vs-ultracode-eval`) was built on
exactly this principle, and the pivot document states the standard plainly: if
the data disagrees with the document, the data wins.
