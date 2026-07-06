Status: draft
Priority: P1
Discovered-from: specs/drain-sweep-preservation/tasks/03-worker-commits-and-bump.md
Spec: ../SPEC.md
Blocking: no

# Antigravity mirror of drain Worker prompt missing task 03's incremental-commit clause

The antigravity mirror of the drain Worker prompt (`antigravity/.agents/workflows/drain.md`, worker-prompt block ~lines 127-166) still says only "commit to task/NN-<slug>, do not push" and did not receive task 03's incremental-commit clause (commit at each completed TDD step, before spawning any verifier) — `antigravity/` was not in task 03's Touch list and its Goal/Steps described no mirror step, so the unattended worker could not edit it. Per CLAUDE.md's mirror convention this is a spec gap (the "unlisted mirror silently ships un-mirrored" failure mode). The antigravity file has no Headless-fallback section by design (no Workflow tool there), so only the Worker-prompt clause is the missing mirror.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
