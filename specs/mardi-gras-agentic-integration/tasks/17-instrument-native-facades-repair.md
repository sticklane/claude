# Task 17: migrate native façade claims and requeue paths

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status is always the frozen initial display value `pending`; workers and orchestrators update bd, never this line. -->
<!-- Task definitions are immutable after registration. Workers report progress, decisions, and deferred questions to the orchestrator; they do not rewrite task files. -->

Status: pending
Depends on: 01, 14, 16, 37, specs/toolkit-core-simplification/tasks/03-remove-live-task-authority-contradictions.md, specs/toolkit-core-simplification/tasks/04-retire-dead-live-surfaces.md, specs/toolkit-core-simplification/tasks/07-validate-native-orchestration-contract.md
Priority: P0
Budget: 34 turns
Spec: ../SPEC.md (requirements R9, R17)
Touch: .claude/skills/work/SKILL.md, .claude/skills/build/SKILL.md, .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, .claude/skills/drain/dispatch-worker.sh, .claude/skills/handoff/SKILL.md, .claude/skills/resume-handoff/SKILL.md, skills/work/SKILL.md, skills/build/SKILL.md, skills/drain/SKILL.md, skills/handoff/SKILL.md, skills/resume-handoff/SKILL.md, tests/test_agentic_facade_conformance.sh, tests/inventory/mardi-gras-17-facades.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-17-facades.json

## Goal

Make installed `/work`, top-level `/build`, and `/drain` use Task 01's
session-safe claim boundary and stop before task-prose loading, worker
dispatch, or edits on every lost claim. Every toolkit-owned requeue path,
including handoff recovery, uses Task 00D's conditional adapter to clear the
assignee before removing markers.

## Touch

This historical replacement owns only claim, drain-envelope, and
revision-conditional requeue migration across the installed façades. It may
update generated entrypoints for the touched skills, but it must not add child
lifecycle instrumentation, edit `.claude/agents` or runtime profiles, own the
native façade matrix/report, add a shared scheduler, change Task 01's claim
implementation, or edit `fleet`. Task 38 may later overlap the same skills in
isolated worktrees; deterministic integration serializes their landing.

## Steps

1. Write the failing cross-runtime claim-loss, drain-envelope, orphan, and
   requeue fixtures first, preserving the validated native-orchestration trace
   contract from the cross-spec prerequisites.
2. Route top-level work/build/drain through the exact R9 claim forms, propagate
   the canonical run ID through dispatch, review, gate, close, and cleanup,
   and stop before task-prose loading or edits on every lost claim.
3. Consume the fixed drain envelope for worker verification and update every
   toolkit-owned orphan/requeue surface to retain its liveness and dirty-tree
   guards, perform the revision-conditional reopen plus assignee clear, prove
   post-state/history, and only then remove claim or inflight markers.
4. Regenerate the touched portable entrypoints and add the replacement
   inventory fragment without changing event, agent, runtime-profile, or
   canary ownership.

## Acceptance

- [ ] `bash tests/test_agentic_facade_conformance.sh claim requeue` → installed work/build/drain use the exact R9 claim boundary, verify drain preclaims, stop before dispatch on loss, and conditionally clear assignees before marker cleanup on every owned requeue surface (L3).
- [ ] `python3 -m pytest tests/test_agentic_claim_races.py -q -k 'facade or drain_envelope or requeue or orphan'` → direct, UI, drain, raw-claim, crash, and foreign-cursor fixtures preserve the winning Beads authority and never detach code work from its run (L3).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json && bash scripts/check.sh` → the narrowed claim/requeue façade surfaces are classified and the repository gate passes (L3).
