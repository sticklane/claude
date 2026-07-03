# Agent work-tracking dashboards — what the field does

Research behind `/workboard` (and the session-scoped `/fleet`). This file
holds the findings and citations; the skills state only the rules. Collected
2026-07 from Google Antigravity, Amazon Kiro, and published guidance from
Anthropic, OpenAI, and DeepMind.

## Google Antigravity — the Agent Manager

Antigravity's Agent Manager is a mission-control surface: workspaces (one
agent per repo to avoid cross-contamination), an **Inbox** that is "the
asynchronous communication ledger for all active agents across all active
workspaces," and a conversation pane. Each thread shows at-a-glance status —
**Idle / Running / Blocked**, where Blocked means "needs your input or
approval" — and the Inbox doubles as the cross-repo review queue.
([Agent Manager docs](https://antigravity.google/docs/agent-manager),
[codelab](https://codelabs.developers.google.com/getting-started-google-antigravity))

Agents communicate through **artifacts**, not transcripts: a Task List
(checklist, states `todo | in-progress | completed`), an Implementation Plan
(the main review checkpoint), and a post-completion Walkthrough with
evidence (screenshots, browser recordings). Users comment on artifacts
inline; agents incorporate comments without halting.
([developers blog](https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/),
[walkthrough docs](https://antigravity.google/docs/walkthrough))

Everything is plain files under `~/.gemini/antigravity*/brain/<conversation-id>/`:
`task.md`, `implementation_plan.md`, `walkthrough.md`, each with a
`*.metadata.json` (`artifactType`, `summary`, `updatedAt`, `version`) and
versioned backups. Task phases: `PLANNING | EXECUTION | VERIFICATION`.
Autonomy is policy-per-category (artifact review / terminal execution /
browser), not one dial.
([antigravity-cli](https://github.com/michaelw9999/antigravity-cli),
[agent modes docs](https://antigravity.google/docs/agent-modes-settings))

**Lessons taken**: few, decision-oriented states with *blocked-on-human* as
the load-bearing one; the cross-repo inbox IS the dashboard; artifacts with
sidecar metadata make state greppable without parsing prose.

## Amazon Kiro — spec-driven state on disk

Each feature is `.kiro/specs/<name>/` with exactly `requirements.md`
(EARS-notation acceptance criteria), `design.md`, and `tasks.md` — three
phases, each gated by human approval before the next is generated.
`tasks.md` is the execution store: checkbox tasks where `[ ]` = not
started, `[-]` = in progress, `[x]` = done, with requirement back-references
(`_Requirements: 6.1, 6.3_`) making coverage computable. "Sync Files"
re-derives checkbox state from the actual code, guarding against drift.
Specs are committed and greppable — ~7,750 public `tasks.md` files exist on
GitHub. ([specs docs](https://kiro.dev/docs/specs/),
[best practices](https://kiro.dev/docs/specs/best-practices/),
[issue #8859](https://github.com/kirodotdev/Kiro/issues/8859))

**Lessons taken**: "open work" = a committed file containing `[ ]` or `[-]`
— a dashboard can scan every repo with zero runtime integration; pipeline
phase × task completion is a two-axis status; reconcile state against
reality, don't trust checkboxes forever (workboard's stale detection is the
cheap version of this).

## Anthropic

- **Artifact-first memory**: the multi-agent research system persists plans
  and phase summaries to external memory because context truncates — the
  on-disk plan, not the transcript, is the canonical record. Checkpoint and
  resume rather than restart. Token usage explains ~80 % of performance
  variance, so cost belongs on any management surface.
  ([multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system))
- **Verification gates the stop**: every task carries a runnable check;
  agents "show evidence rather than asserting success" — explicitly because
  it matters "for sessions you weren't watching."
  ([Claude Code best practices](https://code.claude.com/docs/en/best-practices))
- Agents should "pause for human feedback at checkpoints or when
  encountering blockers" — blocked-on-human is a first-class state.
  ([Building effective agents](https://www.anthropic.com/engineering/building-effective-agents))

## OpenAI

- **Codex cloud task model** — the strongest published template for a unit
  of work: task → isolated environment → diff/PR → cited evidence (terminal
  logs, test output) → human review/merge.
  ([Codex cloud](https://developers.openai.com/codex/cloud),
  [Introducing Codex](https://openai.com/index/introducing-codex/))
- **Tracing hierarchy**: trace (workflow) → spans (tool calls, handoffs),
  with a `group_id` linking traces of one larger effort — the same shape as
  session → tool runs, grouped by spec.
  ([Agents SDK tracing](https://openai.github.io/openai-agents-python/tracing/))
- Escalate to humans on guardrail breach or repeated failure — the two
  intervention triggers.
  ([A practical guide to building agents, PDF](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf))

## DeepMind

- **AlphaEvolve**: controller + versioned program database + asynchronous
  evaluator fleet; every candidate gets a scalar score from an automated
  evaluator in an isolated environment — automated evaluation is what takes
  the human out of the inner loop. Cheap models for breadth, expensive for
  depth. ([blog](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/),
  [arXiv:2506.13131](https://arxiv.org/abs/2506.13131))
- **AGI safety approach**: monitor deployed agent *populations* in
  aggregate, not just per-agent logs — a fleet view is a safety control, not
  a convenience. ([arXiv:2504.01849](https://arxiv.org/html/2504.01849v1))

## Design principles workboard encodes

1. **Artifact-first**: read state from files on disk (task `Status:` lines,
   checkboxes, HANDOFF.md, metadata sidecars, git) — never transcripts
   (Anthropic memory pattern; Kiro committed specs; Antigravity brain).
2. **Inbox over inventory**: the top of the dashboard is the set of items
   demanding a human decision — blocked, needs-review, stale — sorted by
   severity (Antigravity Inbox; OpenAI escalation triggers).
3. **Small state machine**: `active / recent / idle / stale` for sessions;
   `blocked / needs-review / stale` for work. More states = less decision.
4. **Two-axis progress**: pipeline stage (spec → tasks → done) × task
   completion (Kiro), rendered as one bar with done + in-progress segments.
5. **Staleness is a first-class defect**: open work with no artifact-mtime
   or session activity past a threshold gets flagged — the reconcile-
   against-reality instinct (Kiro Sync Files; AlphaEvolve re-scoring).
6. **Population view**: one page over every repo and session, because
   aggregate anomalies (five dirty repos, three parked handoffs) are
   invisible per-session (DeepMind).
7. **Read-only**: observation must not mutate the system it observes;
   routing back into work happens through the existing pipeline skills.
