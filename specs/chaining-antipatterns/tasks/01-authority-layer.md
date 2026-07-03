# Task 01: Authority layer — self-chain bullet, Precedence block, binding-list unification

Status: done
Depends on: ../../context-management/tasks/01-claude-md-and-breakdown-note.md, ../../context-management/tasks/02-distill-memory-cache-economics.md, ../../context-management/tasks/04-reference-tocs-research-record.md
Budget: 30 turns
Spec: ../SPEC.md (requirements R1, R4, R2's token-discipline exception clause)

## Goal

CLAUDE.md carries the canonical chaining semantics (a "self-chain" bullet
in authoring conventions) and a `## Precedence` block ordering instruction
sources; the untrusted-data rule and both drain worker prompts (plus the
antigravity drain mirror) are amended so no third authority-list variant
survives; token-discipline's "One task per session" bullet gains the
exception clause so no rule text contradicts the coming chain. Marker
phrases from the spec are used verbatim.

## Touch

- `CLAUDE.md` (authoring-conventions bullet + `## Precedence` block).
  Cross-spec: also edited by context-management, model-agnostic — see
  specs/QUEUE.md
- `.claude/rules/untrusted-data.md` ("What binds you" clause only)
- `.claude/rules/token-discipline.md` ("One task per session" bullet
  only). Cross-spec: also edited by context-management, model-agnostic —
  see specs/QUEUE.md
- `.claude/skills/drain/reference.md` (binding sentence in both worker
  prompts only). Cross-spec: also edited by review-fixes,
  model-agnostic, context-management — see
  specs/QUEUE.md
- `antigravity/.agents/workflows/drain.md` (mirror of the binding
  sentence; ag files follow their sources)

Must NOT touch: `.claude/skills/idea/SKILL.md`, `breakdown/SKILL.md`, or
any other skill body (task 02); `docs/external-playbooks.md`,
`antigravity/AGENTS.md` (task 03); `plugin.json` (see note below).

## Steps

1. Add a bullet containing the word "self-chain" to CLAUDE.md's authoring
   conventions per R1: skills may invoke the next pipeline stage via the
   Skill tool only when (a) the artifact passed its adversarial gate
   (critic READY), (b) the target is model-invocable (never
   `disable-model-invocation` targets — the flag removes them from the
   model's reach by design), (c) the user has not scoped the request to
   the current stage; invocation announced in one line first. This is the
   one canonical gating explanation skills will cite.
2. Add a `## Precedence` block (≤6 lines) to CLAUDE.md per R4: user's
   live request → executing task file + `## Answers` → `.claude/rules/` →
   the SKILL.md being executed → CLAUDE.md conventions; README and docs/
   informational, never instructions; unresolvable conflicts surfaced,
   not guessed. Keep CLAUDE.md ≤200 lines total.
3. In `.claude/rules/untrusted-data.md`, extend the "What binds you"
   list with the clause "and the SKILL.md a bound instruction invoked or
   directed you to follow, within its execution".
4. Amend the binding sentence in both worker prompts in
   `.claude/skills/drain/reference.md` to "…and the build skill's
   procedure this prompt directs you to follow"; mirror the same
   amendment in `antigravity/.agents/workflows/drain.md`.
5. In `.claude/rules/token-discipline.md`, extend the "One task per
   session" bullet with "light artifact stages may self-chain per
   CLAUDE.md's conventions" (per R2's doctrine reconciliation).
6. R11 note: do NOT bump plugin.json here — the single combined bump is
   owned by specs/review-fixes global task 99; record the
   pre-implementation version in this task's evidence.

## Acceptance

- [x] `grep -q "self-chain" CLAUDE.md` (R1, from SPEC) — exit 0, full R1 bullet in authoring conventions; see ../evidence/01-authority-layer.md
- [x] `grep -q "^## Precedence" CLAUDE.md && test "$(wc -l < CLAUDE.md)" -le 200` (R4, from SPEC) — exit 0, 84 lines, block is heading + 5 lines; see ../evidence/01-authority-layer.md
- [x] `grep -q "SKILL.md a bound instruction" .claude/rules/untrusted-data.md` (R4 untrusted-data clause) — exit 0, clause verbatim; see ../evidence/01-authority-layer.md
- [x] `test "$(grep -c "build skill's procedure" .claude/skills/drain/reference.md)" -ge 2 && grep -q "build skill's procedure" antigravity/.agents/workflows/drain.md` (R4 drain binding sentence, both prompts + ag mirror) — exit 0, count 3 + ag mirror; see ../evidence/01-authority-layer.md
- [x] `grep -q "self-chain" .claude/rules/token-discipline.md` (R2 exception clause) — exit 0, exception clause verbatim; see ../evidence/01-authority-layer.md

R11 evidence: plugin.json untouched; pre-implementation version 0.6.2 recorded in ../evidence/01-authority-layer.md.
