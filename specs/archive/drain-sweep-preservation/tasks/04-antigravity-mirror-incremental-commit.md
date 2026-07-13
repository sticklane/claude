Status: done
Priority: P1
Touch: antigravity/.agents/workflows/drain.md
Discovered-from: specs/drain-sweep-preservation/tasks/03-worker-commits-and-bump.md
Spec: ../SPEC.md
Blocking: no

# Antigravity mirror of drain Worker prompt missing task 03's incremental-commit clause

The antigravity mirror of the drain Worker prompt (`antigravity/.agents/workflows/drain.md`, worker-prompt block ~lines 127-166) still says only "commit to task/NN-<slug>, do not push" and did not receive task 03's incremental-commit clause (commit at each completed TDD step, before spawning any verifier) — `antigravity/` was not in task 03's Touch list and its Goal/Steps described no mirror step, so the unattended worker could not edit it. Per CLAUDE.md's mirror convention this is a spec gap (the "unlisted mirror silently ships un-mirrored" failure mode). The antigravity file has no Headless-fallback section by design (no Workflow tool there), so only the Worker-prompt clause is the missing mirror.

Decision (2026-07-06): yes — mirror the incremental-commit guidance from the drain Worker prompt (`.claude/skills/drain/reference.md`, "commit ... at each completed TDD step (test → feat → refactor) ... before spawning any verifier") into the antigravity drain workflow's worker-prompt block. `antigravity/` is now listed in this task's Touch header.

## Acceptance

- [x] `grep -q 'each completed TDD step' antigravity/.agents/workflows/drain.md` → exits 0 (incremental-commit clause mirrored; currently absent)
  - Evidence: grep exits 0; clause added inside the worker-prompt blockquote after "task/NN-<slug>, do not push", mirroring `.claude/skills/drain/reference.md`'s incremental-commit paragraph. Verifier report: specs/drain-sweep-preservation/evidence/04-antigravity-mirror-incremental-commit.md
