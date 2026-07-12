# Verification: task 07 keep-pending-cli-wiring

Verdict: PASS

Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-a246fefe9fa13cf74
Base commit for task-file diff: 025f7a3

## Acceptance criteria

1. ✓ `cd agentprof && go run . claude --help 2>&1 | grep -q keep-pending`
   Exit 0. `--help` output includes `-keep-pending` flag with usage text
   "keep one tool:(pending) sample per unmatched tool call instead of
   consolidating them into a single pending_calls count".

2. ✓ `cd agentprof && go test ./...`
   All 15 packages pass:
   ```
   ok  	github.com/sticklane/agentprof	(cached)
   ok  	github.com/sticklane/agentprof/internal/antigravity	(cached)
   ok  	github.com/sticklane/agentprof/internal/bqtime	(cached)
   ... (12 more, all ok)
   ```
   Includes new tests `TestClaudeReportsUnmatchedToolCallsOnStderr` and
   `TestClaudeKeepPendingEmitsPerCallPendingSamples`.

3. ✓ `grep -qi 'keep-pending' agentprof/README.md`
   Exit 0. Two hits: line 238 (Pending tool calls section note) and line 406
   (Commands table row for `agentprof claude`), both describing the flag
   accurately.

4. ✓ `bash agentprof/scripts/check.sh`
   Output:
   ```
   check: format-check ok
   check: lint ok
   check: tests ok
   ```

## Behavior sanity-check

`cd agentprof && go run . claude --claude-dir testdata/claude-dir 2>&1 >/dev/null`
→ stderr:
```
skipped 1 unparseable lines
2 unmatched tool call(s) consolidated into tool:(pending)
```
Exit 0. Confirms the pending parse-stat is surfaced on a real run against the
committed fixture (testdata/claude-dir, which contains tool_use blocks with
no matching tool_result).

`--keep-pending` variant (same fixture) → stderr:
```
skipped 1 unparseable lines
2 unmatched tool call(s) kept as tool:(pending)
```
Exit 0. Confirms the flag is accepted and changes the disposition wording,
matching the code's `if *keepPending { disposition = "kept as tool:(pending)" }`
branch in cmd_claude.go.

## Diff / scope review

`git diff --stat 025f7a3 HEAD` touches exactly:
- agentprof/README.md (+8/-3)
- agentprof/cmd_claude.go (+17/-2)
- agentprof/cmd_claude_test.go (+34)
- specs/agentprof-attribution-gaps/tasks/07-keep-pending-cli-wiring.md (+11)

Matches the task's Touch list (agentprof/cmd_claude.go,
agentprof/cmd_claude_test.go, agentprof/README.md) plus the task file itself.
No scope creep found. cmd_claude.go change is minimal: adds `fs.Bool
("keep-pending", ...)`, switches `CollectWithReprime` → `CollectWithOptions`,
prints the pending stat conditionally. Matches the recorded PLAN exactly.

New tests (`TestClaudeReportsUnmatchedToolCallsOnStderr`,
`TestClaudeKeepPendingEmitsPerCallPendingSamples`) assert on substring
presence of behavior-level markers ("unmatched tool call", "tool:(pending)",
absence of "pending_calls") rather than exact output strings or internals —
consistent with testing behavior, not overfitting to a single fixture value.
Test file was not modified after some other failing-test commit as far as
this diff shows; it was added in the same diff as the feature.

## Append-only task-file check

`git diff 025f7a3 -- specs/agentprof-attribution-gaps/tasks/07-keep-pending-cli-wiring.md`
shows only one hunk: insertion of the `<!-- PLAN (delete at close-out) -->`
comment block (lines 16-25). No other lines changed — Status line (still
`in-progress`), Goal, Steps/Touch/Budget headers, Original report, and every
acceptance-criterion checkbox/text are byte-identical to base. This is within
the permitted append-only set (worker may "maintain plan comment block").

Finding (not a criteria failure, but worth flagging): despite the
implementation being complete and all four acceptance commands passing, the
worker never flipped the Status line from `in-progress` nor ticked any of
the acceptance checkboxes nor added evidence-citation lines in the task file
itself — the task file looks like work is still in flight even though the
code is done. The PLAN comment block also was never removed at close-out.
This is a housekeeping gap, not a criterion violation (append-only rule was
not violated — nothing impermissible was changed).

## Gates

`bash agentprof/scripts/check.sh` → green (format-check, lint, tests all ok).

## Tool-call budget

Well under the ~20 ceiling; all 4 criteria + sanity check + diff checks
exercised directly.
