Status: draft
Priority: P3
Discovered-from: specs/drain-rolling-window/tasks/01-drain-rolling-window-scheduler.md
Spec: ../SPEC.md
Blocking: no

# Stale "group mode" cross-reference in drain/SKILL.md's push-guard parenthetical

`.claude/skills/drain/SKILL.md`'s "## 3. Collect the verdict" push-guard parenthetical (line 249) still reads "drain's own group mode follows it" — task 01 replaced group-throughput mode with the rolling-window scheduler, so this cross-reference now points at a mechanism that no longer exists. Should read "drain's own rolling-window merges" (or equivalent). One-line fix, left out of task 01's Touch scope deliberately.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
