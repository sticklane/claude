# Task 03: Orchestration decision record, version bump, e2e panel check

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: in-progress
Depends on: 01, 02, ../../orchestrator-context/tasks/05-decisions-e2e-bump.md
Priority: P2
Budget: 35 turns
Spec: ../SPEC.md (requirements R7, R9-bump, end-to-end)
Touch: docs/decisions/orchestration.md, .claude-plugin/plugin.json, specs/ultra-mode/evidence/

## Goal

`docs/decisions/orchestration.md` captures the adopt/leave-model-driven
split, the effort tiers, the cost figures with their baseline ambiguity,
the single-agent default, both deliberate non-adoptions (no auto-ultra
heuristics; single-call rubric judge over multi-judge default) with
citations, and links the research doc + spec. plugin.json is bumped. The
spec's end-to-end critique-panel check is run where session conditions
permit and its outcome recorded as evidence.

## Steps

1. Write the decision record per R7.
2. Bump plugin.json minor version; `claude plugin validate .`.
3. End-to-end: if the executing session can activate ultracode (the
   Workflow tool's opt-in), run /critique against a fixture spec with the
   three plants (contradiction, un-runnable check, refutable bait) and
   record panel launch + both real plants found + refuted finding
   dropped; then run /critique in a fixture install without runtimes/ and
   record the single-critic path with no ultra mention. If the session
   cannot activate ultracode (unattended workers cannot opt in), record
   the closed-gate half only and leave the open-gate half as a marked
   manual item in this task file — do not fake it.

## Acceptance

- [ ] `test -f docs/decisions/orchestration.md` → exit 0; names both non-adoptions and links docs/orchestration-research-2026-07.md
- [ ] `git diff HEAD~1 -- .claude-plugin/plugin.json` in the implementing commit shows a version bump; `claude plugin validate .` → exit 0
- [ ] Closed-gate e2e recorded in specs/ultra-mode/evidence/: /critique in a no-runtimes fixture runs the single-critic path with no ultra mention
- [ ] Open-gate panel e2e recorded, or explicitly marked manual-pending with the reason
