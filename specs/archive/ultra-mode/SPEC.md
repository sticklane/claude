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

- R0 (sequencing/dependency): `runtimes/` does not exist yet — it is created
  by `specs/model-agnostic/SPEC.md` (tasks queued in `specs/QUEUE.md`). Either
  model-agnostic lands first, or this spec's implementer creates
  `runtimes/claude-code.md` with model-agnostic R1's structure (`## Tiers` /
  `## Headless` / `## Notes`) before adding the section below — the added
  fourth section is a sanctioned superset of model-agnostic R1's
  three-section minimum (cross-reference it there so a later model-agnostic
  implementer doesn't "normalize" it away). Add ultra-mode to `specs/QUEUE.md`
  with this dependency edge.
- R1: `runtimes/claude-code.md` gains an `## Orchestration (ultra)` section
  containing: the two-condition gate above (including WHERE the ultracode
  opt-in rules are defined: the Workflow tool's own tool description — the
  profile section restates the opt-in forms: "ultracode" keyword, session
  flag, or the user's own explicit ask); a workflow-script template per ultra
  variant (critique panel, drain/parallel dispatch, verification votes, idea
  fan-out); the effort-tier prompt language; and resume instructions
  (scriptPath + resumeFromRunId, plus the rule that task-file state is the
  durable checkpoint — a resumed run re-reads `Status:` lines before
  dispatching). **API verification step (mandatory, first):** the API names
  used here (agent/parallel/pipeline/phase/log/budget; scriptPath +
  resumeFromRunId; budget.remaining()) were recorded from a live Workflow
  tool schema on 2026-07-03, but the implementer MUST re-verify against the
  live tool schema in-session before writing templates, and template
  comments must note the schema-check date.
- R2: **critique**: SKILL.md documents the ultra path — a panel of 3–5
  lens-diverse critics (correctness, security, verification-gaps, scope,
  cost-if-missed) run in parallel over the same artifact pointer, findings
  deduped then adversarially verified (a finding dies on majority refute)
  before being relayed. The single-critic path remains the default and the
  only path when the gate is closed; the skill text states when the panel is
  worth 10×+ tokens (pre-implementation specs, security-sensitive diffs, "be
  thorough" asks).
- R3: **drain and parallel**: SKILL.md documents the ultra dispatch path — the
  dependency graph compiles **from the task files' `Depends on:` headers**
  (the machine-readable source drain already uses; a spec's
  `## Parallelization` section is a human view and, per QUEUE.md, often just a
  pointer) into a workflow script: pipeline
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
- R6: Every ultra reference in skill text lives under a dedicated
  `## Ultra path` heading and uses gated language containing the literal
  marker phrase **"active runtime profile"** so plugin installs and eval
  fixtures — which have no `runtimes/` — read as today's skills verbatim.
  Enforcement is a standalone, model-free lint script
  `evals/lint-ultra-gate.sh`: for each of the five touched SKILL.md files, a
  case-insensitive match of "ultra" must have the literal string "active
  runtime profile" within ±3 lines; exits non-zero listing violations. It is
  NOT wired into `evals/run.sh` (which runs model sessions per scenario);
  it's invoked directly and referenced from the testing section of CLAUDE.md.
- R7: A decision record `docs/decisions/orchestration.md` captures: the
  adopt/leave-model-driven split, the effort tiers, the cost figures with
  their baseline ambiguity, the single-agent default, and links to
  `docs/orchestration-research-2026-07.md` + this spec. It also records the
  two deliberate non-adoptions: no auto-ultra heuristics, and no multi-judge
  voting as the default verifier (single-call rubric judge instead), with the
  research citations.
- R8: Toolkit hygiene: `bash evals/lint-ultra-gate.sh` passes (there is no
  `tests/` dir in this repo; the model-driven suite `evals/run.sh` requires
  model access and is run per changed skill only where an evalset exists —
  not a gate for this spec); each of the **five** touched SKILL.md files
  (critique, drain, parallel, build, idea) keeps its `## Ultra path` section
  ≤ 25 lines, detail in the runtime profile.
- R9: Repo authoring conventions (CLAUDE.md) are honored: the antigravity/
  mirror gets the corresponding skill-text changes in the same commit (the
  gate reads as permanently closed there — Antigravity has no Workflow tool
  or runtimes/, so mirrored text must degrade to a no-op mention or be
  adapted per the mirror's existing porting pattern), and
  `.claude-plugin/plugin.json` `version` is bumped since skill behavior
  changes. Note the plugin install ships without `runtimes/`, so plugin
  users always see the closed-gate path — by design.

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

- [ ] `grep -n "Orchestration (ultra)" runtimes/claude-code.md` hits (the file
      created per R0 if model-agnostic hasn't landed), the section contains
      all four templates, the effort-tier language ("3–10 tool calls"),
      resume instructions, and a schema-check date comment; `specs/QUEUE.md`
      lists ultra-mode with its dependency (covers R0, R1)
- [ ] `bash evals/lint-ultra-gate.sh` exits 0 (every case-insensitive "ultra"
      in the five SKILL.md files has the literal "active runtime profile"
      within ±3 lines, each under a `## Ultra path` heading); deleting the
      marker phrase from one file makes it exit non-zero naming that file
      (covers R2–R6)
- [ ] `grep -rn "ultra" .claude/skills/breakdown/ .claude/skills/autopilot/`
      returns nothing (covers Out of scope)
- [ ] `test -f docs/decisions/orchestration.md` and it names both
      non-adoptions and links the research doc (covers R7)
- [ ] `wc -l` of each `## Ultra path` section (between its heading and the
      next heading) ≤ 25 in all five files (covers R8)
- [ ] `git show --stat HEAD` for the implementing commit(s) touches the
      antigravity mirror alongside each changed skill, and
      `.claude-plugin/plugin.json` version is bumped (covers R9)
- [ ] **End-to-end:** in a Claude Code session with ultracode active, run
      /critique against a fixture spec containing a planted contradiction, a
      planted un-runnable acceptance check, AND a planted plausible-but-false
      "bug" designed to bait a refutable finding — the panel path launches (a
      Workflow run is observable), both real plants are found, and the run
      log shows the verify-vote phase executed with any refuted finding
      dropped from the relayed set; then run /critique in a fixture install
      with no runtimes/ dir — the single-critic path runs with no ultra
      mention in its output.

## Open questions

(none — gating, scope, placement, and verification defaults decided in
interview; research caveats are recorded in the decision record, not blocking)

## Parallelization

See specs/QUEUE.md (canonical, single copy) — this spec's tasks are
wired into the combined wave plan there; the Depends-on headers in
tasks/ are the machine-readable source.

## Amendments

- **2026-07-03 (breakdown critic):** R8's parenthetical "there is no
  tests/ dir in this repo" is stale — tests/ exists (hook-template and
  install-gates suites). The operative rule stands: lint-ultra-gate.sh
  is invoked directly, not wired into evals/run.sh or any aggregate
  runner.
