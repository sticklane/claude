# Task 09: enforce the default-context budget and publish the evidence report

<!-- Task state is canonical in bd. The Status line is frozen display and is not edited by workers. -->

Status: pending
Depends on: 01, 03, 04, 06, 08
Priority: P2
Budget: 32 turns
Spec: ../SPEC.md (requirement R9)
Touch: scripts/check-context-budget.py, scripts/report-toolkit-outcomes.py, tests/test_context_budget.sh, tests/inventory/09-context-report.json, specs/toolkit-core-simplification/REPORT.json, specs/toolkit-core-simplification/surface-inventory/09-context-report.json

## Goal

Set and enforce a measured line/token ceiling for default-loaded AGENTS and
rules, then publish the dated before/after report required by R9. The report
must distinguish confirmed removals from retained optional skills and show
unknown rates instead of manufacturing outcome claims.

## Touch

This task records final evidence in its additive surface fragment and report;
the frozen baseline is not edited. It may not reclassify or delete a
functioning optional skill. Do not edit the default-loaded files themselves;
Tasks 03/04 own their content.

## Steps

1. Write failing real-tree and over-budget fixtures for the context check.
2. Derive the ceiling from the frozen baseline with explicit headroom and add
   the deterministic token estimate.
3. Generate and validate `REPORT.json` with every R9 before/after field,
   scorecard formula version, source window, and unknown rates.

## Acceptance

- [ ] `bash tests/test_context_budget.sh` → real tree passes and line/token overflow fixtures fail with exact contributors (L2).
- [ ] `python3 scripts/report-toolkit-outcomes.py --check specs/toolkit-core-simplification/REPORT.json` → validates all dated R9 evidence without a skill-count target (L2).
- [ ] `bash scripts/check.sh` → clean-checkout canonical gate runs every retained test exactly once and is green (L3).
