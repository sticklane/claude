# Task 01: Priority header, breakdown rubric, drain tie-break, mirrors

Status: pending
Depends on: ../../review-fixes/tasks/02-drain-state-machine.md, ../../review-fixes/tasks/03-header-contract.md, ../../context-management/tasks/01-claude-md-and-breakdown-note.md, ../../chaining-antipatterns/tasks/03-antipattern-guards.md
Priority: P1
Budget: 25 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R5)

## Goal

Add the optional `Priority: P0-P3` header (absent = P2) to breakdown's
template with the four-line rubric, and the deterministic tie-break to
drain's dispatch (Priority, then unblocking-power counted over this
run's inventory resolving Depends-on exactly as dispatchability does,
then path). rf-03 has already landed the five-field inventory tuple.
Mirror into the antigravity breakdown SKILL (not the workflow shim)
and drain workflow. Spec R1/R2/R3/R5 are exact.

## Touch

- .claude/skills/breakdown/SKILL.md (also edited by rf-03, cm-01, ca-02/03 — deps serialize)
- .claude/skills/drain/SKILL.md (also edited by rf-02/03 — deps serialize)
- antigravity/.agents/skills/breakdown/SKILL.md
- antigravity/.agents/workflows/drain.md

## Steps

1. Template `Priority: P2` line + absent-means-P2 comment (R1).
2. Rubric in breakdown's ordering step (R3, phrases "unblocking", "P0").
3. Tie-break sentence in drain's dispatch section (R2, phrases "tie-break", "Priority").
4. Mirrors (R5). No plugin.json bump (rf-99 owns it).

## Acceptance

- [ ] `grep -q "Priority: P2" .claude/skills/breakdown/SKILL.md && grep -q "P0" .claude/skills/breakdown/SKILL.md && grep -qi "unblocking" .claude/skills/breakdown/SKILL.md` -> exit 0 (R1+R3)
- [ ] `grep -q "tie-break" .claude/skills/drain/SKILL.md && grep -q "Priority" .claude/skills/drain/SKILL.md && grep -qi "unblocking" .claude/skills/drain/SKILL.md` -> exit 0 (R2)
- [ ] `grep -q "Priority" antigravity/.agents/skills/breakdown/SKILL.md && grep -qi "tie-break" antigravity/.agents/workflows/drain.md` -> exit 0 (R5)
- [ ] Manual paper dry-run per the spec's end-to-end criterion: tasks A (P1, 0 dependents) / B (no header, 3 pending dependents) / C (no header, 0 dependents, earliest path) order as A, B, C; with A absent, B beats C
