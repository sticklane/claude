Status: done
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

- [x] `grep -c "drain's own group mode" .claude/skills/drain/SKILL.md` → 0
- [x] `grep -c "rolling-window" .claude/skills/drain/SKILL.md` → ≥ 1 in the push-guard parenthetical's vicinity

Evidence: verifier PASS (specs/drain-rolling-window/evidence/07-fix-stale-group-mode-reference.md) — AC1 grep → 0; AC2 line 249 now reads "drain's own rolling-window merges follow it" in the push-guard parenthetical; single-line diff, no scope creep.

## Discovered

- The antigravity mirror `antigravity/.agents/workflows/drain.md` (lines 237-238) carries the identical stale "drain's own group mode follows it" text in its push-guard paragraph, outside this task's Touch scope — see specs/drain-rolling-window/tasks/12-fix-stale-group-mode-antigravity-drain-workflow.md
