# Ultra Mode: Workflow-Backed Orchestration in the Existing Skills

> **Provenance:** interview 2026-07-03. Steven asked how ultracode (Claude Code's
> Workflow tool) fits the toolkit and commissioned a verified vendor survey —
> see `docs/orchestration-research-2026-07.md` (every claim 3-vote verified;
> the DeepMind leg did not survive verification and is an open question there).
> Decisions: **ultra mode inside existing skills** (no new skill names), all four
> scopes (critique panel, drain/parallel dispatch, verification votes,
> idea/research fan-out), placed per the model-agnostic spec's runtime-profile
> rule (`specs/model-agnostic/SPEC.md` R2–R5): Workflow-tool specifics live in
> `runtimes/claude-code.md`; their absence means today's behavior.

## Problem

The toolkit's orchestration is split between a deterministic file-based state
machine (/drain's committed `Status:` flips) and per-turn model judgment
(/build, /critique, /idea deciding each fan-out live). Claude Code's Workflow
tool now offers scripted orchestration — deterministic fan-out, barriers, token
budgets, adversarial-verify patterns, resumable runs — but the toolkit never
references it, so every ultra-style run is improvised per session. The vendor
survey confirms the design axis (Anthropic: predefined code paths for
well-defined tasks, model judgment only for open decisions; OpenAI: orchestrate
via code when determinism/cost matter, single agent by default) and warns the
cost: multi-agent runs ~10–15× single-agent tokens, gated in production by
prompted effort-scaling rules, not hard caps.

## Solution

Add an **ultra path** to critique, drain, parallel, build, and idea, gated on
two conditions (both required): the ultracode opt-in is active (user keyword,
session flag, or explicit ask — the Workflow tool's own opt-in rules) AND the
active runtime profile documents an orchestration section (i.e.
`runtimes/claude-code.md` in the toolkit checkout; absent in plugin installs
and eval fixtures → skills behave exactly as today). The profile carries the
workflow-script templates; the skills carry only tier-language pointers, per
the model-agnostic layering. File artifacts stay the interface everywhere:
workflow scripts read/write the same SPEC.md, task files, and `Status:` flips
that the non-ultra path uses, so an interrupted ultra run resumes from files —
drain's "orchestration without an orchestrator" invariant survives.

Research-derived design rules baked into the templates:

- **Deterministic where well-defined, model judgment where open** — the script
  owns loops/fan-out/gates; decomposition (/breakdown) and routing stay
  model-driven.
- **Effort tiers in dispatch prompts** (Anthropic's proven anti-runaway
  mechanism): simple lookup = 1 agent / 3–10 tool calls; comparison = 2–4
  agents / 10–15 calls each; 10+ agents only for genuinely breadth-first work.
- **Runnable checks before judges**: verification prefers acceptance commands;
  falls back to a single-call rubric judge (0–1 score + pass/fail); voting
  panels are reserved for adversarial critique. Evaluator-optimizer loops are
  bounded at 2–4 cycles in script-owned while-loops.
- **Single-agent default**: ultra never auto-triggers; the ~10–15× token
  multiple is spent only on breadth-first or verification-critical work.

## Requirements

- R1: `runtimes/claude-code.md` gains an `## Orchestration (ultra)` section
  containing: the two-condition gate above; a workflow-script template per
  ultra variant (critique panel, drain/parallel dispatch, verification votes,
  idea fan-out) using the Workflow tool's real API (agent/parallel/pipeline/
  phase/budget); the effort-tier prompt language; and resume instructions
  (scriptPath + resumeFromRunId, plus the rule that task-file state is the
  durable checkpoint — a resumed run re-reads `Status:` lines before
  dispatching).
- R2: **critique**: SKILL.md documents the ultra path — a panel of 3–5
  lens-diverse critics (correctness, security, verification-gaps, scope,
  cost-if-missed) run in parallel over the same artifact pointer, findings
  deduped then adversarially verified (a finding dies on majority refute)
  before being relayed. The single-critic path remains the default and the
  only path when the gate is closed; the skill text states when the panel is
  worth 10×+ tokens (pre-implementation specs, security-sensitive diffs, "be
  thorough" asks).
- R3: **drain and parallel**: SKILL.md documents the ultra dispatch path — the
  spec's `## Parallelization` groups compile into a workflow script: pipeline
  over groups (barrier only between dependency groups), one worker agent per
  task file (worktree isolation, same worker prompt as today with the
  effort-tier language added), verifier per completed task, and drain's
  status-flip + commit performed after each verdict exactly as the non-ultra
  path does. Budget guard: the script checks `budget.remaining()` before each
  dispatch when a target is set. Interrupting the workflow loses nothing:
  re-running non-ultra drain (or resuming the workflow) picks up from the
  committed task-file state.
- R4: **build**: SKILL.md documents ultra verification — acceptance commands
  run first (deterministic gate); criteria with no runnable command get a
  refute-majority vote (3 verifiers, distinct lenses); the fix-reverify loop
  is bounded at 4 cycles then flips to blocked with the failure evidence.
  Non-ultra build keeps its single verifier.
- R5: **idea**: SKILL.md documents ultra scouting — a multi-modal sweep
  (by-structure, by-convention, by-history, by-dependency scouts in parallel)
  plus a completeness critic before the interview, replacing the 2–4 ad-hoc
  scouts only when the gate is open and the idea spans multiple repos or
  subsystems.
- R6: Every ultra reference in skill text is gated language ("when the active
  runtime profile has an Orchestration section and the ultracode opt-in is
  active…") so plugin installs and eval fixtures — which have no `runtimes/`
  — read as today's skills verbatim. The evals suite gets a fixture assertion
  that each touched SKILL.md mentions the gate alongside every ultra mention
  (artifact-level check, no workflow execution in evals).
- R7: A decision record `docs/decisions/orchestration.md` captures: the
  adopt/leave-model-driven split, the effort tiers, the cost figures with
  their baseline ambiguity, the single-agent default, and links to
  `docs/orchestration-research-2026-07.md` + this spec. It also records the
  two deliberate non-adoptions: no auto-ultra heuristics, and no multi-judge
  voting as the default verifier (single-call rubric judge instead), with the
  research citations.
- R8: Toolkit hygiene: `bash tests/…` (existing suite) still passes; the four
  touched SKILL.md files stay within their current length discipline (the
  ultra sections are ≤ 25 lines each, detail lives in the runtime profile).

## Out of scope

- **Changing any non-ultra behavior** — with the gate closed, byte-for-byte
  today's semantics.
- **New skill names** (/ultra, /ultrabuild) — rejected in interview.
- **autopilot and breakdown changes** — autopilot inherits drain's worker
  prompt (already shared); breakdown's decomposition stays model-driven per
  the research; neither gains an ultra section in this pass.
- **A DeepMind/ADK-informed revision** — open question in the research doc;
  revisit if that leg ever verifies.
- **Auto-triggering ultra** by task-size heuristics — opt-in only.
- **Workflow scripts as committed artifacts** — scripts are generated
  per-run from the profile templates; only the templates are versioned.

## Acceptance criteria

- [ ] `grep -n "Orchestration (ultra)" runtimes/claude-code.md` hits, and the
      section contains all four templates, the effort-tier language
      ("3–10 tool calls"), and resume instructions (covers R1)
- [ ] For each of critique, drain, parallel, build, idea SKILL.md:
      `grep -q "ultra" <file>` hits AND every hit is within 3 lines of gate
      language referencing the runtime profile (script the check) (covers
      R2–R6)
- [ ] `grep -rn "ultra" .claude/skills/breakdown/ .claude/skills/autopilot/`
      returns nothing (covers Out of scope)
- [ ] The evals fixture assertion for gated ultra mentions passes as part of
      the evals suite run (covers R6)
- [ ] `test -f docs/decisions/orchestration.md` and it names both
      non-adoptions and links the research doc (covers R7)
- [ ] Existing toolkit tests pass; `wc -l` of each ultra section (between its
      heading and the next) ≤ 25 (covers R8)
- [ ] **End-to-end:** in a Claude Code session with ultracode active, run
      /critique against a fixture spec containing a planted contradiction and
      a planted un-runnable acceptance check — the panel path launches (a
      Workflow run is observable), both plants are found, and at least one
      spurious finding is killed by the verify vote; then run /critique in a
      fixture install with no runtimes/ dir — the single-critic path runs with
      no ultra mention in its output.

## Open questions

(none — gating, scope, placement, and verification defaults decided in
interview; research caveats are recorded in the decision record, not blocking)
