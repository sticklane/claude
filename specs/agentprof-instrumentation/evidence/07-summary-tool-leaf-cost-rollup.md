# Verification: 07-summary-tool-leaf-cost-rollup

Verdict: PASS

## Criterion 1: `cd agentprof && go test ./... -run Summary`

Command: `go test ./... -run Summary -v`
Result: PASS. All 5 tests in package pass, including
`TestClaudeSummaryExcludesToolLeafRows` (new).

Red-first confirmed: stashed the uncommitted `summary.go` fix (leaving only
the committed test from `ab01ae7`) and re-ran the new test alone — it failed
for the right reason:

```
summary_test.go:107: summary row model = "tool:(pending)": tool:/pending leaf
frames must not key a cost rollup row (task 07)
summary_test.go:107: summary row model = "tool:Workflow": ...
--- FAIL: TestClaudeSummaryExcludesToolLeafRows (0.00s)
```

Restored the stash; re-ran full suite — green again.

## Criterion 2: `cd agentprof && bash scripts/check.sh`

Command: `bash scripts/check.sh`
Output:

```
check: format-check ok
check: lint ok
check: tests ok
```

Exit code: 0.

## (a) Touch confinement

`git diff <base> --stat` → only `agentprof/summary.go` (+18/-1) and
`agentprof/summary_test.go` (+10) changed. Matches the task's `Touch:`
list exactly. No other files modified.

## (b) Grouping change mirrors costsummary's marker set, does not relabel

`summary.go`'s new `isMarkerLeaf` checks `tool:`/`role:`/`stage:` prefixes —
the identical marker set to `internal/costsummary/costsummary.go`'s
`modelLeaf` (verified by grep, same three `strings.HasPrefix` checks).

Deviation checked deliberately: `costsummary.modelLeaf` walks backward
through the whole stack looking for a non-marker frame to use as a
substitute model label. `summary.go` instead only checks the immediate
leaf and `continue`s (drops the sample from the rollup) when it is a
marker — it does NOT walk back. This is correct per the task's own
criterion (b), which explicitly forbids the walk-back behavior producing
a `model="main"` row: `toolSamples` (internal/claude/claude.go:857-875)
constructs a tool sample's stack by _replacing_ the model-name leaf with
`tool:<name>`, so the frame preceding a tool leaf is a stage frame (e.g.
`"main"`), never a model name. Walking back would therefore fold tool
samples into a bogus `model="main"` row — exactly what (b) prohibits.
Dropping the sample (current implementation) is the only choice
consistent with both (b)'s prohibition and the task's Answers decision
("EXCLUDE tool/pending leaves from the summary rollup").

## (c) `go run . claude --claude-dir testdata/claude-dir -o summary` output

Command: `go run . claude --claude-dir testdata/claude-dir -o summary`
Output (stderr: "skipped 1 unparseable lines"; stdout JSON array):
6 rows, sessions sess-0001/sess-0002, models: claude-fable-5,
claude-haiku-4-5, `<synthetic>`, claude-sonnet-4-5, mystery-model-9.
No row's model starts with `tool:`. No spurious `model="main"` row either.

## Task-file append-only check

`git diff 82818fcf76dc908b1c809007fffb8a7fdcb4a65f -- specs/agentprof-instrumentation/tasks/07-summary-tool-leaf-cost-rollup.md`
→ empty (no diff at all). Status still reads `in-progress`, acceptance
checkboxes unticked, no evidence-citation line added by the worker. Not a
violation of the append-only rule (nothing was changed), but it does mean
the worker has not yet recorded completion in the task file — flagged for
the caller's attention since the code-level work is otherwise complete and
green.

## Scope creep

None found. Diff is exactly `summary.go` (new `isMarkerLeaf` helper + one
`continue` branch in `summarize`) and `summary_test.go` (one new test).
Test fixture (`testdata/claude-dir`) predates this task (last touched in
task 04) and was not modified — no overfitting to fabricated data.

## Gates

`bash scripts/check.sh` → exit 0 (format-check, lint, tests all ok).
