# Task 27: certify the production cutover

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status is always the frozen initial display value `pending`; workers and orchestrators update bd, never this line. -->
<!-- Task definitions are immutable after registration. Workers report progress, decisions, and deferred questions to the orchestrator; they do not rewrite task files. -->

Status: pending
Depends on: 01, 21, 22, 24, 25, 26, 37
Priority: P0
Budget: 24 turns
Spec: ../SPEC.md (requirements R1, R15, R18, R19, R21)
Touch: HUMAN.md, specs/mardi-gras-agentic-integration/TERMINAL-PARITY-REPORT.json, specs/mardi-gras-agentic-integration/PRODUCTION-CUTOVER-EVIDENCE.json

## Goal

MANUAL-PENDING: after trusted upstream Beads and Mardi Gras releases exist,
install their exact allowlisted artifacts, rerun the released terminal
journey, and record the production cutover receipt against Task 26's final
façade report and Task 25's immutable package. This external-state task may
make Workboard controls read-only only when every current binary, runtime,
package, report, and protocol identity still matches.

## Touch

This task may not publish either upstream project, populate or weaken an
allowlist without an immutable upstream artifact and checksum manifest,
change Workboard or fleet, rerun implementation against a patched provider,
or edit the final package. If a missing trusted release requires an allowlist
or package refresh, record that as a new dependent immutable task and wire the
refresh plus recertification before this task rather than changing this
registered work scope.

## Steps

1. MANUAL-PENDING until both installed artifacts exactly match existing R21
   and R18 trusted-release entries. Verify Task 27's committed HUMAN blocker,
   the final Task 25 package identity pair, and Task 26's complete report.
2. Install the trusted released Beads and Mardi Gras artifacts, explicitly run
   `agentic bd-authority install --repo <physical-repo> --confirmed`, and
   require `agentic live --check --json` to pass every authority, provider,
   package, runtime, and protocol check without mutation.
3. Run Task 22's identical terminal journey with the absolute released Mardi
   Gras binary and atomically write canonical terminal-parity evidence.
4. Call Task 20's sole mutating `--record-cutover` command with the Task 26
   façade report and new terminal report, then require read-only cutover
   status to remain ready under fresh binary and package fingerprinting.
5. Run Task 24's installed cutover journey to prove Workboard keeps both
   machine-wide inventory/session/cost views, rejects former controls, and
   preserves fleet.
6. Write only bounded receipt identities and command verdicts to
   `PRODUCTION-CUTOVER-EVIDENCE.json`; in the same evidence commit remove only
   Task 27's exact HUMAN line.

## Acceptance

- [ ] `MANUAL_PENDING=1 agentic bd-authority install --repo "$PWD" --confirmed --json && agentic live --check --json | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["beads"]["released"] is True and d["provider"]["released"] is True and d["package"]["manifest_hash"] and d["package"]["execution_environment_hash"]'` → the exact allowlisted Beads/Mardi Gras artifacts and final immutable package pass the explicit production authority and read-only live checks (L3; manual-pending on trusted releases and administrative installation).
- [ ] `MARDI_GRAS_BINARY="$(command -v mg)" MANUAL_PENDING=1 bash specs/mardi-gras-agentic-integration/tests/e2e-provider-pty.sh --released --report specs/mardi-gras-agentic-integration/TERMINAL-PARITY-REPORT.json` → the complete Task 22 journey runs against the trusted released binary and records exact artifact, protocol, package, and journey identities (L3; manual-pending on the released binary).
- [ ] `agentic live --record-cutover --facade-report specs/mardi-gras-agentic-integration/FACADE-CANARY-REPORT.json --terminal-report specs/mardi-gras-agentic-integration/TERMINAL-PARITY-REPORT.json --json && agentic live --cutover-status --json | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["ready"] is True'` → the exact production receipt is recorded once and remains ready under fresh identity checks (L3).
- [ ] `bash specs/mardi-gras-agentic-integration/tests/workboard-cutover.sh --installed` → the certified installation keeps Workboard inventory/session/cost views and fleet routing while rejecting all legacy browser controls (L3).
- [ ] `python3 specs/mardi-gras-agentic-integration/tests/validate-manual-certification.py --task 27 --commit HEAD --facade-report specs/mardi-gras-agentic-integration/FACADE-CANARY-REPORT.json --terminal-report specs/mardi-gras-agentic-integration/TERMINAL-PARITY-REPORT.json --production-evidence specs/mardi-gras-agentic-integration/PRODUCTION-CUTOVER-EVIDENCE.json` → the evidence commit changes only terminal/final evidence plus HUMAN.md, deletes exactly Task 27's attested line in that same commit, preserves every other HUMAN byte, and binds every trusted binary, package, runtime, façade, terminal, receipt, and fresh cutover-status identity/hash (L3).

Depth ceiling: upstream publication and authenticated administrative
installation are external state; the manual-pending allowlisted-binary,
terminal, receipt, and installed-Workboard journeys are the behavioral
evidence and patch-only artifacts remain blocked.
