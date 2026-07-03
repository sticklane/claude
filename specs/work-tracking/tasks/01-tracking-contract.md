# Task 01: Discovered work, append-only task files, stopping points

Status: in-progress
Depends on: ../../review-fixes/tasks/07-evals-distribution-and-evidence.md, ../../context-management/tasks/03-tool-call-ceilings.md, ../../task-priority/tasks/01-priority-and-tiebreak.md, ../../tournament-votes/tasks/01-majority-votes.md
Priority: P1
Budget: 40 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4, R5, R7)

## Goal

Land the whole tracking contract: `Discovered:` + `Done vs remaining:`
worker-report sections (R1); drain-materialized deduped `Status: draft`
stubs with the vet/rewrite label, never dispatchable, never flipped by
drain (R2); /build's offer "only on the user's yes" (R3); append-only
task files with the verifier pathspec diff and drain's merge-base
re-check (R4); drain-written `## Progress` done-vs-remaining entries at
the real non-done events (R5); all antigravity mirrors (R7 — breakdown
mirror targets the SKILL, not the workflow shim). The spec's R-texts
are exact and were critic-hardened; follow them to the letter.

## Touch

- .claude/skills/drain/SKILL.md and reference.md (deps serialize the drain chain)
- .claude/skills/build/SKILL.md (rf-03/07 landed — deps above)
- .claude/skills/breakdown/SKILL.md (after task-priority 01)
- .claude/agents/verifier.md (after context-management 03)
- antigravity/.agents/workflows/{drain,build}.md, antigravity/.agents/skills/{breakdown,verifier}/SKILL.md

## Acceptance

- [ ] `grep -q "Discovered:" .claude/skills/drain/reference.md && grep -q "Discovered:" .claude/skills/build/SKILL.md` -> exit 0 (R1)
- [ ] `grep -q "Status: draft" .claude/skills/drain/SKILL.md && grep -qi "dedup" .claude/skills/drain/SKILL.md && grep -q "Discovered-by:" .claude/skills/drain/SKILL.md && grep -q "only a human" .claude/skills/drain/SKILL.md && grep -qi "never dispatchable" .claude/skills/drain/SKILL.md && grep -qi "vet" .claude/skills/drain/SKILL.md` -> exit 0 (R2)
- [ ] `grep -q "only on the user's yes" .claude/skills/build/SKILL.md` -> exit 0 (R3)
- [ ] `grep -q "may flip only" .claude/skills/drain/reference.md && grep -q "may flip only" .claude/skills/breakdown/SKILL.md && grep -qi "git diff" .claude/agents/verifier.md && grep -q "merge-base" .claude/skills/drain/SKILL.md` -> exit 0 (R4)
- [ ] `grep -q "## Progress" .claude/skills/drain/SKILL.md && grep -qi "done vs remaining" .claude/skills/drain/SKILL.md` -> exit 0 (R5)
- [ ] `grep -q "Discovered:" antigravity/.agents/workflows/drain.md && grep -q "merge-base" antigravity/.agents/workflows/drain.md && grep -q "may flip only" antigravity/.agents/skills/breakdown/SKILL.md && grep -qi "git diff" antigravity/.agents/skills/verifier/SKILL.md` -> exit 0 (R7)
- [ ] Manual paper dry-run per the spec's end-to-end criterion: BLOCKED worker with one Discovered item -> one draft stub (vet label), one Progress entry, one commit; duplicate discovery -> no second stub; draft never dispatchable, never flipped by drain
