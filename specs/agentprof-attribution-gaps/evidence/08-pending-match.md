# Evidence: 08 — pending from tool_result on meta/sidechain line

## The bug

`parseTranscript` in `agentprof/internal/claude/claude.go` handled `"user"`
lines by skipping any `isMeta`/`isSidechain` line **before** it populated the
tool-result set (`p.toolResults`). An Agent-tool / Task result frequently
lands on exactly such a line, so the originating `tool_use` was never matched
and got counted `pending` — the mechanical source suspected behind the
~8,854 pending-sample volume in the original report.

Old order (pre-fix):

```go
if l.IsMeta || l.IsSidechain {
    continue          // <- skipped before matching
}
if ids := toolResultIDs(l.Message.Content); len(ids) > 0 { ... }
```

## The fix

Hoist the tool-result matching **above** the `isMeta`/`isSidechain` skip so
results on those lines still match their `tool_use`. The `prevTs` model-call
duration anchor still advances only on non-skipped lines, preserving existing
duration semantics.

- Fix commit: `a7e68e9` (fix), `<prev>` test commit; base `6858d9f`.
- Changed: `agentprof/internal/claude/claude.go` (matching order), new test
  `agentprof/internal/claude/meta_sidechain_match_test.go`.

## Hermetic reproduction (in-repo, runs anywhere)

`TestToolResultOnMetaOrSidechainLineMatchesToolUse` builds a transcript where
`tu1`'s `tool_result` arrives on an `isMeta` (and, as a subtest, `isSidechain`)
user line. Pre-fix behavior is demonstrated by construction: the test committed
at the RED step observed `Stats.Pending = 1` and one `tool:(pending)` sample
for BOTH flags; after the fix the pending count drops to `0` and no
`tool:(pending)` sample is emitted.

```
cd agentprof && go test ./internal/claude/ -run TestToolResultOnMetaOrSidechainLineMatchesToolUse -v
```

## Real-window before/after measurement — MANUAL-PENDING

Not runnable in an isolated worktree: it needs real `~/.claude` transcript
data (absent from the worktree; `docs/memory/unattended-worker-tool-limits.md`).
The `claude` subcommand prints the parse-stat as
`N unmatched tool call(s) <disposition>` on stderr. To measure the drop on
real data, run the same command against `$HOME/.claude` at the pre-fix base and
at the fix commit and diff the counts:

```
# from the agentprof module directory:
cd agentprof

# BEFORE (base, pre-fix):
git checkout 6858d9f -- internal/claude/claude.go
go run . claude --claude-dir "$HOME/.claude" >/dev/null 2>pending_before.txt
grep 'unmatched tool call' pending_before.txt

# AFTER (fix):
git checkout a7e68e9 -- internal/claude/claude.go
go run . claude --claude-dir "$HOME/.claude" >/dev/null 2>pending_after.txt
grep 'unmatched tool call' pending_after.txt
```

Expected: the AFTER count is materially lower than BEFORE (hypothesis: the
Agent-tool / TaskOutput result shapes that were landing on meta/sidechain lines
now match). Record both numbers here when run attended/post-merge.

Result (attended run): MANUAL-PENDING — not yet run against real data.
