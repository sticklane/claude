# Task 02: Wire the `/workboard` skill to `viz.py`

Status: in-progress
Depends on: 01
Priority: P1
Budget: 10 turns
Spec: ../SPEC.md (requirements R5, R6 — workboard half)
Touch: /Users/sjaconette/claude/.claude/skills/workboard/workboard.py, /Users/sjaconette/claude/.claude/skills/workboard/test_workboard.py

## Goal
The `/workboard` skill imports the shared `viz` module and renders a **Sessions timeline** (replacing its flat session list) plus spec **dependency DAGs**, so the snapshot dashboard uses the shared renderer instead of its own bars-and-tables. `test_workboard.py` gains assertions for both.

## Touch
Only the two workboard skill files. Do NOT touch `agent-console.py` or `fleet/reference.md` (sibling tasks own the agent-console `start_ts` half and the fleet migration). Import `viz` via `sys.path.insert(0, str(Path(__file__).parent.parent / "_shared"))`.

## Steps
1. In `scan_sessions` (`workboard.py:574-582`) add `start_ts` per SPEC.md's resolution order (earliest transcript record ts → transcript `st_birthtime` → `end_ts` for transcript-less sessions); keep the existing last-activity as `end_ts`. Write the failing test assertion first.
2. Import `viz`; render the sessions section via `viz.timeline(rows)` (map each session → `{label, status, start_ts, end_ts, tooltip, href}`), and render each spec's task graph via `viz.dag(tasks)`.
3. Inject `viz.VIZ_CSS` into the page `<style>`.
4. Extend `test_workboard.py`: a session row produces a `.viz-bar` that carries its `var(--viz-*, #hex)` fallback (colored with no host vars); a spec with deps produces a `<path>`.

## Acceptance
- [ ] `pytest /Users/sjaconette/claude/.claude/skills/workboard/test_workboard.py` → all pass (covers R5 + workboard R6)
- [ ] `python3 -c "import sys; sys.path.insert(0,'/Users/sjaconette/claude/.claude/skills/_shared'); sys.argv=['w']; import importlib.util as u; ..."` — a smoke render of the workboard HTML contains `viz-bar` and (given a spec with deps) `<path` (assert in the test file rather than inline if simpler)
