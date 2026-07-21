Status: draft
Discovered-from: specs/ctx-dispatch-adoption/tasks/02-breakdown-structure-gathering.md
Spec: ../SPEC.md
Blocking: no

# antigravity/.agents/skills/breakdown/SKILL.md still reads scout-only after task 02

Task 02 rewrote `.claude/skills/breakdown/SKILL.md` step 2 to gather
structure via `ctx tree`/`ctx sig`/`ctx refs` before scouts, and mirrored
it into `antigravity/.agents/workflows/breakdown.md` (the workflow
delegator, task 02's Touch). `antigravity/.agents/skills/breakdown/SKILL.md`
— the skill the workflow delegates to — was out of task 02's Touch and
still reads scout-only ("use the scout skill"), leaving an internal
antigravity procedural inconsistency: the workflow says ctx-first, the
skill it delegates to says scout-only.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
