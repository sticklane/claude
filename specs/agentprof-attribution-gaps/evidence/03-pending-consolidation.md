# Verification: Task 03 — pending consolidation

Verdict: PASS

## Criterion 1: `cd agentprof && go test ./internal/claude/` passes

Command run: `cd agentprof && go test ./internal/claude/... -v`
Result: PASS — all 38 tests pass, including:
- TestPendingToolUseConsolidatesWithCount
- TestUnmatchedToolCallsConsolidateIntoOnePendingSample
- TestConsolidatedPendingHasNoEmptyValuesSamples
- TestKeepPendingPreservesPerCallEmptyValuedSamples
- TestPendingParseStatCountsUnmatchedCalls
- TestMatchedCallsAreNotCountedPending
- TestCollectTotalsMatchExpectedFixtureData (asserts pending_calls: 2 in fixture totals)

`ok github.com/sticklane/agentprof/internal/claude 0.208s`

(Note: `go test ./internal/claude/` from the worktree root fails with "directory
prefix internal/claude does not contain main module" because the Go module
root is `agentprof/`; the criterion's literal `cd agentprof && ...` form
works correctly and is what was run above.)

## Criterion 2: evidence/03-pending-volume.md

File exists at `specs/agentprof-attribution-gaps/evidence/03-pending-volume.md`.
Verified content:
- (a) Documents the consolidation mechanism (toolSamples returns
  ([]Sample, int); Options{KeepPending}; Stats{Pending}).
- (b) Reachable fixture-based before/after table: "empty-values tool:(pending)
  samples" before=2 (per-call/--keep-pending) → after=0 (default
  consolidation), backed by TestConsolidatedPendingHasNoEmptyValuesSamples and
  TestCollectTotalsMatchExpectedFixtureData (pending_calls: 2 in totals).
- (c) Gives exact runnable manual-pending commands for the 14-day-window
  before/after count (using `git worktree add` against b4971fe for "before"
  and this branch for "after", counting jsonl lines and pending-tagged
  samples) and for the Agent-tool/TaskOutput real-transcript shape
  investigation (jq/grep pipeline against `$HOME/.claude/projects`).
- Correctly explains why the ≥8% total-sample drop cannot be reproduced from
  the fixture (fixture has 1-unmatched-call-per-response, so no response
  collapses N→1) and why the live 14-day numbers are unreachable from an
  isolated worktree.

Per the task instructions, criterion 2 is satisfied.

## Criterion 3: `bash agentprof/scripts/check.sh` is green

Command run: `bash agentprof/scripts/check.sh`
Output:
```
check: format-check ok
check: lint ok
check: tests ok
```
PASS.

## Consolidation behavior deep check (claude.go / pending_test.go / duration_test.go)

Read `agentprof/internal/claude/claude.go` diff against base b4971fe:
- `toolSamples` signature changed to
  `(r response) toolSamples(modelStack []string, results map[string]time.Time, sessionID, turn string, keepPending bool) ([]schema.Sample, int)`.
- Default path (keepPending=false): unmatched calls are counted (`pending++`)
  but NOT emitted per-call; after the loop, if `pending > 0 && !keepPending`,
  ONE `tool:(pending)` sample is appended carrying
  `Values: {"pending_calls": pending}` — matches "ONE tool:(pending) sample
  with pending_calls=<count>, not N empty-valued samples".
- `keepPending=true` path: each unmatched call appends its own
  `tool:(pending)` sample with an empty `Values{}` map — matches "Options.KeepPending
  preserves the per-call empty-valued emission".
- `Stats.Pending` is accumulated in `CollectWithOptions`/`session.collect`
  from the `int` (unmatched-call count) returned by `toolSamples` at both
  call sites (main-transcript and per-agent) — matches "Stats.Pending counts
  unmatched calls", verified independent of keepPending
  (TestPendingParseStatCountsUnmatchedCalls loops over both `false` and
  `true` and asserts `stats.Pending == 3` in both cases).
- `Collect` and `CollectWithReprime` keep their original signatures/behavior
  by delegating into `CollectWithOptions` — no existing test callsite needed
  to change except the two that assert exact pending-sample shape
  (`TestPendingToolUseHasEmptyValues` renamed/updated,
  `TestCollectTotalsMatchExpectedFixtureData` totals map gained
  `pending_calls: 2`), which is the expected/legitimate consequence of the
  behavior change the task describes, not test-weakening.

Read `pending_test.go`: 5 focused tests, each asserting one behavior
(3-in-one-turn consolidation with count, no empty-values samples under
consolidation, per-call preservation under KeepPending, Stats.Pending
counting under both modes, and a matched-call negative control). Fixtures
are generic (three arbitrary tool names/ids), not tuned to any specific
acceptance-check magic number beyond the task's own "3 unmatched calls"
example — no overfitting observed.

## Scope / Touch check

`git diff --stat b4971fe051c75e81f08d4b4b15917d2e549236ec HEAD`:
```
 agentprof/internal/claude/claude.go                | 126 +++++++++++++++------
 agentprof/internal/claude/claude_test.go           |   3 +
 agentprof/internal/claude/duration_test.go         |  15 ++-
 agentprof/internal/claude/pending_test.go          | 125 ++++++++++++++++++++
 .../tasks/03-pending-consolidation.md              |  18 +++
 5 files changed, 245 insertions(+), 42 deletions(-)
```
Plus untracked `specs/agentprof-attribution-gaps/evidence/03-pending-volume.md`
(new file under Touch's `specs/agentprof-attribution-gaps/evidence/`).

All changed paths are within Touch
(`agentprof/internal/claude/`, `agentprof/testdata/` [none touched, fine],
`specs/agentprof-attribution-gaps/evidence/`) plus the task's own file
(`specs/agentprof-attribution-gaps/tasks/03-pending-consolidation.md`).

`cmd_claude.go` confirmed NOT edited: `git diff --stat ... -- agentprof/cmd_claude.go`
returned empty, and `grep -n "KeepPending\|--keep-pending" cmd_claude.go`
returned no matches. The CLI flag is correctly deferred as Discovered/
out-of-Touch, exactly as the task's plan comment states.

No scope creep found.

## Append-only task-file check

`git diff b4971fe051c75e81f08d4b4b15917d2e549236ec HEAD -- 'specs/*/tasks/*.md'`
shows only an added `<!-- PLAN (delete at close-out): ... -->` HTML-comment
block inserted after the header fields and before `## Goal`. Goal, Touch,
Steps, and Acceptance section text are byte-identical to base. No other
task files were touched (only 03-pending-consolidation.md appears in the
diff). Status/checkboxes were NOT flipped to done in this diff (Status
still reads `in-progress` in the working tree) — this is fine per the
append-only contract (worker may flip its own Status/checkboxes; here it
simply hasn't yet, which is not a violation).

## Overall

PASS on all three acceptance criteria. No scope creep. No test overfitting
detected — the new tests exercise generic multi-call fixtures and the
existing fixture-based totals test was updated to reflect the new
(expected, task-specified) shape rather than weakened.
