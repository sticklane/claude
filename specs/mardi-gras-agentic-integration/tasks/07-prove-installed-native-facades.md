# Task 07: prove the installed native façades

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: 06
Priority: P0
Budget: 22 turns
Spec: ../SPEC.md (requirements R9, R11, R15, R17)
Touch: specs/mardi-gras-agentic-integration/FACADE-CANARY-REPORT.json

## Goal

Run the native façade driver against the immutable installed package and
record full claim-through-cleanup evidence for every supported
runtime/workflow pair. This satisfies the absorbed toolkit-core façade
obligation without waiting for a Mardi Gras provider release.

## Touch

This is authenticated runtime evidence, not implementation. It may update only
the bounded report: no skill, package, tracker task, or runtime profile is
modified, and no unsupported Antigravity workflow is promoted.

## Steps

1. MANUAL-PENDING because real Claude Code, Codex, and Antigravity native
   managers and authenticated sessions are required.
2. Resolve the currently installed immutable package root and manifest hash
   with `agentic package current --json`, which does not require Mardi Gras.
3. Run the exact canary grammar once per supported runtime/workflow set,
   retaining isolated fixture repositories and bounded logs only on failure.
4. Validate and write one report binding package, runtime binary fingerprints,
   claim/work/review/gate/close/cleanup evidence, and unsupported-mode
   preflight failures.

## Acceptance

- [ ] `MANUAL_PENDING=1 bash specs/mardi-gras-agentic-integration/tests/runtime-facade-canary.sh --installed-package "$(agentic package current --json | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"package_root\"])')" --runtime claude-code --workflows work,build,drain --report specs/mardi-gras-agentic-integration/FACADE-CANARY-REPORT.json` → Claude Code completes every native façade stage against the installed package (L3).
- [ ] `MANUAL_PENDING=1 bash specs/mardi-gras-agentic-integration/tests/runtime-facade-canary.sh --installed-package "$(agentic package current --json | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"package_root\"])')" --runtime codex --workflows work,build,drain --report specs/mardi-gras-agentic-integration/FACADE-CANARY-REPORT.json` → Codex completes every native façade stage against the same package (L3).
- [ ] `MANUAL_PENDING=1 bash specs/mardi-gras-agentic-integration/tests/runtime-facade-canary.sh --installed-package "$(agentic package current --json | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"package_root\"])')" --runtime antigravity --workflows work,build --report specs/mardi-gras-agentic-integration/FACADE-CANARY-REPORT.json` → Antigravity completes supported stages and the report records drain/resume as rejected before spawn (L3).
- [ ] `python3 -c 'import json; data=json.load(open("specs/mardi-gras-agentic-integration/FACADE-CANARY-REPORT.json")); assert data["schema"] == "agentic.facade-canary/v1" and data["complete"] is True'` → the merged report is schema-tagged and complete (L2).
