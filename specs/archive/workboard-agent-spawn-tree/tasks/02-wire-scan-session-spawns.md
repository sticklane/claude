# Task 02: scan_session_spawns() wiring into assemble() and --json

Status: done
Depends on: 01
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirements R5, R8)
Touch: .claude/skills/workboard/workboard.py, .claude/skills/workboard/test_workboard.py, .claude/skills/workboard/reference.md

## Goal

A new `scan_session_spawns()` function follows the existing `scan_*()`
contract (reference.md:62-67: return records keyed with
`last_touched`/`last_ts`), runs `extract_agent_tree()` (from Task 01) per
session, and attaches the resulting tree to that session's existing record
inside `assemble()` — without changing any other `scan_*()` function's
output shape. `workboard.py --json` output includes the new tree data per
session.

## Touch

Only `workboard.py` (new function + one wiring edit inside `assemble()`,
near line 1424-1495), `test_workboard.py`, and a short addition to
`reference.md` documenting the new field. Do not touch rendering
(`_session_timeline_html()`, `render_html()`) — that's Task 03. Do not
modify `extract_agent_tree()`'s internals (Task 01's scope); call it as-is.

## Steps

1. Write a failing test first: construct (or reuse Task 01's fixture
   pattern) a session directory with a spawning sub-agent, call
   `scan_session_spawns()` directly, and assert the returned record for
   that session carries a non-empty tree field (e.g. `spawn_tree`) plus
   `last_touched`/`last_ts` per the scan contract.
2. Write a second failing test asserting that running `assemble()` (or the
   relevant subset of scans) before and after this change produces
   identical output for every other `scan_*()` function — i.e. diff the
   non-session parts of the assembled dict, or directly compare each other
   `scan_*()` function's own return value in isolation (R5).
3. Implement `scan_session_spawns(session_jsonl_path)` (or matching the
   existing per-session scan signature) calling `extract_agent_tree()` per
   session and returning the tree keyed for merge into that session's
   existing record.
4. Wire it into `assemble()` alongside the other `scan_*()` calls that feed
   session records — attach the tree onto each session dict under a
   `spawn_tree` key (or equivalently named, matching R8's wording) without
   altering any other scan's output.
5. Confirm `--json` includes the field: add or extend a test that runs the
   CLI (or calls `assemble()` directly, if that's faster/cleaner) and
   asserts a session with a real or fixture spawn tree has a non-empty
   `spawn_tree` key in the JSON-serializable output.
6. Add a short note to `reference.md` documenting the new field, following
   the existing scan_*() documentation style at reference.md:62-67.

## Acceptance

- [x] `python3 -m unittest discover -s .claude/skills/workboard -p "test_workboard.py" -v 2>&1 | grep -E "test_scan_session_spawns|OK"` → new tests pass, suite reports `OK`.
- [x] `python3 .claude/skills/workboard/workboard.py --json | python3 -m json.tool > /dev/null && echo VALID_JSON` → prints `VALID_JSON` (wiring doesn't break the existing `--json` output).
- [x] A test or explicit diff check confirms every other `scan_*()` function's own return value is byte-identical before/after this change (R5) — cite the specific test name added in step 2 here once written. Test: `test_scan_session_spawns_leaves_other_scans_unchanged` (in `test_workboard.py`, class `TestScanSessionSpawns`) captures `scan_sessions()` and `scan_todos()` output before and after `scan_session_spawns()` runs and asserts equality.
