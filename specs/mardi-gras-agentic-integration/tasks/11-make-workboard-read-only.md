# Task 11: make Workboard a read-only overview

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: 08, 10
Priority: P0
Budget: 40 turns
Spec: ../SPEC.md (requirement R19)
Touch: .claude/skills/workboard/SKILL.md, .claude/skills/workboard/reference.md, agent-console/agent-console.py, agent-console/README.md, agent-console/tests/, .claude-plugin/plugin.json, .codex-plugin/plugin.json, specs/mardi-gras-agentic-integration/WORKBOARD-CUTOVER-BASE, specs/mardi-gras-agentic-integration/tests/workboard-cutover.sh, tests/test_workboard_cutover.py, tests/test_plugin_manifest_versions.py, tests/inventory/mardi-gras-11-workboard.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-11-workboard.json

## Goal

Keep Workboard's distinct machine-wide repository/session/cost overview while
removing it as a competing execution surface after production parity exists.
Before that production gate, the current behavior remains intact; afterward,
repository-scoped control routes explicitly to `agentic live`.

## Touch

Do not delete the scanner, historical research, cost panel, or cross-repo
views. Cutover detection consumes only `agentic live --cutover-status --json`;
the exact receipt must match the current released provider, package, runtimes,
façade canaries, and terminal parity evidence. A patch-only, absent, malformed,
or stale receipt preserves all existing behavior.

## Steps

1. Before any edit, record the exact task-base commit in
   `WORKBOARD-CUTOVER-BASE`, then write the failing before/after cutover route
   and skill fixtures, including a root canonical wrapper.
2. Add a bounded read-only receipt-status check whose failure preserves
   the existing Workboard behavior.
3. After readiness, suppress browser dispatch, priority, status, resume,
   verify, and stop controls and reject the corresponding mutation endpoints,
   while retaining cross-repo inventory, sessions, cost, and repo drill-down.
4. Add per-repository `agentic live` migration commands and distinguish
   machine-wide read-only requests from repository-scoped interactive ones in
   skill guidance.
5. Update every affected agent-console action/endpoint test for pre-receipt
   retention and post-receipt rejection.
6. Bump and synchronize the Claude and Codex plugin versions relative to the
   recorded task-base commit. Validate Antigravity's intentionally
   unversioned three-key manifest unchanged; add unique inventory fragments
   and keep historical implementation surfaces explicitly classified.

## Acceptance

- [ ] `bash specs/mardi-gras-agentic-integration/tests/workboard-cutover.sh` → controls remain before the released-provider/check/canary/parity gate, then disappear with mutation endpoints disabled while inventory/session/cost content and repo navigation remain (L3).
- [ ] `python3 -m pytest tests/test_workboard_cutover.py -q` → the canonical hermetic route/endpoint fixture enforces the same before/after boundary without a real installed provider (L3).
- [ ] `bash agent-console/scripts/check.sh` → the agent-console skills, cost, parser, and render surfaces remain green (L3).
- [ ] `python3 -m pytest tests/test_plugin_manifest_versions.py -q && bash tests/test_codex_skill_entrypoints.sh` → Claude and Codex carry the same valid bumped version, while Antigravity retains its required unversioned shape and every shared entrypoint remains valid (L2).
- [ ] `base="$(cat specs/mardi-gras-agentic-integration/WORKBOARD-CUTOVER-BASE)" && git cat-file -e "$base^{commit}" && ! git diff --quiet "$base" -- .claude-plugin/plugin.json .codex-plugin/plugin.json` → both versioned manifests changed from the explicit task-base commit, independent of task commit count (L1).
  Depth ceiling: Git can prove the manifest versions changed, while the behavioral complement is the package lifecycle suite plus runtime-specific manifest validation in the preceding criterion.
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json` → the measured Workboard surface and new cutover test are validly classified without unapproved deletion (L2).
- [ ] `bash scripts/check.sh` → the complete toolkit gate passes after legacy control cutover (L3).
