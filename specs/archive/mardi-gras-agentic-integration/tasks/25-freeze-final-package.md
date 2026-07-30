# Task 25: freeze the final immutable package

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status is always the frozen initial display value `pending`; workers and orchestrators update bd, never this line. -->
<!-- Task definitions are immutable after registration. Workers report progress, decisions, and deferred questions to the orchestrator; they do not rewrite task files. -->

Status: pending
Depends on: 01, 24, 37
Priority: P0
Budget: 32 turns
Spec: ../SPEC.md (requirements R1, R7, R8, R12, R15, R19)
Touch: agentic/package-files-v1.txt, agentic/schema/public-json-surfaces-v1.json, .claude-plugin/plugin.json, .codex-plugin/plugin.json, plugin.json, skills/, tests/test_agentic_package_inventory.py, tests/test_agentic_public_json_contract.py, tests/test_plugin_manifest_versions.py, tests/inventory/mardi-gras-25-package-freeze.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-25-package-freeze.json

## Goal

Freeze the complete source inventory and synchronized runtime manifests after
every packaged skill, profile, schema, provider, documentation, and Workboard
change has landed. A clean source revision must build the same canonical R7
package identity twice, while an omitted, extra, mode-drifted, tampered, or
ambient dependency fails before installation or canary use.

## Touch

This task updates only final inventory, generated portable entrypoints, public
surface registration, and synchronized package manifests; it does not change
workflow behavior or certification reports. Regenerate `skills/` from the
canonical `.claude/skills/` tree rather than hand-editing generated wrappers,
preserve the fleet entrypoint and marketplace promise, and do not install
into the developer's real account during tests.

## Steps

1. Write failing closed-inventory tests for missing, extra, duplicate,
   noncanonical, symlink, mode, source-commit, generated-entrypoint, plugin
   identity, and public-JSON membership drift.
2. Regenerate all portable entrypoints from their canonical skills, verify the
   fleet wrapper remains present, and update the sorted
   `agentic/package-files-v1.txt` inventory to include every final committed
   member exactly once.
3. Synchronize the Claude and Codex package versions and validate the
   intentionally unversioned Antigravity manifest without changing package
   behavior.
4. Build twice from the same clean source revision in isolated directories,
   compare exact package-manifest bytes and identity pairs, and inject member,
   mode, runtime, loader, and ambient-import drift at package-current,
   supervise, canary merge, and cutover boundaries.
5. Run the full package lifecycle, public JSON, entrypoint, inventory, and
   repository gates before handing the immutable source revision to Task 26.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_package_inventory.py -q` → the closed source inventory, generated wrappers, source-commit bytes, normalized modes, synchronized manifests, and deterministic double-build identity pass while every drift fixture fails closed (L3).
- [ ] `bash specs/mardi-gras-agentic-integration/tests/install-lifecycle.sh` → the exact final source installs, verifies, upgrades, retains referenced versions, rejects tampering and identity collisions, and uninstalls only inside isolated account/state roots (L3).
- [ ] `python3 -m pytest tests/test_agentic_public_json_contract.py tests/test_plugin_manifest_versions.py -q` → every final public artifact is registered and Claude/Codex versions match while Antigravity retains its required unversioned form (L2).
- [ ] `bash tests/test_codex_skill_entrypoints.sh` → every generated entrypoint, including fleet and all packaged façades, is present and current (L2).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json && bash scripts/check.sh` → the final package surface is fully classified and the complete toolkit gate passes (L3).
