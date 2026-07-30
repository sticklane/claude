# Task 22: prove the terminal journeys

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status is always the frozen initial display value `pending`; workers and orchestrators update bd, never this line. -->
<!-- Task definitions are immutable after registration. Workers report progress, decisions, and deferred questions to the orchestrator; they do not rewrite task files. -->

Status: pending
Depends on: 01, 21, 39, 37
Priority: P0
Budget: 42 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R17, R18)
Touch: specs/mardi-gras-agentic-integration/tests/e2e-provider-pty.sh, specs/mardi-gras-agentic-integration/tests/fixtures/fake-runtime, specs/mardi-gras-agentic-integration/terminal-parity-report.schema.json, agentic/schema/public-json-surfaces-v1.json, tests/test_agentic_live_terminal.py, tests/test_agentic_claim_races.py, tests/test_agentic_activity.py, tests/test_agentic_launch.py, tests/test_agentic_live.py, tests/test_agentic_public_json_contract.py, tests/inventory/mardi-gras-22-terminal.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-22-terminal.json

## Goal

Prove the complete repository-scoped control and observation journey in real
pseudo-terminals and tmux using the pinned provider and deterministic fake
runtimes. The same harness exposes a strictly trusted released-binary mode for
Task 27, but this task neither fabricates that external release nor writes
product documentation.

## Touch

All fixtures use isolated repositories, account/state roots, package roots,
dispatch stores, trackers, runtimes, and tmux servers. The default path must
obtain the binary through Task 21's exact-base helper; released mode requires
an absolute allowlisted binary and canonical report destination, never a
locally patched or self-reported artifact.

## Steps

1. Write the failing PTY/tmux and hermetic Python fixtures first, including
   isolated process-start/boot, Beads, package, runtime, and provider state.
2. Exercise browsing and drill-down, issue launch, drain cancellation and
   confirmation, UI/direct/drain/raw claim races, direct-run appearance,
   source slowdown and stale retention, spawn/runtime failure, pane switching,
   foreground suspension/return, dashboard quit/crash, and restoration.
3. Assert repeated alternate-screen refresh is in-place and bounded, preserves
   selection/detail state, and adds no terminal scrollback.
4. Add `MARDI_GRAS_BINARY=<absolute> --released --report <path>` so it verifies
   exact Task 21 allowlist provenance and R14 handshake, bypasses the pinned
   patch helper, runs the identical journey, and atomically writes canonical
   `agentic.terminal-parity/v1` evidence.
5. Register every terminal-parity and journey-error leaf in the shared
   public-JSON inventory, run the cross-module race, activity, launch, live,
   and public JSON suites together, and add the new surfaces to the measured
   inventory.

## Acceptance

- [ ] `bash specs/mardi-gras-agentic-integration/tests/e2e-provider-pty.sh` → the pinned provider and fake runtimes complete every named terminal journey with bounded redraw, restored terminal state, and no scrollback growth (L3).
- [ ] `python3 -m pytest tests/test_agentic_live_terminal.py -q` → hermetic PTY/tmux fixtures prove foreground and dashboard recovery, pinned-default selection, exact released override/report grammar, atomic report writes, and pre-journey rejection of malformed or untrusted release inputs (L3).
- [ ] `python3 -m pytest tests/test_agentic_claim_races.py tests/test_agentic_activity.py tests/test_agentic_launch.py tests/test_agentic_live.py -q` → the terminal harness preserves the cross-module claim, correlation, prompt, package, and live-check safety contracts (L3).
- [ ] `python3 -m pytest tests/test_agentic_public_json_contract.py -q` → terminal parity evidence and every journey/error leaf are canonical, bounded, and registered (L2).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json && bash scripts/check.sh` → terminal surfaces are classified and the full toolkit gate passes (L3).
