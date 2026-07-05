# Task 03: Vendor `viz.py` into agent-console + wire + conformance

Status: pending
Depends on: 01
Priority: P1
Budget: 10 turns
Spec: ../SPEC.md (requirements R6 — agent-console half, R7, R8)
Touch: /Users/sjaconette/agent-console/viz.py, /Users/sjaconette/agent-console/agent-console.py, /Users/sjaconette/agent-console/scripts/check.sh

## Goal
The `agent-console` live server renders its Sessions block as a `viz.timeline()` (replacing flat text) and its spec DAGs via `viz.dag()`, from a **byte-identical vendored copy** of the toolkit `viz.py`. A conformance step in `scripts/check.sh` fails the build if the vendored copy drifts. agent-console stays pure-stdlib / no-network.

## Touch
Work entirely in the separate repo `~/agent-console` (its own git + `scripts/check.sh` gate). Do NOT edit toolkit files here. The vendored `viz.py` must be a byte-for-byte copy of `~/claude/.claude/skills/_shared/viz.py` (from task 01).

## Steps
1. Copy `~/claude/.claude/skills/_shared/viz.py` → `~/agent-console/viz.py` (byte-identical; verify sha256 header).
2. In `collect_sessions`/`live_sessions` (`agent-console.py:404,468-480`) add `start_ts` per SPEC.md's resolution order (PID-injected transcript-less sessions → `start_ts = end_ts`, min-width bar).
3. Delete `_dep_graph_svg` (`:891-958`) and `_task_stroke` (`:880-888`); call `viz.dag()` at the former wiring site (`:1057-1068`) and `viz.timeline()` in place of the flat-text Sessions block (`:1082-1097`). Inject `viz.VIZ_CSS`.
4. Add the conformance step to `scripts/check.sh` per R8: primary = diff vendored vs `~/claude/.claude/skills/_shared/viz.py` when present (hard-fail on diff); secondary = recompute vendored body sha256 vs its header (hard-fail); toolkit absent → print the SKIPPED line and pass.

## Acceptance
- [ ] `bash /Users/sjaconette/agent-console/scripts/check.sh` → PASS (existing render smoke-tests + new conformance step; covers R6/R7/R8)
- [ ] tamper test: append a byte to `/Users/sjaconette/agent-console/viz.py`, rerun `bash /Users/sjaconette/agent-console/scripts/check.sh` → **fails** the toolkit-diff (with `~/claude` present); then restore the byte and it passes
- [ ] `grep -c '_dep_graph_svg\|_task_stroke' /Users/sjaconette/agent-console/agent-console.py` → `0` (old renderers deleted)
