# Task 03: render collapsible spawn-tree view per session

Status: pending
Depends on: 02
Priority: P1
Budget: 16 turns
Spec: ../SPEC.md (requirements R6, R7)
Touch: .claude/skills/workboard/workboard.py, .claude/skills/workboard/test_workboard.py

## Goal

The existing session view (near `_session_timeline_html()`,
workboard.py:1762-1784) renders an expandable/collapsible indented tree for
any session carrying a non-empty `spawn_tree` (from Task 02) — one row per
agent, indented by `spawnDepth`, showing agent type/description, a
status chip, and start/elapsed time. Sessions without a spawn tree render
exactly as before (no visual regression). Failed/errored branches get
distinct styling.

## Touch

Only `workboard.py`'s rendering section (`_session_timeline_html()`,
`render_html()`, and their shared CSS block) and `test_workboard.py`. Do not
touch `scan_session_spawns()`, `assemble()`'s wiring, or `extract_agent_tree()`
— those are Task 01/02's scope and must already be producing correct data by
the time this task starts.

## Steps

1. Reuse `/fleet`'s existing status-chip convention exactly rather than
   inventing a new one: glyph + word pairs `▶ running`, `✓ completed`,
   `✕ failed` (fleet/reference.md:29-30, HTML pattern at
   fleet/reference.md:181, CSS at fleet/reference.md:99-107 — `.chip`,
   `.s-running`, `.s-completed`, `.s-failed`, color on the glyph only,
   word always present).
2. Write a failing test first asserting that rendering `render_html()` (or
   the relevant helper) for a fixture session with a non-empty `spawn_tree`
   produces HTML containing: one row per tree node, indentation reflecting
   `spawnDepth` (e.g. nested `<ul>`/`<li>` or a depth-keyed class/margin),
   a status chip per node using the fleet glyph+word convention, and a
   visually distinct class/marker on failed nodes (e.g. an `s-failed`
   class plus a row-level modifier class, not color alone).
3. Write a second failing test asserting that rendering a session with an
   empty/absent `spawn_tree` produces byte-identical (or equivalent-DOM)
   output to the pre-feature rendering — no regression for the common case
   (R6).
4. Implement the rendering: extend `_session_timeline_html()` (or add a
   sibling helper it calls) to emit the collapsible/expandable tree markup
   when `spawn_tree` is non-empty, wire the fleet-style chip CSS into
   workboard's existing stylesheet block, and leave the no-tree path
   unchanged.
5. Run both tests, confirm green for the right reason.

## Acceptance

- [ ] `python3 -m unittest discover -s .claude/skills/workboard -p "test_workboard.py" -v 2>&1 | grep -E "test_render.*spawn|test_render.*no_regression|OK"` → new rendering tests pass, suite reports `OK`. This is the real gate for R6/R7; the fixture built in step 2 is the deterministic source of truth, not any live scan of real session data.
- [ ] Within the same fixture-based test added in step 2, assert (via Python's `re` module, inline in the test) that the rendered HTML fragment contains a fleet-style chip class matching `class="chip s-(running|completed|failed)"` — confirms a status chip actually renders for the fixture's spawn-tree node, fully deterministic (no dependency on whatever real session data happens to be on disk at build time).
