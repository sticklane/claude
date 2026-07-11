# Verification: 01-reprime-label

Verdict: PASS

## Criterion 1 — four-case fixture test exists and passes

Command:
```
cd agentprof && go test ./internal/claude/
```
Output:
```
ok  	github.com/sticklane/agentprof/internal/claude	(cached)
```

Confirmed test `TestCollectMarksReprimeOnlyOnMidSessionMainLoopCallsAboveThreshold`
in `agentprof/internal/claude/claude_test.go` (lines 677-705) built on fixture
`writeReprimeFixture` (lines 643-666) exercises all four required cases in one
run, each with its own assertion:
- main loop's first call, >50k cache write → asserts NOT marked (`first` stack, line 689-692)
- mid-session main-loop call, >50k → asserts marked `reprime=true` (`mid` stack, line 693-696)
- later main-loop call, <50k (sub-threshold) → asserts NOT marked (`sub` stack, line 697-700)
- subagent's first call, >50k, same session → asserts NOT marked (`agent` stack, line 701-704)

A second test, `TestCollectReprimeThresholdZeroDisablesLabel` (lines 707-720),
confirms `--reprime-threshold 0` disables labeling on the same fixture.
`go test -run Reprime -v` output:
```
=== RUN   TestCollectMarksReprimeOnlyOnMidSessionMainLoopCallsAboveThreshold
--- PASS: TestCollectMarksReprimeOnlyOnMidSessionMainLoopCallsAboveThreshold (0.00s)
=== RUN   TestCollectReprimeThresholdZeroDisablesLabel
--- PASS: TestCollectReprimeThresholdZeroDisablesLabel (0.00s)
PASS
ok  	github.com/sticklane/agentprof/internal/claude	0.203s
```

Result: PASS

## Criterion 2 — flag documented in --help

Command:
```
cd agentprof && go run . claude --help 2>&1 | grep -q reprime-threshold
```
Exit: success (grep found match). Actual help text:
```
  -reprime-threshold int
    	cache_write_tokens above which a non-first main-loop call is labeled reprime=true (0 disables) (default 50000)
```

Result: PASS

## Criterion 3 — scripts/check.sh green

Command:
```
cd agentprof && bash scripts/check.sh
```
Output:
```
check: format-check ok
check: lint ok
check: tests ok
```

Result: PASS

## Touch scope check

Command:
```
git diff 5b5950943677c5f738ce841511258155ac6511ce --stat
```
Output:
```
 agentprof/cmd_claude.go                  |  3 +-
 agentprof/internal/claude/claude.go      | 33 ++++++++++--
 agentprof/internal/claude/claude_test.go | 88 ++++++++++++++++++++++++++++++++
 3 files changed, 118 insertions(+), 6 deletions(-)
```
All three files fall within Touch scope (`agentprof/internal/claude/`,
`agentprof/cmd_claude.go`). No changes to `internal/costsummary/`,
`agent-console/`, `SCHEMA.md`, or `README.md`. No scope creep found.
`agentprof/testdata/` untouched, which is fine — Touch is permissive, not
mandatory.

## Task-file append-only check

Command:
```
git diff 5b5950943677c5f738ce841511258155ac6511ce -- specs/cache-reprime-visibility/tasks/01-reprime-label.md
```
Output: empty (no diff) — the task file has not been modified since the base
commit (Status still reads "in-progress", no checkboxes ticked). This is
explicitly permitted per the verification instructions ("the task file may
not yet be updated with ticks — that's fine, close-out happens after you
verify"). No violation.

## Overfitting check

The fixture uses generic labels (alpha/bravo/charlie, session "sess-z", agent
"agent-S") rather than literal values baked into the implementation. Read
`internal/claude/claude.go` diff logic: threshold comparison and "first
main-loop call per transcript" tracking are general (not special-cased to
fixture values). Did not find hard-coded fixture-specific branches.

## Overall verdict: PASS
