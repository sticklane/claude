# Task 04: instrument the native façades

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: 01, 03, specs/toolkit-core-simplification/tasks/07-validate-native-orchestration-contract.md
Priority: P0
Budget: 44 turns
Spec: ../SPEC.md (requirements R5, R9, R11, R15, R17)
Touch: .claude/skills/work/SKILL.md, .claude/skills/build/SKILL.md, .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, .claude/skills/drain/dispatch-worker.sh, .claude/agents/implementation-worker.md, .claude/agents/verifier.md, .claude/agents/critic.md, runtimes/claude-code.md, runtimes/codex.md, runtimes/antigravity.md, tests/test_agentic_facade_conformance.sh, tests/test_codex_skill_entrypoints.sh, specs/mardi-gras-agentic-integration/tests/runtime-facade-canary.sh, specs/mardi-gras-agentic-integration/facade-canary-report.schema.json, tests/inventory/mardi-gras-04-facades.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-04-facades.json

## Goal

Make `/work`, `/build`, and `/drain` use the strengthened claim boundary and
emit the version-2 event history through their existing native orchestrators.
This task replaces and absorbs toolkit-core task 08, including its full
runtime conformance obligations.

## Touch

Do not add a common orchestration loop, duplicate the event substrate, or move
work ownership into events. Task 03 owns event schema/storage; this task only
emits through that API.

## Steps

1. Write failing façade conformance fixtures first, preserving the
   native-orchestration trace contract from the cross-spec prerequisite.
2. Migrate top-level work/build/drain claims to Task 01 outcomes and propagate
   the canonical run ID through workers, reviewers, gates, closure, and
   cleanup.
3. Define the fixed drain envelope and update every authorized orphan/requeue
   path to clear the assignee only after its existing liveness and dirty
   worktree safeguards pass.
4. Emit version-2 events through Task 03's API, recording
   dispatch/PID/start correlation only from the validated supervisor
   environment and never using it for authorization.
5. Align runtime profiles and compact worker contracts, regenerate/validate
   shared entrypoints, add unique inventory fragments, and provide the native
   canary driver that Tasks 07 and 12 will run against installed packages.
   Its report update is lock-plus-temp-rename atomic, accumulates entries by
   runtime/workflow under one package hash, rejects mixed packages, and marks
   complete only for the exact supported matrix.

## Acceptance

- [ ] `bash tests/test_agentic_facade_conformance.sh work build drain` → every runtime façade produces the normalized claim/work/review/gate/close/cleanup trace, stops on a lost claim, verifies drain preclaims, and clears assignees during authorized orphan recovery (L3).
- [ ] `bash tests/test_codex_skill_entrypoints.sh` → generated entrypoints remain current and runtime-native collaboration contracts remain discoverable (L2).
- [ ] `bash specs/mardi-gras-agentic-integration/tests/runtime-facade-canary.sh --self-test` → hermetic native-manager fixtures prove the driver requires claim, work, independent review, one gate, close, cleanup, runtime identity, and package identity; three invocations atomically accumulate the exact matrix, while mixed-package and interrupted merges never produce a complete report (L3).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json` → changed and new façade surfaces are validly classified without editing retained event tests (L2).
- [ ] `bash scripts/check.sh` → the repository gate remains green after native façade instrumentation (L3).
