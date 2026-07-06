Status: draft
Priority: P3
Discovered-from: specs/drain-rolling-window/tasks/05-ship-gates-and-mirrors.md
Spec: ../SPEC.md
Blocking: no

# Stale "group throughput mode" reference in antigravity breakdown/SKILL.md's Hand off section

`antigravity/.agents/skills/breakdown/SKILL.md`'s "Hand off" section still says "its group throughput mode hands you concurrent Agent Manager launches" — task 05 renamed that mode to the rolling window in `antigravity/.agents/workflows/drain.md`, so this cross-reference now points at terminology that no longer exists. One-line fix, left out of task 05's scope since it's a Hand off section detail, not the Group: grammar content task 05 owned.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
