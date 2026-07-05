# Task 01: Extract the shared `viz.py` renderer + golden tests

Status: done
Depends on: none
Priority: P0
Budget: 12 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4)
Touch: /Users/sjaconette/claude/.claude/skills/_shared/viz.py, /Users/sjaconette/claude/.claude/skills/_shared/test_viz.py

## Goal
The single source-of-truth renderer exists at `.claude/skills/_shared/viz.py` — pure stdlib, exposing `timeline()`, `dag()`, `VIZ_CSS`, `canonical_status()`, `STATUS_HEX`, and the `--emit-fleet-css` / `--self-sha256` CLI, with a `# viz-sha256:` provenance header. A `test_viz.py` proves every renderer contract. This is the foundation the other three tasks import or vendor; nothing else can start until it is green.

## Touch
Create only the two files under `.claude/skills/_shared/`. Do NOT modify `workboard.py`, `agent-console.py`, or `fleet/reference.md` (later tasks). Lift the DAG layout from `agent-console.py:891-958` and timeline geometry from `fleet/reference.md:31-37,106-121` by copying into the new module — do not edit those originals here.

## Steps
1. Write `test_viz.py` FIRST (failing): golden `dag()` (a 3-task chain → one `<g>` per task + `<path>` per edge; empty-edge list → `""`; a cyclic `deps` set terminates); `timeline()` (2 rows → two `.viz-bar`s ordered by `start_ts`, `left`/`width` normalized to `[min(start),now]` floored 0.75%; empty rows → fixed empty-state string; a row missing `start_ts` raises `ValueError`; a rendered `.viz-bar` contains its `var(--viz-*, #hex)` fallback so it is colored with no host vars); `canonical_status()` covering the full alias table + unknown→`open`; `STATUS_HEX` has all 6 tokens.
2. Implement `viz.py` to pass: `canonical_status`, `STATUS_HEX` (running `#d98a63`, open `#6ea3c0`, done `#3a4150`, failed `#c96262`, stale `#5a6070`, blocked `#d9b063`), `dag()` (layout verbatim from source; node **stroke** + num-text via `STATUS_HEX`; fill/edge/title = named constants `_DAG_NODE_FILL/_DAG_EDGE/_DAG_TEXT`; self-contained dark mini-canvas bg), `timeline()`, `VIZ_CSS` (`.viz-lane/.viz-track/.viz-bar/.viz-axis`, `.viz-graphwrap/.viz-node/.viz-edge`; colors via `var(--viz-<token>, <hex>)`, no `:root`).
3. Add the CLI: `--emit-fleet-css` prints exactly `VIZ_CSS` between `/* >>> viz:timeline-css BEGIN */` and `/* <<< viz:timeline-css END */`; `--self-sha256` prints sha256 of the body below the `# viz-sha256:` header. Add/update the header line to match.
4. Import-audit clean (stdlib only).

## Acceptance
- [x] `python3 -m py_compile /Users/sjaconette/claude/.claude/skills/_shared/viz.py` → exit 0 (verifier confirmed, agent aebe696152f843ed8)
- [x] the stdlib-only AST audit from SPEC.md R1 acceptance → prints `stdlib-only: ok` (verifier confirmed)
- [x] `pytest /Users/sjaconette/claude/.claude/skills/_shared/test_viz.py` → all pass (covers R2–R4) (verifier: 14 passed, spot-checked assertions are non-vacuous)
- [x] `python3 /Users/sjaconette/claude/.claude/skills/_shared/viz.py --emit-fleet-css | head -1` → the `BEGIN` sentinel line (verifier confirmed)
- [x] `python3 /Users/sjaconette/claude/.claude/skills/_shared/viz.py --self-sha256` → a 64-hex string matching the file's `# viz-sha256:` header (verifier confirmed exact match)
