# Task 23: document agentic live

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status is always the frozen initial display value `pending`; workers and orchestrators update bd, never this line. -->
<!-- Task definitions are immutable after registration. Workers report progress, decisions, and deferred questions to the orchestrator; they do not rewrite task files. -->

Status: pending
Depends on: 01, 22, 39, 37
Priority: P0
Budget: 28 turns
Spec: ../SPEC.md (requirement R16)
Touch: docs/guides/agentic-live.md, README.md, specs/mardi-gras-agentic-integration/DOC-REVIEW.json, agentic/schema/public-json-surfaces-v1.json, tests/test_agentic_live_docs.py, tests/test_agentic_public_json_contract.py, tests/inventory/mardi-gras-23-docs.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-23-docs.json

## Goal

Publish the complete operator and developer contract for `agentic live` from
the behavior proven by Tasks 22 and 39. The guide distinguishes
repository-scoped toolkit activity from `fleet`'s session-wide native
inventory and Workboard's machine-wide history without removing or rerouting
any fleet promise.

## Touch

This task owns only the guide, its README entry, the documentation contract
test, and revision-bound review artifact. It must not change CLI behavior,
runtime profiles, Workboard, fleet implementation or routing, or claim that
an upstream provider release exists. Load the repository's prose-review
doctrine before drafting the human-facing files.

## Steps

1. Write the failing closed R16 topic-map test first, covering every named
   install, control, activity, runtime, recovery, upgrade, fleet, Workboard,
   and uninstall topic.
2. Draft the guide and concise README route from the verified behavior,
   explicitly naming Beads as work authority, skills as execution authority,
   Mardi Gras as repository TUI, fleet as session-wide native inventory, and
   Workboard as machine-wide read-only inventory after cutover.
3. Document activity confidence, child monitoring, claim loss, drain
   confirmation, direct-skill correlation, tmux and foreground behavior,
   spawn failure, duplicate launch, stale sources, recovery limits, supported
   runtime/workflow pairs, upgrade identity checks, and uninstall/purge.
4. Run Vale, link checks, an independent prose review, and a README reader
   test against the exact reviewed revision. In a direct child evidence
   commit, write canonical `DOC-REVIEW.json` naming that ancestor and prove
   the guide and README bytes remain identical.
5. Register every documentation-review leaf in the shared public-JSON
   inventory and add the documentation surfaces to the measured inventory.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_live_docs.py -q && vale docs/guides/agentic-live.md README.md && bash tests/test_doc_links.sh` → the complete R16 topic map, revision-bound review artifact, style checks, links, and byte-identity guard pass (L2).
- [ ] `python3 -c 'import json; p="specs/mardi-gras-agentic-integration/DOC-REVIEW.json"; d=json.load(open(p, encoding="utf-8")); assert d["schema"]=="agentic.documentation-review/v1" and d["vale"]=="pass" and d["prose_review"]=="pass" and d["reader_test"]=="pass" and sorted(d["paths"])==["README.md","docs/guides/agentic-live.md"]'` → the bounded independent-review artifact records all required judgments for the exact doc paths (L1).
- [ ] `python3 -m pytest tests/test_agentic_public_json_contract.py -q` → the documentation-review artifact and every field are canonical, bounded, and registered (L2).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json && bash scripts/check.sh` → documentation surfaces are classified and the toolkit gate passes (L3).

Depth ceiling: the topic map and deterministic style/link checks are L1/L2;
the revision-bound independent prose-review and reader-test verdicts are the
required judgment complement.
