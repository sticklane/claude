# Task 01: `## Orchestration (ultra)` section in runtimes/claude-code.md

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: done
Depends on: none
Priority: P1
Budget: 40 turns
Spec: ../SPEC.md (requirements R0, R1)
Touch: runtimes/claude-code.md

## Goal

`runtimes/claude-code.md` (which exists — model-agnostic landed, so R0's
create-branch is moot) gains an `## Orchestration (ultra)` section: the
two-condition gate (ultracode opt-in per the Workflow tool's own rules,
restated as keyword / session flag / explicit ask, AND an active runtime
profile with an orchestration section), one workflow-script template per
ultra variant (critique panel, drain/parallel dispatch, verification
votes, idea fan-out), the effort-tier prompt language ("3–10 tool calls"
ladder), and resume instructions (scriptPath + resumeFromRunId; task-file
`Status:` lines re-read before dispatch as the durable checkpoint). Adds
the cross-reference note so a later model-agnostic editor doesn't
normalize the fourth section away.

## Touch

Single file. Must NOT touch: any SKILL.md (task 02 owns the five skills),
evals/, docs/decisions, plugin.json.

## Steps

1. **API verification first (mandatory):** re-verify the Workflow tool's
   live schema in-session (agent/parallel/pipeline/phase/log/budget;
   scriptPath + resumeFromRunId; budget.remaining()); date-stamp the
   schema check in the template comments.
2. Confirm the acceptance greps fail (RED).
3. Write the section per R1, templates commented with the schema-check
   date; keep templates aligned with the research-derived rules
   (deterministic-vs-model split, effort tiers, runnable checks before
   judges, bounded evaluator loops, single-agent default).
4. Run acceptance.

## Acceptance

- [x] `grep -n "Orchestration (ultra)" runtimes/claude-code.md` → hit; section contains all four templates, the effort-tier language (`grep -q "3–10 tool calls" runtimes/claude-code.md || grep -q "3-10 tool calls" runtimes/claude-code.md`), resume instructions, and a schema-check date comment — verifier PASS: heading L60, four distinct templates (critique-panel/drain-dispatch/build-verify/idea-scout), effort-tier grep exit 0, `### Resume` present, `SCHEMA-CHECK DATE: 2026-07-03` comment (see evidence/01-runtime-orchestration-section.md)
- [x] `grep -q "resumeFromRunId" runtimes/claude-code.md && grep -qi "Status:" runtimes/claude-code.md` → exit 0 — verifier PASS: resumeFromRunId L100/114, Status-line re-read as durable checkpoint L103
- [x] Section notes the model-agnostic cross-reference (sanctioned fourth section) — verifier PASS: cross-reference note L62-69 cites specs/model-agnostic/SPEC.md R1 as a sanctioned superset
