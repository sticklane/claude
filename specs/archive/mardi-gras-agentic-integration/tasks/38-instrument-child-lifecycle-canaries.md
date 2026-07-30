# Task 38: instrument child lifecycle and native façade canaries

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status is always the frozen initial display value `pending`; workers and orchestrators update bd, never this line. -->
<!-- Task definitions are immutable after registration. Workers report progress, decisions, and deferred questions to the orchestrator; they do not rewrite task files. -->

Status: pending
Depends on: 01, 14, 16, 17, 37
Priority: P0
Budget: 44 turns
Spec: ../SPEC.md (requirements R5, R10, R11, R12, R15, R17)
Touch: .claude/skills/work/SKILL.md, .claude/skills/build/SKILL.md, .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, .claude/skills/drain/dispatch-worker.sh, .claude/agents/implementation-worker.md, .claude/agents/verifier.md, .claude/agents/critic.md, runtimes/claude-code.md, runtimes/codex.md, runtimes/antigravity.md, skills/work/SKILL.md, skills/build/SKILL.md, skills/drain/SKILL.md, tests/test_agentic_facade_conformance.sh, tests/test_agentic_child_activity.py, tests/test_codex_skill_entrypoints.sh, specs/mardi-gras-agentic-integration/tests/run-native-facade-matrix.sh, specs/mardi-gras-agentic-integration/facade-canary-report.schema.json, tests/inventory/mardi-gras-38-child-canaries.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-38-child-canaries.json

## Goal

Instrument Claude Workflow, Codex collaboration, and Antigravity native
orchestration with Task 16's queued, started, and exactly-one-terminal child
events after Task 17's claim migration. Provide the hermetic native façade
matrix and closed report schema that bind those traces to one verified
package identity pair and exact runtime fingerprints.

## Touch

This task owns native child lifecycle emission, the affected compact
agent/skill/runtime contracts, generated entrypoint conformance, and the
façade matrix driver/report. It consumes Task 17's claim and requeue behavior
without changing it, grants events no authorization, reads no transcript or
arbitrary output tail, and adds no scheduler or runtime capability registry.
Skill and conformance-test overlap with Task 17 is intentional: dependency
ordering plus isolated-worktree execution and deterministic landing preserve
both changes.

## Steps

1. Write failing per-runtime queued/started/terminal, dispatch-correlation,
   crash-to-unknown, duplicate-terminal, event-failure, and report-merge
   fixtures first.
2. Emit queued before native child dispatch, started only after the runtime
   accepts the child, and exactly one completed or failed event after
   collection. UI-started root runs copy only validated supervisor fields;
   direct runs omit them.
3. Keep worker, verifier, critic, and runtime-profile contracts compact while
   propagating canonical root run, parent, agent, worktree, branch, timing,
   role, and bounded typed outcome fields through every supported runtime.
4. Implement the atomic native façade report merge: bind one R7 package
   identity pair, require one fingerprint per runtime, reset only a changed
   runtime, reject cross-package input, and mark complete only for Claude and
   Codex work/build/drain plus Antigravity work/build and unsupported-mode
   pre-spawn checks.
5. Regenerate affected portable entrypoints and add the child/canary
   inventory fragments without modifying fleet or Task 16's event store.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_child_activity.py -q` → all native runtimes emit ordered queued/started/exactly-one-terminal records, event failures remain advisory, crashed indeterminate children become unknown, and no transcript-derived data enters a record (L3).
- [ ] `bash tests/test_agentic_facade_conformance.sh work build drain` → the post-Task-17 façades preserve claim/requeue behavior and add the normalized child lifecycle around native isolation, review, one gate, close, and cleanup (L3).
- [ ] `bash specs/mardi-gras-agentic-integration/tests/run-native-facade-matrix.sh --self-test` → hermetic native-manager fixtures prove package/fingerprint binding, exact matrix accumulation, unsupported Antigravity rejection, atomic per-runtime reset, and interrupted-merge recovery (L3).
- [ ] `bash tests/test_codex_skill_entrypoints.sh` → affected shared-skill entrypoints are current and runtime-native orchestration remains discoverable (L2).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json && bash scripts/check.sh` → child/canary surfaces are classified and the complete repository gate passes (L3).
