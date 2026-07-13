Verdict: PASS (with one scope-creep finding, non-blocking)

## Acceptance commands (run in agentprof/)

1. `go test ./...` -> all packages `ok` (claude, pprofenc, etc.) — PASS
2. `go test ./... -run 'Pending'` -> `--- PASS: TestPendingToolUseHasEmptyValues` — PASS
3. `go test ./... -run 'Duration'` -> `--- PASS: TestToolCallSampleReportsExactDuration`,
   `TestToolCallDurationClampsNegativeDeltaToZero`, `TestModelCallDurationOmitsFirstAndMeasuresRest`,
   `TestModelCallDurationSpansInterveningToolResult` — PASS
4. `gofmt -l . | wc -l` -> `0` — PASS

## Code-level criteria

- R1 (tool sample id-matched, sibling leaf `tool:<name>`, duration_ms=clamp0(result_ts-use_ts),
  negative clamps to 0): `internal/claude/claude.go` toolSamples()/clamp0 (~line 812-830) and
  duration_test.go TestToolCallSampleReportsExactDuration / TestToolCallDurationClampsNegativeDeltaToZero
  exercise exactly this against parsed `[]schema.Sample`. Verified — leaf is `tool:Bash` sibling
  to `main`, not nested under model leaf; negative-delta test asserts exactly 0. PASS.
- R2 (unresolved tool_use -> `tool:(pending)`, empty Values, no fabricated duration_ms):
  claude.go ~line 826 (`leaf := "tool:(pending)"`, no `values["duration_ms"]` set when no match);
  TestPendingToolUseHasEmptyValues asserts `len(got[0].Values) == 0`. PASS.
- R3 (model-call duration_ms = clamp0(this_ts - prevTs), prevTs = previous parser-captured line
  (deduped assistant OR tool_result-carrying user line), first sample per transcript omits it,
  skipped lines never "previous"): claude.go ~line 478-584 tracks `prevTs`/`hasPrev` across
  collect(), sets `r.durationMs, r.hasDuration = clamp0(ts.Sub(prevTs)), true` only when
  `hasPrev`. Tests TestModelCallDurationOmitsFirstAndMeasuresRest and
  TestModelCallDurationSpansInterveningToolResult both pass and specifically test the
  first-sample-omission and the tool_result-as-previous-line cases. PASS.
- R7 Values half (no existing Values key removed/altered, only duration_ms added): diff of
  `testdata/claude-dir.expected.json` (2a33239..HEAD) shows only additions — `total_duration_ms`
  key added, 3 new tool: stacks added, existing keys (cost_microusd, tokens, etc.) unchanged in
  value. `internal/pprofenc/pprofenc.go` diff only adds a case for `duration_ms` -> milliseconds
  unit, does not touch existing `wall_ms`/`cost_microusd` handling. PASS.

## Append-only task-file check

`git diff 2a332399a1dfb85bdf8cf0dfaa86c7151db1c9b1 -- specs/agentprof-instrumentation/tasks/01-tool-and-model-durations.md`
shows only the insertion of the `<!-- PLAN (delete at close-out) -->` comment block; no
Status/checkbox/Goal/Steps/Touch/criteria text was altered (Status is still "in-progress",
checkboxes unticked at time of verification — consistent with "verify before close-out"). PASS
(append-only respected; per instructions do not fail on plan-block presence).

## Touch discipline

Task's `Touch:` header is `agentprof/internal/, agentprof/testdata/`. Files actually changed
(vs base 2a33239):
- agentprof/internal/claude/claude.go — OK (internal/)
- agentprof/internal/claude/claude_test.go — OK (internal/)
- agentprof/internal/claude/duration_test.go — OK (internal/, new)
- agentprof/internal/pprofenc/pprofenc.go — OK (internal/)
- agentprof/testdata/claude-dir.expected.json — OK (testdata/)
- specs/agentprof-instrumentation/tasks/01-tool-and-model-durations.md — OK (task file itself,
  always allowed)
- **agentprof/cmd_claude_test.go — OUTSIDE Touch.** This file lives at the agentprof/ package
  root, not under `agentprof/internal/` or `agentprof/testdata/`. The task's own PLAN comment
  block explicitly calls out this exact edit ("cmd_claude_test.go 10→13") but the Touch header
  itself was never widened to include it. This is a **Touch violation** — a small, low-risk one
  (a sample-count assertion bumped 10->13 to match new tool: samples, required for `go test ./...`
  to pass), but it is a file edit outside the declared Touch list and should be flagged as
  scope creep / Touch-header drift for drain to reconcile (either the Touch header should have
  listed `agentprof/cmd_claude_test.go` explicitly, or the file should not have needed touching).

## Scope-creep / other findings

- No other files outside Touch + task file were modified by this work (git diff --stat confirmed
  only the 7 files above changed vs base).
- No marker (`role:`/`stage:`) handling was added — confirmed absent from claude.go diff,
  consistent with the Touch note reserving that for task 02.

## Summary

All 4 runnable acceptance commands pass; R1/R2/R3/R7(Values) are correctly implemented and
covered by targeted tests that exercise the exact scenarios (known delta, negative-delta clamp,
pending/empty-Values, first-sample-omission, tool_result-as-previous-line). One Touch-scope
finding (cmd_claude_test.go edited outside the declared Touch list) — flagged but not required
to fail the task given it's a minimal, test-only, spec-necessary fixture-count bump acknowledged
in the task's own plan block.
