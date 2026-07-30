# Task 12: certify the production cutover

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: 07, 11
Priority: P0
Budget: 20 turns
Spec: ../SPEC.md (requirements R15, R18, R19)
Touch: specs/mardi-gras-agentic-integration/FACADE-CANARY-REPORT.json, specs/mardi-gras-agentic-integration/TERMINAL-PARITY-REPORT.json, specs/mardi-gras-agentic-integration/PRODUCTION-CUTOVER-EVIDENCE.json

## Goal

After Mardi Gras publishes a compatible provider release, certify the exact
installed release, immutable package, native runtime façades, and terminal
journey, then record the receipt that makes Workboard controls read-only. This
is external-state release work; it must remain blocked rather than treating
the pinned development patch as production.

## Touch

This task may not publish Mardi Gras, fabricate a release, weaken receipt
validation, or modify Workboard code. Reports contain bounded versions,
digests, verdicts, and timestamps only—no prompts, transcripts, tokens, or
credentials.

## Steps

1. MANUAL-PENDING until an upstream release returns the exact R14 handshake.
   Reinstall the current Task 11 package, run the read-only live check, and
   require its package version/hash and released build commit before any
   report is accepted.
2. Run Task 04's exact native façade driver grammar against that installed package for
   Claude Code and Codex work/build/drain plus Antigravity work/build.
3. Run Task 10's complete terminal journey with its explicit released-binary
   override, not the pinned patch, and write the terminal report.
4. Call `agentic live --record-cutover` with both reports, then verify
   `--cutover-status` is ready and Workboard retains inventory/cost while
   rejecting every former control.
5. Record the bounded command results and receipt identities in
   `PRODUCTION-CUTOVER-EVIDENCE.json`.

## Acceptance

- [ ] `MANUAL_PENDING=1 bash bin/install-agentic-cli --source "$PWD" --json && agentic live --check --json | python3 -c 'import json,sys; data=json.load(sys.stdin); assert data["provider"]["released"] is True and data["package"]["manifest_hash"]'` → manual-pending until a compatible upstream release exists; then the exact post-Task-11 package is reinstalled and passes the released-provider read-only check (L3).
- [ ] `package_root="$(agentic package current --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["package_root"])')" && MANUAL_PENDING=1 bash specs/mardi-gras-agentic-integration/tests/runtime-facade-canary.sh --installed-package "$package_root" --runtime claude-code --workflows work,build,drain --report specs/mardi-gras-agentic-integration/FACADE-CANARY-REPORT.json && MANUAL_PENDING=1 bash specs/mardi-gras-agentic-integration/tests/runtime-facade-canary.sh --installed-package "$package_root" --runtime codex --workflows work,build,drain --report specs/mardi-gras-agentic-integration/FACADE-CANARY-REPORT.json && MANUAL_PENDING=1 bash specs/mardi-gras-agentic-integration/tests/runtime-facade-canary.sh --installed-package "$package_root" --runtime antigravity --workflows work,build --report specs/mardi-gras-agentic-integration/FACADE-CANARY-REPORT.json` → all supported native journeys bind the reinstalled package and Antigravity rejects unsupported modes (L3).
- [ ] `MARDI_GRAS_BINARY="$(command -v mg)" MANUAL_PENDING=1 bash specs/mardi-gras-agentic-integration/tests/e2e-provider-pty.sh --released --report specs/mardi-gras-agentic-integration/TERMINAL-PARITY-REPORT.json` → the same Task 10 journey runs against the installed released binary through its tested override and records the released build identity (L3).
- [ ] `agentic live --record-cutover --facade-report specs/mardi-gras-agentic-integration/FACADE-CANARY-REPORT.json --terminal-report specs/mardi-gras-agentic-integration/TERMINAL-PARITY-REPORT.json --json && agentic live --cutover-status --json | python3 -c 'import json,sys; data=json.load(sys.stdin); assert data["ready"] is True'` → the exact production receipt records and reads ready (L3).
- [ ] `bash specs/mardi-gras-agentic-integration/tests/workboard-cutover.sh --installed` → the certified installation keeps machine-wide inventory/session/cost views and rejects all legacy browser controls (L3).
  Depth ceiling: publication of the upstream release is external state this repository cannot create; the manual-pending released-binary journey is the behavioral evidence and patch-only builds must remain blocked.
