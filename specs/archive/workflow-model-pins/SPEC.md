# Workflow stages: pin model, not just effort, on mechanical fan-outs

Status: open
Priority: P1
Breakdown-ready: true

## Problem

`agent:workflow-subagent` spent $549 in the 2026-06-27→07-11 window, $486
of it on fable-5 (see EVIDENCE.md) — the frontier session model running
mechanical fan-out stages. The token-discipline rule ("Tier by stage type":
mechanical stages run scout-tier) is half-applied in the one workflow
script this repo ships: `.claude/workflows/deep-research.js` passes
`effort: "low"` on its Search and Fetch/Extract stages (lines ~185, ~219)
but never passes `model`, so those agents inherit the calling session's
model. Effort is not price: a low-effort fable call still bills fable
rates. skill:deep-research alone ran 917 fable calls ($167) in the window;
its Fetch stage moved 2.61M uncached input tokens through fable pricing.

The same gap is doctrinal: the workflow-author skill
(`.claude/skills/workflow-author/SKILL.md`) bakes toolkit guards into
generated scripts but does not require a stage to declare a `model`
alongside `effort`, so every future authored workflow repeats the mistake.
The Workflow tool's own guidance ("default to omitting model") is tuned for
judgment stages and is the wrong default for mechanical ones — the
toolkit's tier ladder (token-discipline.md "Model and effort matching")
already says so; the scripts just don't implement it.

Note specs/agent-tier-leaks explicitly declared workflow-subagent model
policy out of scope ("that's the workflow author's lever") — this spec is
that lever.

## Solution

Pin scout-tier models on deep-research's mechanical stages, and make
"mechanical stage ⇒ model AND effort, explicitly" a workflow-author
authoring rule so generated scripts carry the pin from birth. Judgment
stages (Verify, Synthesize) keep inheriting the session model — unchanged.

## Requirements

- R1 **deep-research mechanical stages pinned.** In
  `.claude/workflows/deep-research.js`, every `agent()` call in the Search
  and Fetch/Extract phases passes both `model` (scout-tier alias, i.e.
  `haiku`) and the existing `effort: "low"`. Scope/Verify/Synthesize
  stages stay on the session model (no `model` opt), matching the file's
  own header comments. Phase metadata/comments updated to say
  "haiku + effort:low" where they currently say only "effort:low".
- R2 **Workflow-author authoring rule.** The workflow-author skill
  requires every mechanical stage (search, fetch, extract, grep-like
  scouting, conformance checks) to pass BOTH `model` (cheap tier) and
  `effort: 'low'`, and requires judgment stages to omit `model`
  deliberately (inherit) — a one-line comment in the generated script
  naming which of the two each stage is. The rule lands in an
  ALWAYS-APPLIES location (Procedure step 2, or a new subsection outside
  the "Doctrine guards" block) — NOT under the doctrine-guards preamble,
  whose "every generated script that touches queue state carries all
  four" scope would read the rule as queue-state-only and exclude
  deep-research-shaped workflows entirely. Template/example snippets in
  the skill updated to match.
- R3 **Plugin hygiene (skill change only).** The antigravity mirror does
  NOT apply to this spec: workflow-author is explicitly not ported
  (`antigravity/README.md:40`) and `.claude/workflows/*.js` has no
  antigravity analog — do not create ports. The R2 skill edit requires a
  `.claude-plugin/plugin.json` version bump; the R1 workflow-script edit
  does not (plugins cannot ship workflows — workflow-author
  SKILL.md:8-9). R3 is the closing task and OWNS the bump: it lands in
  this spec's shipping commits before `claude plugin validate .` runs,
  and R3's task `Touch:` must list `.claude-plugin/plugin.json`.
  `claude plugin validate .` passes after the bump.

## Out of scope

- Retuning the tier ladder or agent frontmatter pins (unchanged).
- The harness Workflow tool's own defaults (upstream, not ours).
- Ad-hoc/inline workflows already run from past sessions.
- general-purpose Agent-tool dispatch outside workflows (covered by the
  freehand fan-out doctrine landed via specs/drain-wake-cost/tasks/02).

## Acceptance criteria

- [ ] Every `agent(` call in the Search and Fetch phases of
  `.claude/workflows/deep-research.js` includes both `model:` and
  `effort:` opts; Verify/Synthesize calls include neither a `model:` opt
  nor an `effort:` downgrade — checked by grep + MANUAL read of the five
  phases (R1)
- [ ] `node --check .claude/workflows/deep-research.js` passes (script
  stays parseable JS) (R1)
- [ ] workflow-author SKILL.md names the both-or-neither rule:
  `grep -qi 'model' .claude/skills/workflow-author/SKILL.md` hits AND
  MANUAL: rule states mechanical stages pass model+effort, judgment
  stages inherit deliberately, and it sits OUTSIDE the queue-state-scoped
  doctrine-guards preamble (R2)
- [ ] `claude plugin validate .` passes; `.claude-plugin/plugin.json` is
  bumped in this spec's shipping commits (R3, the closing task, owns the
  bump); NO antigravity files are added or changed by this spec (R3)
- [ ] MANUAL (deferred, needs runs): next 7-day agentprof window shows
  skill:deep-research model mix majority-haiku by calls on Search/Fetch
  stages (marker frames from specs/agentprof-instrumentation make the
  stages visible)

## Open questions

- Whether Verify's 3-vote refuters count as judgment (keep session model)
  or mechanical (pin sonnet). Default: judgment — refutation quality is
  the product; note the decision in the file header.

## Parallelization

Task map: 01 = R1 (deep-research.js), 02 = R2 (workflow-author skill) —
disjoint Touch, no shared undecided design; 03 = R3 closing gate after
both (format grammar per specs/drain-rolling-window/SPEC.md's
Parallelization section).

- Group: 01, 02
