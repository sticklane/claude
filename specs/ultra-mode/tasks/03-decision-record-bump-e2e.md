# Task 03: Orchestration decision record, version bump, e2e panel check

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: done
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

- [x] `test -f docs/decisions/orchestration.md` → exit 0; names both non-adoptions and links docs/orchestration-research-2026-07.md
      — doc present; names "No auto-ultra heuristics" and "single-call rubric judge instead" of multi-judge voting under `## Deliberate non-adoptions`, each with a research citation; links docs/orchestration-research-2026-07.md (3 refs) + SPEC.md.
- [x] `git diff HEAD~1 -- .claude-plugin/plugin.json` in the implementing commit shows a version bump; `claude plugin validate .` → exit 0
      — version 0.7.3 → 0.7.4 in the implementing commit; `claude plugin validate .` → `✔ Validation passed`, exit 0.
- [x] Closed-gate e2e recorded in specs/ultra-mode/evidence/: /critique in a no-runtimes fixture runs the single-critic path with no ultra mention
      — evidence/03-closed-gate-e2e.md: harness (03-closed-gate-harness.sh, exit 0, 6/6 asserts) proves the ultra path unreachable in a no-runtimes install; a live single `critic` run found both real plants (R1/R2 contradiction, un-runnable "feels fast" check), verdict NOT READY, zero "ultra" mentions.
- [x] Open-gate panel e2e recorded, or explicitly marked manual-pending with the reason
      — marked MANUAL-PENDING in evidence/03-closed-gate-e2e.md: Workflow (ultracode) tool unavailable to the unattended worker; the orchestrator runs the open-gate panel probe post-merge.
