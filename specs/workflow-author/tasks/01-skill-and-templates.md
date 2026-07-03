# Task 01: workflow-author skill, templates, premise verification

Status: in-progress
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

## Acceptance

- [ ] `test -f .claude/skills/workflow-author/SKILL.md && [ "$(wc -l < .claude/skills/workflow-author/SKILL.md)" -le 100 ] && ! grep -q "^disable-model-invocation" .claude/skills/workflow-author/SKILL.md && grep -q "human-gates" .claude/skills/workflow-author/SKILL.md` -> exit 0 (R1)
- [ ] `grep -q "sole writer" .claude/skills/workflow-author/SKILL.md && grep -q "BLOCKED" .claude/skills/workflow-author/SKILL.md && grep -q "budget.remaining()" .claude/skills/workflow-author/SKILL.md` -> exit 0 (R3)
- [ ] `test -f .claude/skills/workflow-author/reference.md && grep -q "tournament.js" .claude/skills/workflow-author/reference.md && grep -q "queue-wave.js" .claude/skills/workflow-author/reference.md && grep -q "tournament-votes" .claude/skills/workflow-author/reference.md && grep -q "export const meta" .claude/skills/workflow-author/reference.md` -> exit 0 (R4)
- [ ] `test -f specs/workflow-author/evidence/01.md` and it records the premise re-verification (R6)
