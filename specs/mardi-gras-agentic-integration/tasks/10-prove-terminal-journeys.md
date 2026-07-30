# Task 10: prove terminal journeys and document the cutover

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: 06, 09
Priority: P0
Budget: 38 turns
Spec: ../SPEC.md (requirements R1 through R18)
Touch: specs/mardi-gras-agentic-integration/tests/e2e-provider-pty.sh, specs/mardi-gras-agentic-integration/tests/fixtures/fake-runtime, specs/mardi-gras-agentic-integration/terminal-parity-report.schema.json, tests/test_agentic_live_terminal.py, docs/guides/agentic-live.md, README.md, tests/inventory/mardi-gras-10-terminal.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-10-terminal.json

## Goal

Prove the complete repository-scoped developer journey in real pseudo-terminals
and tmux, including live redraw, drill-down, safe launch, claim collisions,
drain confirmation, crashes, and dashboard return. Publish the supported
install, runtime, recovery, confidence, and uninstall experience without
claiming an upstream release exists.

## Touch

By default the E2E fixture uses the pinned provider helper and a deterministic
fake runtime. With an explicit absolute `MARDI_GRAS_BINARY`, it verifies the
released handshake and runs the identical journey without applying the patch.
Neither mode depends on the developer's real home, tracker, or runtime
credentials.

## Steps

1. Write the pseudo-terminal and tmux journey against an isolated repository,
   home, dispatch store, runtime, and patched Mardi Gras binary by default.
2. Exercise browsing/detail, issue launch, explicit drain cancellation and
   confirmation, UI/direct/drain/raw claim races, activity degradation,
   runtime failure, tmux switching, foreground handoff, dashboard crash, and
   return.
3. Assert alternate-screen redraw is bounded and produces no scrollback
   growth across repeated refreshes.
4. Add a released-binary override that requires an absolute executable,
   validates the R14 handshake, bypasses the pinned checkout helper, and then
   runs the same journey. Define `--released --report <path>` to atomically
   write validated `agentic.terminal-parity/v1` evidence and cover the exact
   grammar, report, and failure paths in the hermetic canonical contract.
5. Document install/check, control ownership, direct skill use, evidence
   confidence, recovery, runtime limits, upgrades, uninstall, and the
   unreleased-provider gate.
6. Add unique inventory fragments for the terminal fixture and guide.

## Acceptance

- [ ] `bash specs/mardi-gras-agentic-integration/tests/e2e-provider-pty.sh` → the pinned provider and fake runtimes complete every named terminal journey with bounded redraw and no scrollback growth (L3).
- [ ] `python3 -m pytest tests/test_agentic_live_terminal.py -q` → the canonical hermetic PTY fixture proves alternate-screen restoration, bounded refresh output, foreground return, dashboard-exit behavior, pinned-default selection, exact `MARDI_GRAS_BINARY ... --released --report` override, atomic validated report generation, and rejection of missing/malformed release inputs without network or runtime credentials (L3).
- [ ] `python3 -m pytest tests/test_agentic_claim_races.py tests/test_agentic_activity.py tests/test_agentic_launch.py tests/test_agentic_live.py -q` → the cross-module safety contract remains green as one suite (L3).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json && bash scripts/check.sh` → inventory and the full toolkit gate pass (L3).
