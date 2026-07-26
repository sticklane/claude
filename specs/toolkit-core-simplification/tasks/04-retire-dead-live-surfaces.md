# Task 04: retire dead live references and one-off workflows

<!-- Task state is canonical in bd. The Status line is frozen display and is not edited by workers. -->

Status: pending
Depends on: 02
Priority: P1
Budget: 32 turns
Spec: ../SPEC.md (requirement R4)
Touch: .claude/rules/token-discipline.md, .claude/workflows/cross-repo-beads-adoption.js, .claude/workflows/full-cutover-and-health-check.js, .claude/workflows/ultracode-queue-sweep.js, .claude/workflows/ultracode-queue-sweep-phase2.js, agentic/audit.py, bin/check-token-discipline, tests/test_agentic_audit.py, tests/test_check_token_discipline.sh, runtimes/antigravity.md, runtimes/claude-code.md, runtimes/codex.md, antigravity/README.md, codex/README.md, docs/agent-dashboards.md, docs/decisions/orchestration.md, docs/decisions/orchestrator-context.md, docs/external-playbooks.md, docs/memory.md, docs/memory/drain-dispatch-lessons.md, docs/memory/live-drain-reconciliation.md, docs/task-tracking-design-research-2026-07.md, tests/test_live_surface_retirement.sh, tests/inventory/04-live-retirement.json, specs/toolkit-core-simplification/surface-inventory/04-live-retirement.json

## Goal

Remove completed-spec-specific workflows from live discovery and eliminate
live recommendations for deleted `drain_frontier.py`, the abandoned composer,
and mirrored runtime ports. Historical specs and evidence remain intact and
explicitly historical.

## Touch

Delete only rows classified `retire-dead` in the frozen baseline. Preserve
`deep-research.js`, standalone ctx, native runtime orchestration, and every
functioning on-demand skill.

## Steps

1. Write the failing live-surface test from the baseline classifications.
2. Remove the four completed one-off workflows and their live callers.
3. Replace or remove deleted-executable/composer/mirror claims in the listed
   rules, audit metric, runtime profiles, READMEs, and live docs.
4. Re-run the inventory gate to prove no retained row was deleted.

## Acceptance

- [ ] `bash tests/test_live_surface_retirement.sh` → no live discovery or recommendation reaches a retired workflow/executable, while historical evidence remains readable (L2).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json` → only baseline rows classified `retire-dead` are absent (L2).
- [ ] `bash scripts/check.sh` → the cleaned live surface passes the full inventoried suite (L3).
