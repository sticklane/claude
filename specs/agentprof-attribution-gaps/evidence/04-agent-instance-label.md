# Verification: task 04 — agent_id label on subagent samples

Verdict: PASS (with one process finding — task file not updated)

## Task-file append-only check

Command: `git -C <worktree> diff 55fe414 -- specs/agentprof-attribution-gaps/tasks/04-agent-instance-label.md`
Output: empty (no diff at all).

Finding: The task file itself was never touched — Status is still
`in-progress`, none of the three acceptance checkboxes are ticked, and no
evidence-citation lines were added, even though the underlying code/tests/docs
work is complete and all three criteria pass. This isn't a violation of the
append-only rule (nothing disallowed was changed), but it means the task file
does not reflect completion — a drain/orchestrator reading only the task file
would see it as unfinished. Flagging as a process gap, not a FAIL.

## Criterion 1: go test ./internal/claude/, including TestSubagentSamplesCarryDistinctAgentID

Command: `cd agentprof && go test ./internal/claude/ -run TestSubagentSamplesCarryDistinctAgentID -v`
Output tail:
```
=== RUN   TestSubagentSamplesCarryDistinctAgentID
--- PASS: TestSubagentSamplesCarryDistinctAgentID (0.00s)
PASS
ok  	github.com/sticklane/agentprof/internal/claude	0.195s
```

Full package run: `cd agentprof && go test ./internal/claude/` → `ok`.

Test content (agentprof/internal/claude/claude_test.go, appended lines):
uses `collectFixture(t)`, asserts `agent_ids["A"]` and `agent_ids["WS"]` both
present (two same-typed scout subagents get distinct `agent_id` values), and
separately asserts the single main-loop sample (found via
`findByStack(..., []string{"proj","t01 · start","skill:build","main","claude-fable-5"})`)
carries NO `agent_id` key. This is a genuine distinctness + absence assertion,
not a trivial always-pass.

TDD verification: checked out the test-only commit (`a49abf2`, prior to the
`ad60d3d` feat commit) in a scratch worktree and re-ran the test — it FAILED
for the right reason:
```
claude_test.go:987: no sample carries agent_id=A; got agent_ids map[]
claude_test.go:990: no sample carries agent_id=WS; got agent_ids map[]
--- FAIL: TestSubagentSamplesCarryDistinctAgentID (0.00s)
```
Confirms genuine red→green (scratch worktree removed after check; no tracked
files were mutated in the actual worktree under review).

Result: PASS

## Criterion 2: grep -qi 'agent_id' agentprof/SCHEMA.md

Command: `grep -qi 'agent_id' agentprof/SCHEMA.md && echo "SCHEMA HIT"`
Output: `SCHEMA HIT`

Content check: SCHEMA.md gained a new "## The `agent_id` label" section
(between the `reprime` section and "Cost-summary sections") describing the
label's source (`agent-<id>.jsonl` basename), its purpose (distinguishing
same-typed subagent instances sharing a stack frame), that main-loop calls
carry none, and its use with `-tagfocus agent_id=<id>` for fan-out width /
per-instance parallelism — this is a substantive description, not an
incidental mention. Also updated the `labels:` bullet list to include
`agent_id`.

Result: PASS

## Criterion 3: bash agentprof/scripts/check.sh

Command: `bash agentprof/scripts/check.sh`
Output:
```
check: format-check ok
check: lint ok
check: tests ok
```

Result: PASS (green)

## Goal sanity-check

Implementation diff (agentprof/internal/claude/claude.go):
- `agentFile` struct gained `id string` field (sidecar instance id, comment:
  "sidecar instance id (agent-*.jsonl basename sans prefix/suffix)").
- `enumerate()` now threads `id: agentID` into the constructed `agentFile`
  (agentID was already computed at parse time, previously discarded — matches
  the Goal's "currently discarded" framing).
- In `session.collect()`, the main-loop sample (`s.sample(...)`, using
  session-level `s.id`) is untouched; only the subagent-emission block
  (`r.sample(stack, s.id, turn)` → `ms`) sets `ms.Labels["agent_id"] = a.id`,
  and tool-result samples from the same subagent get the same label in a
  loop. This confirms: subagent samples get `agent_id=<sidecar id>`,
  main-loop samples get none, existing labels untouched (label is added to
  the map, not replacing anything).

Result: matches Goal.

## Scope / Touch check

Command: `git -C <worktree> diff 55fe414 --stat`
```
 agentprof/SCHEMA.md                      | 15 ++++++++++++++-
 agentprof/internal/claude/claude.go      | 10 ++++++++--
 agentprof/internal/claude/claude_test.go | 29 +++++++++++++++++++++++++++++
 3 files changed, 51 insertions(+), 3 deletions(-)
```
All three files fall within Touch scope (`agentprof/internal/claude/`,
`agentprof/SCHEMA.md`). Confirmed with a stat excluding the allowed paths —
empty output, i.e. no changes anywhere else in the tree. `agentprof/testdata/`
was listed in Touch but not modified — not a problem (the existing fixture
already had `agent-A` / `agent-WS` transcripts, per the test's use of
`collectFixture`).

No scope creep found.

## Overall verdict: PASS

All three acceptance criteria pass and are genuinely exercised (not
trivially satisfied). Implementation matches the stated Goal. No changes
outside Touch scope. One process finding: the task file's Status/checkboxes
were never updated to reflect completion (see "Task-file append-only check"
above) — worth flipping before this is considered administratively closed,
but does not affect the PASS verdict on the acceptance criteria themselves.
