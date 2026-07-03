# Code-vs-LLM ladder for architecting generative-AI features

## Problem

When a spec involves EMBEDDING generative AI in the product ("summarize
the ticket", "route the email", "chat over our docs"), the toolkit's
architectural skills have no framework for the first-order decision:
which parts should be deterministic code and which should be model
calls. /design judges candidates on requirements fit, verification
story, on-distribution, and simplicity (SKILL.md:52-62) but never asks
the ladder question; /idea's interview covers integration points but
not the judgment-vs-rules split. All three vendors publish converging
guidance (research recorded by this spec in docs/external-playbooks.md):
default deterministic, escalate one rung at a time — pure code → single
LLM call with structured output → workflow patterns → single agent →
multi-agent — with orchestration and side effects staying in code and
schema-constrained output at every code/LLM seam.

## Solution

Four decisions, recommended options adopted (interview picker failed 3/3
this session; non-interactive fallback, reversible): (1) the operational
framework — the five-rung ladder, per-component tests, and seam rules —
lives in a NEW `.claude/skills/design/reference.md`, loaded on demand
per the heavy-reference convention; the research record (sources, vendor
agreement/disagreement, the ~4×/~15× cost curve) lives in
docs/external-playbooks.md; (2) `/design` step 1 (Frame it) gains a
classification gate for LLM-embedding decisions and step 3's ranking
gains the lower-rung tiebreak; (3) `/idea`'s interview (technical
approach) gains the which-parts-are-code question for generative-AI
features; (4) the ladder governs PRODUCT architecture only — the
toolkit's own agent-usage economics stay in token-discipline, and
/idea's existing "a script, not a spec" gate keeps governing process
work (one cross-reference sentence each, no duplication). Marker
phrases ("code-vs-LLM", "lowest rung", "## The ladder", "which parts
are code") do not exist in the repo today.

## Requirements

- R1 (the reference): `.claude/skills/design/reference.md` is created
  with three sections: `## The ladder` — five rungs (0 pure code, 1
  single LLM call + retrieval/examples + structured output, 2 workflow
  patterns: prompt-chaining, routing, parallelization,
  orchestrator-workers, evaluator-optimizer with each pattern's trigger,
  3 single agent — open-ended step count plus OpenAI's three criteria,
  4 multi-agent — breadth-first parallelizable only) each with its
  escalation trigger; `## Per-part tests` — rule-expressible, nuanced
  judgment, ruleset maintainability, unstructured input, failure
  tolerance, latency/cost, eval-ability (escalate only when evals show
  the lower rung failing); `## Seam rules` — structured output at every
  code/LLM boundary and validated in application code (recording the
  OpenAI-vs-Gemini disagreement, siding with validation), side effects
  and loop exits live in code, the model emits arguments only. If over
  100 lines it opens with a TOC (per the context-management spec's
  convention; target well under that).
- R2 (design framing gate): `.claude/skills/design/SKILL.md` step 1
  gains a sentence containing "code-vs-LLM": when the decision involves
  embedding generative AI in the product, classify each part of the
  feature with the ladder in reference.md BEFORE framing candidates —
  the lowest rung that meets requirements is the default candidate, and
  higher-rung candidates must name the failing test that justifies
  escalation.
- R3 (design ranking tiebreak): step 3's ranking sentence is extended:
  for LLM-embedding decisions, "simplicity" means the lowest rung —
  contains the phrase "lowest rung". Step 3's SPEC.md-appendix bullet (the one recording
  candidates considered and rationale) gains: "and, when the ladder
  applied, the chosen rung per component".
- R4 (idea interview): `.claude/skills/idea/SKILL.md`'s interview
  section (Technical approach bullet) gains one line containing "which
  parts are code": for features involving generative AI, ask which
  parts need model judgment and which are rules — defaulting per
  /design's ladder, and recording the split in the spec's Solution.
- R5 (scope separation): one sentence in design/reference.md's intro
  states the ladder governs product architecture; the toolkit's own
  agent-usage scaling lives in `.claude/rules/token-discipline.md`, and
  process-work right-sizing in /idea's existing script-not-a-spec gate
  (cross-references, no restated content).
