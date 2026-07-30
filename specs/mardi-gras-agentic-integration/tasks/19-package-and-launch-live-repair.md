# Task 19: package the immutable CLI runtime

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status is always the frozen initial display value `pending`; workers and orchestrators update bd, never this line. -->
<!-- Task definitions are immutable after registration. Workers report progress, decisions, and deferred questions to the orchestrator; they do not rewrite task files. -->

Status: pending
Depends on: 01, 14, 37
Priority: P0
Budget: 44 turns
Spec: ../SPEC.md (requirements R7, R8, R12)
Touch: agentic/cli.py, agentic/package.py, agentic/runtime.py, agentic/public_json.py, agentic/package-files-v1.txt, agentic/trusted-python-runtimes-v1.json, agentic/schema/package-manifest-v1.json, agentic/schema/installed-runtime-v1.json, agentic/schema/loader-closure-v1.json, agentic/schema/execution-environment-v1.json, agentic/schema/public-json-surfaces-v1.json, bin/agentic, bin/install-agentic-cli, bin/uninstall-agentic-cli, tests/test_agentic_package_supply.py, tests/test_agentic_install_lifecycle.sh, tests/test_agentic_public_json_contract.py, specs/mardi-gras-agentic-integration/tests/install-lifecycle.sh, tests/inventory/mardi-gras-19-live.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-19-live.json

## Goal

Build the reproducible R7 source package plus its self-contained Python
runtime and installation-specific execution-environment identity, then expose
the stable resolver, isolated install/upgrade/uninstall/purge lifecycle, and
read-only `agentic package current --json` wired through Task 14's existing
package-identity validator. This historical replacement continues to satisfy
`agentic-2nj.5` with the complete immutable package/resolver contract; live
activation is the separate Task 39.

## Touch

Task 14 supplies package-identity validation; this task owns source package
construction, trusted standalone runtime supply and extraction, loader
closure, execution-environment evidence, stable resolver, installation
lifecycle, retained versions, installation records, and wiring the
package-current command to Task 14's validator. It must not reimplement Task
14's package parser or identity logic, implement `agentic live`, add provider
or authority handshakes, select supported workflows, run runtime canaries, or
change claims or cohorts. Tests use isolated account/state roots. Task 25
performs the final inventory and manifest freeze after all packaged consumers
land.

## Steps

1. Write failing reproducible-package, hostile-archive, runtime-supply,
   loader-closure, execution-environment, isolated-install, resolver-upgrade,
   retained-package, uninstall, and explicit-purge fixtures first.
2. Implement the closed source inventory and canonical package manifest from
   clean committed blobs, including normalized modes, duplicate and
   normalization rejection, deterministic traversal, atomic same-version
   collision handling, and retention for nonterminal dispatches.
3. Verify the allowlisted standalone runtime archive and upstream checksum
   provenance before extraction; reject every non-regular archive form,
   validate the complete runtime inventory, and record the installed-runtime,
   loader-closure, and execution-environment identities described by R7.
4. Make the stable resolver invoke only the contained interpreter and package
   under the closed environment, revalidating every manifest, runtime,
   loader, module, and native-library identity before command dispatch.
5. Implement isolated install, upgrade, uninstall, and explicit purge plus
   installation-record population and `agentic package current --json`
   wiring. Every invocation passes Task 19's installed records and member
   bytes through Task 14's existing package-current identity validator;
   referenced-version retention remains intact and no second parser or
   identity decision is introduced.
6. Register package, runtime-supply, loader, resolver, and lifecycle public
   JSON surfaces without adding any live-check or runtime-canary output.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_package_supply.py -q` → deterministic source packaging, trusted runtime extraction, hostile archive rejection, complete runtime inventory, Linux and Darwin loader closure, isolated imports, and execution-environment drift behavior pass (L3).
- [ ] `bash specs/mardi-gras-agentic-integration/tests/install-lifecycle.sh --package-only` → isolated account/state fixtures prove resolver install/upgrade, same-version collision rejection, referenced-version retention, Task 14 validation of Task 19-installed records, uninstall with state retained, and explicit-only purge without a duplicate identity parser or live preflight (L3).
- [ ] `python3 -m pytest tests/test_agentic_public_json_contract.py -q -k 'package or runtime_supply or loader or execution_environment'` → every package, runtime-supply, loader, resolver, and lifecycle envelope is canonical and bounded (L2).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json && bash scripts/check.sh` → the immutable package/resolver surface consumed by `agentic-2nj.5` is classified and the repository gate passes (L3).
