Status: in-progress
Depends on: none
Priority: P3
Budget: 4 turns
Discovered-from: specs/drain-rolling-window/tasks/01-drain-rolling-window-scheduler.md
Spec: ../SPEC.md
Touch: .claude/skills/drain/SKILL.md
Blocking: no

# Stale "group mode" cross-reference in drain/SKILL.md's push-guard parenthetical

`.claude/skills/drain/SKILL.md`'s "## 3. Collect the verdict" push-guard parenthetical (line 249) still reads "drain's own group mode follows it" — task 01 replaced group-throughput mode with the rolling-window scheduler, so this cross-reference now points at a mechanism that no longer exists. Should read "drain's own rolling-window merges" (or equivalent). One-line fix, left out of task 01's Touch scope deliberately.

## Steps

1. In `.claude/skills/drain/SKILL.md`'s "## 3. Collect the verdict" push-guard parenthetical, replace "drain's own group mode follows it" with "drain's own rolling-window merges" (or equivalent wording naming the current mechanism).

## Acceptance

- [ ] `grep -c "drain's own group mode" .claude/skills/drain/SKILL.md` → 0
- [ ] `grep -c "rolling-window" .claude/skills/drain/SKILL.md` → ≥ 1 in the push-guard parenthetical's vicinity
