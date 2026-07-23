# Architecture

This repo is the agentic development toolkit: the skills, agents, rules,
and hooks that a Claude Code session loads to plan, split, and execute
software work. This document maps the components and traces how work
moves through them. It describes the state after the 2026-07-22 pivot to
skill-augmented native orchestration; the reasoning behind that pivot
lives in
[architecture-pivot-2026-07-22.md](architecture-pivot-2026-07-22.md) and
is cited here rather than restated.

The organizing idea is that portability is data-level, not
procedure-level. Any agent — on any runtime — can read the same durable
data and pick up the work. The procedures that act on that data are
Claude Code's; other runtimes bring their own.

## The data layer

Three stores hold everything a session needs to know what to do and
where it left off. They are the substrate the rest of the toolkit reads
and writes.

- **The bd queue** (`.beads/`) is the canonical live state: task status,
  dependencies, claims, and provenance. It answers "what is ready" and
  "where was I" as a query, so resume is a lookup rather than a
  reconstructed narrative. The committed `.beads/issues.jsonl` is the
  portable form any agent can read.
- **The ctx index** (`.context/`) is a code-structure index — symbol
  trees, cross-file references, an import graph, and refactor-surviving
  notes anchored to symbols. Agents query it through the `context-tree`
  CLI (`ctx`) instead of reading whole files to answer where a symbol
  lives or what calls it.
- **The task files** under `specs/<slug>/` carry each unit of work: a
  `SPEC.md` with runnable acceptance criteria and `tasks/*.md` sized for
  one clean session each. Their headers (`Depends on`, `Touch`, `Budget`)
  are the schedule; bd holds their live status.

## Components

The active pieces all live under `.claude/`, the source of truth.

- **Skills** (`.claude/skills/`) are the judgment layer and the pipeline
  stages. Judgment skills — idea, critique, breakdown, distill,
  prose-review — encode taste and adversarial checking. Execution skills —
  work, build, drain — run tasks off the queue.
- **Agents** (`.claude/agents/`) are the reusable subagent roles: scout
  for cheap lookups, critic and verifier for independent adversarial
  review, and implementation-worker for dispatched task execution. Each
  pins its own model tier.
- **Rules** (`.claude/rules/`) are the always-on doctrine a session
  loads every turn — token discipline, untrusted-data handling,
  concurrent-session hygiene, and the like.
- **Hooks** (`hooks/`, wired in `.claude/settings.json`) are the
  mechanical enforcement points. The gate skill's Stop hook blocks
  "done" until the repo's checks pass; the bd-compliance hook refuses to
  end a session while it holds open claimed issues. Hooks are the one
  place the harness lets the toolkit enforce rather than advise.
- **Plugin packaging** (`.claude-plugin/`) distributes the toolkit as
  the `agentic` plugin so other repos install the skills and agents
  without copying files.

Supporting tools sit alongside: `agentprof` attributes token and dollar
cost after a run, and `agent-console` renders a local dashboard of open
work and spend. Neither is on the critical path of executing a task.

## The pipeline

Work flows from a raw idea to merged code through a fixed sequence, each
stage handing a checked artifact to the next.

1. **idea** turns a pitch into `specs/<slug>/SPEC.md` with runnable
   acceptance criteria.
2. **critique** runs the critic agent over the spec before any code is
   written — a cheap adversarial pass that catches a wrong plan for a
   fraction of a wrong implementation's cost.
3. **breakdown** splits the spec into independent task files sized for
   one session, with a parallelization map derived from disjoint `Touch`
   sets.
4. **build**, **drain**, or **work** executes the tasks. build works one
   task attended with a human at the keyboard; drain works the ready
   queue unattended, dispatching a fresh worker per issue in dependency
   order; work is the attended daily default off the bd queue.
5. **distill** captures what the session learned back into rules and
   skills so the next session does not repay for it.

Each execution stage verifies its output with an independent verifier
agent before closing the issue in bd, so a task is not "done" until a
second agent confirms its acceptance commands pass.

## The execution engine

Native ultracode workflows are the engine for multi-agent work. A skill
authors a workflow script that dispatches subagents with cheap model
tiers on mechanical stages and the session model on judgment stages;
intermediate results stay in script variables, and every subagent starts
with a blank context. The platform supplies the schema'd returns,
concurrency caps, resume, and the live progress view, so the toolkit
adds judgment and provenance rather than re-implementing orchestration.

## Runtime portability

Claude Code is the primary runtime. Other runtimes read the same data
layer — the bd queue, the ctx index, and the task files — and work tasks
with their own abilities; they no longer receive ported copies of the
procedures. The `antigravity/` and `codex/` directories are each now a
single README pointing a reader of that runtime at the data layer, not a
maintained copy of the pipeline. The full reasoning for dropping
procedure-level portability is in
[architecture-pivot-2026-07-22.md](architecture-pivot-2026-07-22.md).

## Cost control

Cost enforcement is advisory plus a thin guard, not a metered ledger.
Four controls carry it: the native runtime's own concurrency caps,
cheap-model routing written into every authored workflow script,
agentprof attribution after the fact, and a pre-flight estimate
(`.claude/skills/work/preflight_fanout.sh`) that flags a large fan-out
before it launches. The rationale for choosing proportionate controls
over a full enforcement ledger is in the pivot document.
