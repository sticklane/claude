# Task 01: workflow-author skill, templates, premise verification

Status: done
Depends on: ../../tournament-votes/tasks/01-majority-votes.md
Priority: P2
Budget: 30 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4, R6)

## Goal

Create `.claude/skills/workflow-author/` (SKILL.md <=100 lines,
model-invocable, human-gates citation) and reference.md (the <=25-line
API summary that is the worker's sole source — scripts have NO
filesystem access — plus tournament.js and queue-wave.js templates;
tournament.js cites specs/tournament-votes as design owner, now
landed). Re-verify the plugins-cannot-ship-workflows premise per R6
and record it in this task's evidence file
(specs/workflow-author/evidence/01.md).

## Touch

- .claude/skills/workflow-author/SKILL.md (new)
- .claude/skills/workflow-author/reference.md (new)
- specs/workflow-author/evidence/01.md (new)

## Steps

1. SKILL.md per R1+R2 (five procedure steps; doctrine guards R3 with
   "sole writer", "BLOCKED", "budget.remaining()").
2. reference.md per R4 (API summary contents enumerated in R4; both
   templates; barrier-justification comments).
3. Premise re-verification per R6, recorded in evidence.
4. No plugin.json bump (rf-99 owns it).

<!-- Plan (build step 1):
1. Run acceptance commands first — confirm RED (files absent).
2. .claude/skills/workflow-author/SKILL.md: model-invocable frontmatter with
   trigger phrases; human-gates reason-5 sentence; five R2 steps; R3 guards
   ("sole writer", "BLOCKED", "budget.remaining()"); Next stage line. <=100 lines.
3. .claude/skills/workflow-author/reference.md: TOC; <=25-line API summary
   (all R4 items incl. no-filesystem-access); tournament.js (majority-PASS
   cites specs/tournament-votes/SPEC.md) + queue-wave.js templates, four
   guards demonstrated in both, barrier-justification comments.
4. specs/workflow-author/evidence/01.md: R6 premise re-verified 2026-07-03
   against plugins-reference (workflows absent from components) and
   workflows.md (project+user resolution only). Premise HOLDS; no correction.
Risks: SKILL.md line count; negative grep is line-anchored so never start a
line with "disable-model-invocation"; API summary line budget.
-->

## Acceptance

- [x] `test -f .claude/skills/workflow-author/SKILL.md && [ "$(wc -l < .claude/skills/workflow-author/SKILL.md)" -le 100 ] && ! grep -q "^disable-model-invocation" .claude/skills/workflow-author/SKILL.md && grep -q "human-gates" .claude/skills/workflow-author/SKILL.md` -> exit 0 (R1)
  Evidence: verifier ran it verbatim, exit 0; 66 lines — evidence/01.md, item 1.
- [x] `grep -q "sole writer" .claude/skills/workflow-author/SKILL.md && grep -q "BLOCKED" .claude/skills/workflow-author/SKILL.md && grep -q "budget.remaining()" .claude/skills/workflow-author/SKILL.md` -> exit 0 (R3)
  Evidence: verifier exit 0; four guards also demonstrated in both templates — evidence/01.md, item 2 and R3 spot-check.
- [x] `test -f .claude/skills/workflow-author/reference.md && grep -q "tournament.js" .claude/skills/workflow-author/reference.md && grep -q "queue-wave.js" .claude/skills/workflow-author/reference.md && grep -q "tournament-votes" .claude/skills/workflow-author/reference.md && grep -q "export const meta" .claude/skills/workflow-author/reference.md` -> exit 0 (R4)
  Evidence: verifier exit 0; API summary 25 lines with every R4 item — evidence/01.md, item 3 and R4 spot-check.
- [x] `test -f specs/workflow-author/evidence/01.md` and it records the premise re-verification (R6)
  Evidence: verifier exit 0; dated docs re-check recorded, premise HOLDS — evidence/01.md, R6 section.
