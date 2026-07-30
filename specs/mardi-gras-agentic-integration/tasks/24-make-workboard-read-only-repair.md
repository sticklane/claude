# Task 24: make Workboard read-only while preserving fleet

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status is always the frozen initial display value `pending`; workers and orchestrators update bd, never this line. -->
<!-- Task definitions are immutable after registration. Workers report progress, decisions, and deferred questions to the orchestrator; they do not rewrite task files. -->

Status: pending
Depends on: 01, 20, 22, 23, 37
Priority: P0
Budget: 44 turns
Spec: ../SPEC.md (requirements R16, R19)
Touch: .claude/skills/workboard/SKILL.md, .claude/skills/workboard/reference.md, skills/workboard/SKILL.md, agent-console/agent-console.py, agent-console/README.md, agent-console/tests/test_dispatch_runtime.py, agent-console/tests/test_parsers.py, agent-console/tests/test_resume_agent.py, agent-console/tests/test_workboard_cutover.py, .claude-plugin/plugin.json, .codex-plugin/plugin.json, specs/mardi-gras-agentic-integration/WORKBOARD-CUTOVER-BASE, specs/mardi-gras-agentic-integration/tests/workboard-cutover.sh, tests/test_workboard_cutover.py, tests/test_plugin_manifest_versions.py, tests/inventory/mardi-gras-24-workboard.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-24-workboard.json

## Goal

Keep both Workboard routes as live machine-wide repository, session, and cost
views while removing their mutation and dispatch controls only when Task 20's
read-only cutover status reports the exact installed receipt ready.
Repository-scoped interactive requests route to `agentic live`; `fleet`
remains byte-present and keeps its separate session-local native-agent routing
in every cutover state.

## Touch

The implementation seam is `agent-console.Handler.do_GET`,
`agent-console._adapt_board`, `agent-console.render_workboard`, the kanban
renderer, their action registry/endpoints, and Workboard skill guidance. Do
not delete scanners, historical research, session/cost/skills views, repo
drill-down, either fleet skill file, fleet marketplace wording, or fleet
routing claims. A missing, malformed, patch-only, or stale receipt must
preserve current controls; isolated worktrees may overlap these files with
earlier tasks, and R20's deterministic landing resolves the integrated diff.

## Steps

1. Record the exact task-base commit in `WORKBOARD-CUTOVER-BASE`, snapshot the
   canonical and generated fleet skill bytes plus plugin/marketplace fleet
   promises, and write failing pre-receipt, ready-receipt, stale-receipt,
   route, endpoint, and fleet-preservation fixtures first.
2. Add one bounded read-only `agentic live --cutover-status --json` check.
   Every error or non-ready result retains existing Workboard behavior and
   performs no receipt repair.
3. On exact readiness, remove dispatch, priority, status, resume, verify, and
   stop actions from both Workboard renderers and reject the corresponding
   mutation endpoints while preserving cross-repository inventory, sessions,
   costs, repo navigation, and historical views.
4. Add bounded per-repository `agentic live` migration commands and update the
   Workboard skill to distinguish machine-wide read-only inventory from
   repository-scoped interactive control.
5. Regenerate only the Workboard entrypoint, update all affected
   agent-console tests, and prove the fleet snapshots and routes are
   byte-identical and still reachable.
6. Bump and synchronize the Claude and Codex plugin versions relative to the
   recorded task base; leave the intentionally unversioned Antigravity
   manifest and fleet marketplace promises unchanged.

## Acceptance

- [ ] `bash specs/mardi-gras-agentic-integration/tests/workboard-cutover.sh` → controls remain for absent, malformed, patch-only, stale-package, stale-build, and stale-runtime receipts; exact readiness removes only controls while both routes retain inventory/session/cost content, repo navigation, and bounded `agentic live` commands (L3).
- [ ] `python3 -m pytest tests/test_workboard_cutover.py agent-console/tests/test_workboard_cutover.py -q` → hermetic route/action/endpoint fixtures enforce the same before/after boundary and prove the canonical/generated fleet bytes and routing promises never change (L3).
- [ ] `bash agent-console/scripts/check.sh` → Workboard, kanban, scanner, skills, cost, session, parser, and render surfaces remain green (L3).
- [ ] `python3 -m pytest tests/test_plugin_manifest_versions.py -q && bash tests/test_codex_skill_entrypoints.sh` → Claude and Codex versions are synchronized and bumped from the recorded base, Antigravity keeps its three-key form, the Workboard entrypoint is current, and fleet remains present in plugin/marketplace routing (L2).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json && bash scripts/check.sh` → retained Workboard/fleet surfaces and the read-only cutover are classified and the full gate passes (L3).
