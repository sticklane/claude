Status: draft
Discovered-from: specs/mirror-procedure-discipline/tasks/05-audit-factcheck.md
Spec: ../SPEC.md
Blocking: no

# Audit factcheck's reference.md mirror for procedural divergence

Task 05 audited `antigravity/.agents/skills/factcheck/SKILL.md` against its
source `.claude/skills/factcheck/SKILL.md` and found zero incidental
divergence, but `antigravity/.agents/skills/factcheck/reference.md` (the
worker-prompt template) was outside that task's Touch scope and was never
read side-by-side against the source `.claude/skills/factcheck/reference.md`.
Both files exist on both sides, so this is a real, unaudited mirror surface
this spec's task set otherwise doesn't cover.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
