# Task 01: extract_agent_tree() data layer

Status: pending
Depends on: none
Priority: P0
Budget: 20 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4)
Touch: .claude/skills/workboard/workboard.py, .claude/skills/workboard/test_workboard.py

## Goal

`workboard.py` gains a new pure function `extract_agent_tree(session_jsonl_path)`
that parses a session's `.jsonl` for Agent/Task `tool_use`/`tool_result` pairs,
loads each spawned sub-agent's `subagents/agent-<agentId>.jsonl` +
`agent-<agentId>.meta.json` pair, and recurses into any further Agent
`tool_use` events found inside a sub-agent's own transcript. Covered by unit
tests using constructed fixtures (built inline with `tempfile`, matching this
test file's existing self-contained pattern — no new fixture-file
infrastructure).

## Touch

Only `workboard.py` and `test_workboard.py`. Do not touch `scan_sessions()`
(workboard.py:788-838), `assemble()` (workboard.py:1424-1495), or any
rendering function (`_session_timeline_html()`, `render_html()`) — those are
Task 02/03's scope. This task adds one new standalone function plus its
tests; it does not wire the function into anything yet.

## Steps

1. Write failing tests first in `test_workboard.py`, each building its own
   throwaway session directory via `tempfile.TemporaryDirectory()` containing
   a session `.jsonl` and a `subagents/` dir with `agent-<id>.jsonl` +
   `agent-<id>.meta.json` files (mirroring the real shape: meta carries
   `agentType`, `description`, `toolUseId`, `spawnDepth`; each event inside
   the sub-agent's own `.jsonl` carries a `sessionId` back-reference):
   - `test_extract_agent_tree_nests_grandchild_under_parent`: fixture has a
     session spawning agent A (spawnDepth 1), which itself spawns agent B
     (spawnDepth 2) — assert B appears nested under A's node, not at the
     tree root (R4).
   - `test_extract_agent_tree_empty_for_no_agent_calls`: fixture `.jsonl` has
     no Agent/Task `tool_use` events — assert the return is an empty tree
     (e.g. `[]` or equivalent), no exception raised (R3).
   - `test_extract_agent_tree_node_fields`: assert each returned node exposes
     `agentId`, `agentType`, `description`, `status`, `spawnDepth`,
     `started_ts` at minimum (R2).
   Run the suite and confirm all three fail (function doesn't exist yet).
2. Implement `extract_agent_tree(session_jsonl_path)` in `workboard.py`:
   parse the parent `.jsonl` for Agent/Task `tool_use` calls and their
   `tool_result` (capturing `agentId`); for each, load the sibling
   `subagents/agent-<agentId>.meta.json` + `.jsonl` pair; derive `status`
   the same way `/fleet` derives it today (running/completed/failed);
   recurse into the sub-agent's own `.jsonl` for nested Agent `tool_use`
   events, attaching them as children keyed by `spawnDepth`.
3. Run the three tests and confirm they pass for the right reason (not by
   loosening the assertions).
4. Refactor for clarity only if needed — no behavior change once green.

## Acceptance

- [ ] `python3 -m unittest discover -s .claude/skills/workboard -p "test_workboard.py" -v 2>&1 | grep -E "test_extract_agent_tree_nests_grandchild_under_parent|test_extract_agent_tree_empty_for_no_agent_calls|test_extract_agent_tree_node_fields|OK"` → all three new tests pass and suite reports `OK`.
- [ ] `python3 -c "import ast; tree=ast.parse(open('.claude/skills/workboard/workboard.py').read()); print(any(isinstance(n, ast.FunctionDef) and n.name=='extract_agent_tree' for n in ast.walk(tree)))"` → prints `True`.
