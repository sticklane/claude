# Verification: task 02 — reprime + sessions summary sections

Verdict: PASS

## Acceptance criteria

1. `cd agentprof && go test ./internal/costsummary/`
   Command: `cd .../agentprof && go test ./internal/costsummary/ -v`
   Result: PASS — 13 tests, all green, including
   `TestBuildReprimeSectionCountsTokensCostAndByProject`,
   `TestBuildReprimeSectionEmptyWhenNoReprimeSamples`,
   `TestBuildSessionsSectionContextPercentilesMainLoopOnly`,
   `TestBuildSessionsSectionNonNilWhenEmpty`. ✓

2. `cd agentprof && go test ./...`
   Result: all 14 packages `ok` (costsummary, claude, merge, schema, etc). ✓

3. `bash agentprof/scripts/check.sh`
   Result: `check: format-check ok / check: lint ok / check: tests ok`. ✓

## Substantive checks

- **Reprime section**: `Reprime{Count, CacheWriteTokens, CostMicrousd, ByProject}`
  in costsummary.go:34-39; `reprimeRollup` (costsummary.go:93-110) only
  processes samples with `Labels["reprime"] == "true"`, skipping all others
  (verified by `TestBuildReprimeSectionCountsTokensCostAndByProject`, which
  includes a non-reprime-labeled high-cache-write sample and asserts it's
  excluded from the totals). ✓
- **Sessions section**: `SessionStat{Project, Calls, CostMicrousd, P50Ctx,
  P90Ctx}` (costsummary.go:46-52); `sessionStats` (costsummary.go:115-158)
  excludes samples with an `agent:` frame from ctx/percentile/calls/cost
  accumulation (`agentType(smp.Stack)` check at line 130), computing
  percentiles only over main-loop samples. Test
  `TestBuildSessionsSectionContextPercentilesMainLoopOnly` includes an
  `agentCall` sharing the same session label with a huge ctx value (9999)
  and asserts it is excluded from p50/p90/calls/cost — the percentile math
  (nearest-rank) is exercised against hand-computed values, not just
  literal echoes of the implementation. ✓
- **Backward compat**: existing `Summary` fields (`ByProject`, `BySkill`,
  `ByAgentType`, `ByModel`, `Totals`, `SessionsAdded`) are unchanged in name
  and JSON tag; `Reprime` and `Sessions` are pure additions. All 6
  pre-existing grouping/totals tests still pass unmodified. ✓
- **Merge-mode aggregation**: `TestBuildGroupingFromMergedWhileSessionsAddedFromFreshOnly`
  confirms `Reprime`/`Sessions`/`Totals` are computed over `forGrouping`
  (the merged rolling window), while `SessionsAdded` uses `fresh` only —
  matching the Touch-scope contract about `--merge` aggregation. ✓

## Scope / Touch compliance

`git diff <base> --name-only` → only:
- `agentprof/internal/costsummary/costsummary.go`
- `agentprof/internal/costsummary/costsummary_test.go`

No changes to `internal/claude/`, `agent-console/`, `cmd_claude.go`, or
docs. No `testdata/` changes (optional, not required).

## Task-file append-only check

`git diff <base> -- '*/tasks/*.md'` → empty (zero diff). The task file's
Status line is still `in-progress` and no acceptance checkboxes are ticked
— worker has not yet marked completion, but this means no violation of the
append-only contract either (nothing was appended). No `## Progress` or
`## Deferred questions` section was added.

## Test-overfitting check

Test fixtures (`reprimeSample`, `mainCall`, `agentCall`, `groupingFixture`)
build realistic multi-sample scenarios (mixed sessions, mixed agent/main
frames, mixed reprime labels) and assert derived/computed values (sums,
percentiles) rather than hard-coded pass-through of exact implementation
internals. No test file appears tuned to a narrow special case; varying
inputs (e.g. different session labels/costs) would still exercise the same
logic paths correctly.
