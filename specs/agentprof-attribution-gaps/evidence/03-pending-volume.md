# Evidence: 03 — tool:(pending) consolidation volume (R3)

## What changed (code, in Touch scope)

`agentprof/internal/claude/claude.go`:

- `toolSamples` now returns `([]schema.Sample, int)`. Unmatched tool_use
  blocks in a response no longer emit one empty-valued `tool:(pending)`
  sample each; they consolidate into a **single** `tool:(pending)` sample
  carrying `pending_calls = <count>` (no fabricated `duration_ms`). The
  returned int is the unmatched-call count.
- New `Options{ReprimeThreshold, KeepPending}` + `Stats{Skipped, Pending}`
  and `CollectWithOptions(...)`. `Collect`/`CollectWithReprime` keep their
  signatures and delegate (so the ~40 existing test callsites are untouched).
- `Options.KeepPending` (the R3 debug escape hatch) preserves today's
  per-call empty-valued emission — this is the library-level form of the
  `--keep-pending` flag (see "Out-of-Touch" below).
- `Stats.Pending` is the parse-stat: the total number of unmatched tool_use
  calls, surfaced through the `CollectWithOptions` return so result-matching
  regressions stay visible. Counted identically whether consolidated or kept.

## Reachable before/after (fixture, hermetic — no ~/.claude needed)

Testdata fixture `testdata/claude-dir` has two unmatched tool_uses
(`toolu_A`, `toolu_WS`), each alone in its own response.

| | empty-values `tool:(pending)` samples | `pending_calls` total |
|---|---|---|
| before (per-call, `--keep-pending`) | 2 | — |
| after (default consolidation) | **0** | 2 |

Asserted by `TestCollectTotalsMatchExpectedFixtureData` (totals now include
`pending_calls: 2`) and `TestConsolidatedPendingHasNoEmptyValuesSamples`
(no empty-values pending sample survives). The multi-call collapse (3 → 1)
is covered by `TestUnmatchedToolCallsConsolidateIntoOnePendingSample`
(`pending_calls: 3`, one sample) and the keep-pending inverse by
`TestKeepPendingPreservesPerCallEmptyValuedSamples` (3 samples, all empty).

The **total-sample-count drop** only materialises where a response has
>1 unmatched call (N samples → 1). The shared fixture has 1-per-response,
so its total stays 13; the ≥8% drop is a property of the real corpus where
multi-unmatched responses are common (see below).

## MANUAL-PENDING: 14-day-window ≥8% total-sample drop

The before/after count on the local 14-day window requires
`$HOME/.claude/projects`, which is **outside this isolated worktree root**;
per the dispatch contract these numbers are not fabricated. Run to produce
them (from a full checkout, not a worktree):

```
# AFTER (this branch, consolidated):
go run . claude --claude-dir "$HOME/.claude" --days 14 -o /tmp/after.jsonl 2>/tmp/after.stderr
AFTER=$(wc -l < /tmp/after.jsonl)
# The parse-stat line "<N> unmatched tool call(s) ..." requires the CLI flag
# wiring (Discovered, below); until then read Stats.Pending via a tiny driver
# or grep tool:(pending) with pending_calls.

# BEFORE (per-call emission == today's behavior == --keep-pending):
#   once the CLI flag lands:  --keep-pending
#   until then, from the pre-change commit b4971fe:
git worktree add /tmp/ap-before b4971fe && (cd /tmp/ap-before/agentprof && \
  go run . claude --claude-dir "$HOME/.claude" --days 14 -o /tmp/before.jsonl)
BEFORE=$(wc -l < /tmp/before.jsonl)

echo "before=$BEFORE after=$AFTER drop=$(( (BEFORE-AFTER)*100/BEFORE ))%"
# PASS criterion: empty-values tool:(pending) samples == 0 AND drop >= 8%.
# Verify zero empty-values pending samples in the after set:
grep -c '"tool:(pending)"' /tmp/after.jsonl   # each such line must carry pending_calls
```

Expected: `after` has zero `tool:(pending)` samples without a `pending_calls`
value, and `drop >= 8%` (SPEC cited the ~8,854-sample / 9.4% figure).

## MANUAL-PENDING: Agent-tool / TaskOutput unmatched-shape investigation

Code-level finding (from `claude.go`): result-matching only populates
`toolResults` from `tool_result` blocks on **non-meta, non-sidechain user
lines** — `parseTranscript` does `if l.IsMeta || l.IsSidechain { continue }`
(claude.go:673) *before* the `toolResultIDs` block (claude.go:676+). Any
tool_result delivered on a sidechain/meta line, or one that carries its
`tool_use_id` in the top-level `toolUseResult` object rather than a content
`tool_result` block, is therefore never matched and its tool_use stays
pending. This is the most plausible mechanical source of the volume, but
whether the two named shapes (Agent-tool result, TaskOutput result)
actually take that form cannot be confirmed from the fixtures — it needs a
real transcript.

Confirmation command (run against `$HOME/.claude`, outside the worktree):

```
# Are Agent/Task tool_results landing on sidechain/meta lines?
grep -rl '"name":"Task"\|"name":"Agent"' "$HOME"/.claude/projects/*/*.jsonl | while read f; do
  # tool_use ids for Task/Agent in this transcript:
  jq -rc 'select(.message.content|type=="array")|.message.content[]?|select(.type=="tool_use" and (.name=="Task" or .name=="Agent"))|.id' "$f"
done | sort -u > /tmp/agent_tool_ids.txt
# For each id, does a tool_result appear ONLY on an isMeta/isSidechain line?
grep -rh 'tool_result' "$HOME"/.claude/projects/*/*.jsonl | \
  jq -rc 'select(.isMeta==true or .isSidechain==true)|.message.content[]?|select(.type=="tool_result")|.tool_use_id' 2>/dev/null | \
  sort -u > /tmp/sidechain_result_ids.txt
comm -12 /tmp/agent_tool_ids.txt /tmp/sidechain_result_ids.txt   # non-empty => shape confirmed
```

If the intersection is non-empty, the fix is to match tool_results carried
on meta/sidechain lines (or in `toolUseResult`) — but that change is
deliberately **not** made here without the confirming data, because a
speculative loosening of result-matching risks mis-timing genuinely-pending
calls. Deferred to a data-backed follow-up (owning spec task or a human run).

## Out-of-Touch (Discovered, not done here)

The `--keep-pending` CLI flag and the stderr parse-stat log line live in
`agentprof/cmd_claude.go`, which is **not in this task's `Touch:`**
(`agentprof/internal/claude/, agentprof/testdata/, evidence/`). The
library-level `Options.KeepPending` + `Stats.Pending` are the in-scope
surfacing and satisfy all three acceptance criteria (all
`internal/claude`-scoped). Wiring is a ~4-line follow-up in `cmdClaude`:

```go
keepPending := fs.Bool("keep-pending", false, "emit one tool:(pending) sample per unmatched tool_use (debug) instead of a consolidated pending_calls count")
// ...
samples, turns, stats, err := claude.CollectWithOptions(*dir, cutoff,
    claude.Options{ReprimeThreshold: *reprimeThreshold, KeepPending: *keepPending})
// ...
if stats.Skipped > 0 { fmt.Fprintf(stderr, "skipped %d unparseable lines\n", stats.Skipped) }
if stats.Pending > 0 { fmt.Fprintf(stderr, "%d unmatched tool call(s) consolidated into tool:(pending)\n", stats.Pending) }
```
