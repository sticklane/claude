# Task 39: activate live with runtime canaries

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status is always the frozen initial display value `pending`; workers and orchestrators update bd, never this line. -->
<!-- Task definitions are immutable after registration. Workers report progress, decisions, and deferred questions to the orchestrator; they do not rewrite task files. -->

Status: pending
Depends on: 01, 14, 18, 19, 21, 37
Priority: P0
Budget: 40 turns
Spec: ../SPEC.md (requirements R1, R3, R6, R8, R12, R14, R15, R17, R18)
Touch: agentic/cli.py, agentic/live.py, agentic/runtime_canary.py, agentic/schema/live-check-v1.json, agentic/schema/runtime-canary-v1.json, agentic/schema/public-json-surfaces-v1.json, runtimes/parse_headless.py, runtimes/test_parse_headless.py, runtimes/claude-code.md, runtimes/codex.md, runtimes/antigravity.md, tests/test_agentic_live.py, tests/test_agentic_launch.py, tests/test_agentic_install_lifecycle.sh, tests/test_agentic_public_json_contract.py, specs/mardi-gras-agentic-integration/tests/install-lifecycle.sh, specs/mardi-gras-agentic-integration/tests/runtime-canary.sh, specs/mardi-gras-agentic-integration/tests/run-runtime-canary-matrix.sh, tests/inventory/mardi-gras-39-live-canaries.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-39-live-canaries.json

## Goal

Implement read-only `agentic live --check`, exact `agentic live` provider
launch, and the supported runtime/workflow canary matrix over Task 19's
installed records as verified by Task 14's package-current identity validator.
Every invocation freshly authorizes Beads, verifies the trusted Mardi Gras
handshake and current package, fingerprints the selected runtime, and fails
before spawn or mutation on any mismatch.

## Touch

This task owns live preflight/argv, provider and Beads authority handshakes,
runtime/workflow support selection, exact runtime binary fingerprint
comparison, and hermetic runtime-canary drivers/tests. It consumes Task 14's
identity/profile APIs and package-current validator, Task 18's activity
command, Task 19's installed package records, and trusted allowlists supplied
elsewhere. It must not reimplement package identity, construct, extract,
install, upgrade, uninstall, purge, or rewrite the package/runtime supply, and
it may not auto-install an authority schema or promote a patched provider.

## Steps

1. Write failing non-Beads, authority-profile, provider-handshake,
   `/usr/bin/mg`, package/plugin, supported-workflow, runtime-fingerprint,
   canary, exact-argv, and no-mutation fixtures first.
2. Implement `agentic live --check` with Task 00D's fresh authorizer ticket,
   Task 14's package-current verdict over Task 19's installed records, exact
   trusted Mardi Gras protocol/release evidence, tmux support, and Task 14's
   runtime/profile resolution; every failure remains read-only.
3. Implement `agentic live` as exactly the R14 absolute argv after the same
   checks pass, and reject unsupported Antigravity drain/resume before spawn.
4. Resolve and fingerprint each runtime immediately before the canary, invoke
   only that absolute binary, require packaged-skill preflight before Beads
   mutation, re-fingerprint afterward, and record the certified workflow
   matrix consumed by prepare and supervise.
5. Add the self-testing runtime-canary matrix, split live portions of the
   install lifecycle, and register every live, fingerprint, canary, and error
   envelope without changing package construction.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_live.py runtimes/test_parse_headless.py -q` → authority/provider/package preflight, supported workflow selection, exact live argv, `/usr/bin/mg` and patched-provider rejection, no-mutation failures, and runtime fingerprint drift pass (L3).
- [ ] `python3 -m pytest tests/test_agentic_launch.py -q -k 'RuntimeBinary or RuntimeCanary or PackageIdentity'` → prepare accepts only a complete matching canary, records the absolute executable/fingerprint, and supervise rejects every path, byte, version, OS, or architecture swap before spawn (L3).
- [ ] `bash specs/mardi-gras-agentic-integration/tests/run-runtime-canary-matrix.sh --self-test && bash specs/mardi-gras-agentic-integration/tests/install-lifecycle.sh --live-only` → hermetic runtime fixtures prove the full supported matrix reaches packaged-skill preflight, unsupported Antigravity modes fail before spawn, and live lifecycle checks never construct or mutate the package (L3).
- [ ] `python3 -m pytest tests/test_agentic_public_json_contract.py -q -k 'live or runtime_binary or canary'` → every live-check, handshake, fingerprint, canary, and error envelope is canonical and bounded (L2).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json && bash scripts/check.sh` → live/canary surfaces are classified and the complete repository gate passes (L3).