- R6 (research record): `docs/external-playbooks.md` gains a
  "Code-vs-LLM ladder" entry: the three-vendor agreement (default
  deterministic, incremental escalation, code owns orchestration and
  side effects, structured output at seams, smallest capable model),
  the named disagreements (Google's multi-agent lean; structured-output
  validation), the ~4× agent / ~15× multi-agent token-cost anchors, and
  source links; notes the Agents Companion is secondary-verified.
- R7 (mirrors): `antigravity/.agents/skills/design/SKILL.md` mirrors
  R2/R3, and a new `antigravity/.agents/skills/design/reference.md`
  mirrors R1 (the port's skills are near-identical by convention);
  the antigravity idea skill mirrors R4.
- R8 (versioning): the implementing change bumps `plugin.json`'s minor
  version by one from the value it finds, unless landing in a commit-set
  whose other specs already carry a single combined bump.

## Out of scope

- Any change to /breakdown, /build, /drain, or the worker prompts — the
  ladder shapes specs and design decisions, not execution.
- API-level implementation guidance (SDK code, structured-output
  schemas, function-calling examples) — the claude-api harness skill
  and vendor docs own that; the reference stays decision-level.
- Re-litigating the toolkit's own multi-agent architecture (governed by
  token-discipline and the parallel/drain cost warnings).
- A standalone new skill — the ladder rides inside /design and /idea.
- Model-selection tables (owned by the model-agnostic spec's runtime
  profiles).

## Acceptance criteria

- [ ] `test -f .claude/skills/design/reference.md && grep -q "^## The ladder" .claude/skills/design/reference.md && grep -q "^## Per-part tests" .claude/skills/design/reference.md && grep -q "^## Seam rules" .claude/skills/design/reference.md` (R1)
- [ ] `for n in 0 1 2 3 4; do grep -qi "rung $n" .claude/skills/design/reference.md || exit 1; done && grep -qi "evaluator-optimizer" .claude/skills/design/reference.md && grep -qi "validated in application code\|validate.*application code" .claude/skills/design/reference.md` (R1 — all five rungs present + seam rule)
- [ ] `[ "$(wc -l < .claude/skills/design/reference.md)" -le 100 ] || head -5 .claude/skills/design/reference.md | grep -qi "contents\|TOC"` (R1 size/TOC)
- [ ] `grep -q "code-vs-LLM" .claude/skills/design/SKILL.md` (R2)
- [ ] `grep -q "lowest rung" .claude/skills/design/SKILL.md` (R3)
- [ ] `grep -q "which parts are code" .claude/skills/idea/SKILL.md` (R4)
- [ ] `grep -q "token-discipline" .claude/skills/design/reference.md && grep -qi "script, not a spec" .claude/skills/design/reference.md` (R5)
- [ ] `grep -qi "code-vs-LLM ladder" docs/external-playbooks.md && sed -n '/[Cc]ode-vs-LLM ladder/,/^## /p' docs/external-playbooks.md | grep -qi "4×\|4x"` (R6 — scoped to this spec's entry so the sibling spec's 15× elsewhere in the file can't satisfy it)
- [ ] `grep -q "code-vs-LLM" antigravity/.agents/skills/design/SKILL.md && test -f antigravity/.agents/skills/design/reference.md && grep -q "which parts are code" antigravity/.agents/skills/idea/SKILL.md` (R7)
- [ ] plugin.json minor version strictly greater than the pre-implementation value, verified in the implementing task's evidence (R8)
- [ ] End to end: in a fresh session, run /design on a toy decision "add an email-triage feature: parse sender/date, categorize intent, draft replies" — the recorded decision classifies parsing as code (rung 0), categorization as a single structured-output call (rung 1), and names a failing test before any candidate proposes an agent (manual dry-read until the eval harness covers /design).

## Open questions

(none — the four decisions are recorded in Solution; recommended options
adopted per the non-interactive fallback, reversible before
implementation.)
