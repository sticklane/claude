# Verification: Task 08 — pending-match meta/sidechain investigation

Verdict: PASS

Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-a343d2d04ac6213f0
Base for task-file diff: 6858d9f
HEAD at verification: 4f7d1a0 (docs: record task 08 fix + MANUAL-PENDING real-window measurement)

## Criterion 1 — `go test ./internal/claude/` passes, new fixture present

Command:
```
cd agentprof && go test ./internal/claude/ -run TestToolResultOnMetaOrSidechainLineMatchesToolUse -v
```
Output (tail):
```
=== RUN   TestToolResultOnMetaOrSidechainLineMatchesToolUse
=== RUN   TestToolResultOnMetaOrSidechainLineMatchesToolUse/isMeta
=== RUN   TestToolResultOnMetaOrSidechainLineMatchesToolUse/isSidechain
--- PASS: TestToolResultOnMetaOrSidechainLineMatchesToolUse (0.00s)
    --- PASS: .../isMeta (0.00s)
    --- PASS: .../isSidechain (0.00s)
PASS
ok  	github.com/sticklane/agentprof/internal/claude	0.143s
```
Full `go test ./internal/claude/` also passes (cached ok).

File `agentprof/internal/claude/meta_sidechain_match_test.go` exists, defines
`TestToolResultOnMetaOrSidechainLineMatchesToolUse`, asserts
`stats.Pending != 0` fails (i.e. requires 0) and `len(pendingSamples(samples)) != 0`
fails (requires 0 tool:(pending) samples), subtested for both `isMeta` and
`isSidechain` flags.

**Pre-fix reproduction (scratch copy, not committed to the tracked tree):**
copied `agentprof/` to a scratchpad dir, replaced only
`internal/claude/claude.go` with the version at base commit `6858d9f`
(`git show 6858d9f:agentprof/internal/claude/claude.go`), and reran the new
test in that scratch copy:
```
--- FAIL: TestToolResultOnMetaOrSidechainLineMatchesToolUse (0.00s)
    meta_sidechain_match_test.go:38: Stats.Pending = 1, want 0 (a tool_result on a isMeta line should match its tool_use)
    meta_sidechain_match_test.go:41: got 1 tool:(pending) samples, want 0 (isMeta result should match): [...tool:(pending)]
    --- FAIL: .../isMeta (0.00s)
    meta_sidechain_match_test.go:38: Stats.Pending = 1, want 0 (a tool_result on a isSidechain line should match its tool_use)
    --- FAIL: .../isSidechain (0.00s)
FAIL
```
This confirms the test genuinely reproduces the bug and the fix (in
`claude.go`'s `parseTranscript` "user" case, hoisting tool_result matching
above the `IsMeta`/`IsSidechain` skip — confirmed by reading the diff below)
is what makes it pass. Scratch copy was deleted afterward; the real worktree
was never touched by this reproduction (`git status --porcelain` empty
throughout and after).

Verdict: PASS

## Criterion 2 — evidence/08-pending-match.md

`specs/agentprof-attribution-gaps/evidence/08-pending-match.md` exists and
records: the bug (matching-order skip losing results on meta/sidechain
lines), the fix (hoist matching above the skip, `prevTs` semantics
preserved), and the real-window measurement as MANUAL-PENDING with the exact
command:
```
cd agentprof
git checkout 6858d9f -- internal/claude/claude.go
go run . claude --claude-dir "$HOME/.claude" >/dev/null 2>pending_before.txt
grep 'unmatched tool call' pending_before.txt
git checkout a7e68e9 -- internal/claude/claude.go
go run . claude --claude-dir "$HOME/.claude" >/dev/null 2>pending_after.txt
grep 'unmatched tool call' pending_after.txt
```
Result line: "MANUAL-PENDING — not yet run against real data." Correctly
left unresolved since this worktree has no `$HOME/.claude` real transcript
access.

Verdict: PASS

## Criterion 3 — `go test ./...` and `scripts/check.sh`

Commands:
```
cd agentprof && go test ./...
bash agentprof/scripts/check.sh
```
Output:
```
ok  	github.com/sticklane/agentprof	(cached)
ok  	github.com/sticklane/agentprof/internal/antigravity	(cached)
ok  	github.com/sticklane/agentprof/internal/bqtime	(cached)
ok  	github.com/sticklane/agentprof/internal/claude	(cached)
... (all packages ok)
check: format-check ok
check: lint ok
check: tests ok
```
Verdict: PASS

## Task-file append-only check

```
git diff 6858d9f -- 'specs/agentprof-attribution-gaps/tasks/*.md'
```
→ empty (0 bytes). Task file `08-pending-match-meta-sidechain-investigation.md`
is byte-identical to base; Status line still reads `in-progress` (not yet
flipped to done), which matches the expectation that the task file has not
been updated yet. No forbidden edits present (there are also no edits at
all yet, which is fine — nothing to flag).

## Scope-creep check

```
git diff 6858d9f --stat
```
```
 agentprof/internal/claude/claude.go                | 15 +++--
 .../internal/claude/meta_sidechain_match_test.go   | 45 +++++++++++++
 .../evidence/08-pending-match.md                   | 73 ++++++++++++++++++++++
 3 files changed, 129 insertions(+), 4 deletions(-)
```
All three changed files fall within the task's `Touch:` list
(`agentprof/internal/claude/`, `specs/agentprof-attribution-gaps/evidence/`).
The `claude.go` diff is minimal and precisely targeted: hoists the
`toolResultIDs` matching block above the `IsMeta`/`IsSidechain` `continue`,
and correctly guards the `prevTs, hasPrev = ts, true` duration-anchor update
with `if !l.IsMeta && !l.IsSidechain` so pre-existing duration semantics are
preserved (matching only added for pending-count purposes, not the
duration anchor). No unrelated files touched. No scope creep found.

## Overfitting check

The fix is a general reordering of matching logic in `parseTranscript`, not
a special case keyed to test-fixture literals (`tu1`, `sess-z`, etc.) — it
changes behavior for any transcript where a tool_result appears on a
meta/sidechain line, which is exactly the class of bug described in the
Original report. Not overfit to the exact test inputs.

## Overall verdict: PASS

Working tree is clean (`git status --porcelain` empty) after all
verification steps; no tracked file was left modified.
