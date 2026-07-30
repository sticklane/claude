# Task 06: package and launch the live surface

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: 05
Priority: P0
Budget: 42 turns
Spec: ../SPEC.md (requirements R1, R6, R7, R14, R15, R16)
Touch: agentic/cli.py, agentic/live.py, agentic/package.py, agentic/runtime.py, bin/agentic, bin/install-agentic-cli, bin/uninstall-agentic-cli, runtimes/parse_headless.py, runtimes/test_parse_headless.py, runtimes/claude-code.md, runtimes/codex.md, runtimes/antigravity.md, tests/test_agentic_live.py, tests/test_agentic_install_lifecycle.sh, specs/mardi-gras-agentic-integration/tests/install-lifecycle.sh, specs/mardi-gras-agentic-integration/tests/runtime-canary.sh, tests/inventory/mardi-gras-06-live.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-06-live.json

## Goal

Install the CLI and referenced toolkit procedures as immutable,
manifest-hashed packages, expose a stable resolver, and make `agentic live`
perform the complete read-only compatibility check before launching the
provider. Runtime/workflow support comes from the existing runtime profiles
and is promoted only by a live canary.

## Touch

Do not vendor Mardi Gras, duplicate the runtime capability source, or enable
production launch for a patched/unreleased provider. Install tests use an
isolated home and path; they must not mutate the developer's real installation.

## Steps

1. Write failing isolated install, resolver-upgrade, package-retention,
   handshake, and runtime-capability fixtures first.
2. Build the manifest-hashed package layout and atomic owned resolver with
   safe upgrade, uninstall, explicit state-purge behavior, and a read-only
   `agentic package current --json` resolver that does not require Mardi Gras.
3. Extend the existing runtime-profile parser as the one capability source
   and produce fixed pointer-only native argv for each supported pair.
4. Implement `agentic live --check` and `agentic live` with exact binary
   resolution, macOS `/usr/bin/mg` rejection, released-provider handshake,
   package/plugin identity, and no-mutation failure paths.
5. Add hermetic lifecycle tests, live canary drivers, and
   unique inventory fragments.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_live.py runtimes/test_parse_headless.py -q` → capability parsing, exact live argv, handshake rejection, package-current resolution, and no-mutation check behavior pass with hermetic binaries (L3).
- [ ] `bash tests/test_agentic_install_lifecycle.sh` → the canonical wrapper runs isolated HOME/PATH lifecycle fixtures proving atomic install/upgrade/uninstall, immutable recorded-package use, reference retention, plugin mismatch handling, and explicit-only purge (L3).
- [ ] `MANUAL_PENDING=1 bash specs/mardi-gras-agentic-integration/tests/runtime-canary.sh claude work build drain && MANUAL_PENDING=1 bash specs/mardi-gras-agentic-integration/tests/runtime-canary.sh codex work build drain && MANUAL_PENDING=1 bash specs/mardi-gras-agentic-integration/tests/runtime-canary.sh antigravity work build` → manual-pending because authenticated interactive runtime binaries and real PTYs are required; each supported adapter reaches packaged-skill preflight before Beads mutation, and unsupported Antigravity modes fail before spawn (L3).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json` → installer/live/runtime surfaces and tests are inventoried (L2).
- [ ] `bash scripts/check.sh` → the repository gate remains green after package and live activation work (L3).
