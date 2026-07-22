# Verification: task 04 — agentprof per-session ctx adoption telemetry

Verdict: PASS

## Criteria

1. `cd agentprof && go test ./...` → exit 0, including new tests covering the
   three fixture cases.
   - Ran `go test -count=1 ./...` (uncached). All 16 packages `ok`.
   - New tests found: `internal/claude/ctx_usage_test.go`
     (`TestCollectCountsCtxUsageForIndexedRepoSession`,
     `TestCollectExcludesCtxUsageForNonIndexedRepoSession`) and
     `internal/costsummary/costsummary_test.go`
     (`TestBuildSessionsSectionSurfacesCtxUsage`). All pass individually with
     `-v`.
   - Evidence: ✓ PASS (L2 — behavioral: Collect()/Build() invoked, struct
     fields asserted).

2. `cd agentprof && go vet ./...` → exit 0.
   - Ran; no output, exit 0. ✓ PASS.

3. Report output over the fixture shows the ctx metric field, asserted by
   parsing report structure (not exact strings).
   - `costsummary.SessionStat.CtxUsage int64 \`json:"ctx_usage"\`` field added
     (agentprof/internal/costsummary/costsummary.go).
   - `TestBuildSessionsSectionSurfacesCtxUsage` calls `Build(samples, nil)`
     and asserts `s.Sessions["s1"].CtxUsage == 3` / `s.Sessions["s2"].CtxUsage
     == 0` via the Go struct (no string matching), and asserts `ctx_usage` is
     absent from `Totals`/`BySkill`/`ByProject` maps.
   - Evidence: ✓ PASS (L2 — behavioral, struct-level assertion).

## Fixture-case exercise (independent check)

- (a) Indexed-repo session, 2 Bash `ctx tree`/`ctx refs` + 1 `agentic:ctx`
  Skill call = 3: `ctxSessionDir` fixture in `ctx_usage_test.go` builds
  exactly this transcript;
  `TestCollectCountsCtxUsageForIndexedRepoSession` asserts `ctx_usage == 3`.
  Ran in isolation — PASS.
- (b) Non-indexed-repo session, same shapes, excluded (0):
  `TestCollectExcludesCtxUsageForNonIndexedRepoSession` reuses the same
  fixture builder with a `t.TempDir()` that has no `.context/`, asserts
  `ctx_usage == 0`. Ran in isolation — PASS.
- (c) `ctx` as a substring only (`getExecutionCtx` grep) not counted: the
  same fixture's 4th tool call is `grep -rn getExecutionCtx .`; the total
  asserted is 3, not 4, so if the substring were (wrongly) counted the test
  would fail.
  **Mutation check performed**: temporarily replaced
  `ctxBashRe` in `internal/claude/ctx_usage.go` with a case-insensitive bare
  `ctx` substring regex (`(?i)ctx`), reran
  `TestCollectCountsCtxUsageForIndexedRepoSession` — it FAILED
  (`ctx_usage = 4, want 3`), confirming the substring-exclusion assertion is
  live, not vacuous. File was restored from a copy taken before the mutation
  (not via `git checkout`); `git diff` on the file post-restore is empty and
  `go test -count=1 ./internal/claude/...` passes again.

All three fixture cases are genuinely exercised, not vacuous.

## Task-file append-only check

`git diff 1b53f0d2 -- specs/ctx-dispatch-adoption/tasks/04-agentprof-ctx-telemetry.md`
produces **no output** — the task file is byte-identical to the base commit
(Status still `in-progress`, no checkboxes ticked, no evidence lines added
yet). Nothing forbidden was altered because nothing was altered at all; this
matches the task instructions' note that the Status flip/checkbox ticks may
not be committed yet.

## Scope / Touch check

`git diff 1b53f0d2..HEAD --stat` (implementation commits `17069baf`,
`2f7c0fce`) touches only:
- `agentprof/SCHEMA.md`
- `agentprof/internal/claude/claude.go`
- `agentprof/internal/claude/ctx_usage.go` (new)
- `agentprof/internal/claude/ctx_usage_test.go` (new)
- `agentprof/internal/costsummary/costsummary.go`
- `agentprof/internal/costsummary/costsummary_test.go`

All under `agentprof/`, matching `Touch: agentprof/`. No skill files or
`plugin.json` touched, per the task's explicit prohibition. No scope creep
observed.

## TDD sequencing

Commit `17069baf` ("test: red for per-session ctx-usage telemetry") lands
tests only; `2f7c0fce` ("feat: per-session ctx-usage adoption telemetry")
lands the implementation. Correct red→green ordering by commit history
(not independently re-verified that 17069baf's tests failed at that commit,
but the sequencing and commit messages are consistent with TDD).

## Correctness notes

- Word-boundary regex: `(^|[\s;&|(])ctx[ \t]+(verb)\b` — correctly rejects
  `getExecutionCtx`-style substrings (verified live via mutation above) and
  the whole match still requires a following recognized verb.
- `ctx_usage` is deliberately excluded from `Totals`/`By*` rollups per the
  goal's "surfaces alongside the existing skill attribution" framing and is
  scoped to main-loop samples only (subagent samples excluded, tested in
  `TestBuildSessionsSectionSurfacesCtxUsage`).
- No regression: full `go test -count=1 ./...` and `go vet ./...` both clean
  after the mutation-and-restore cycle.

## Criteria-adequacy

- Criterion 1 (test suite green including 3 fixture cases): entailment
  confirmed — tests exercise `Collect()` end-to-end over realistic JSONL
  transcripts and assert numeric struct-field outcomes. Depth: L2
  (behavioral).
- Criterion 2 (`go vet` clean): mechanical gate, L1 (artifact-structure/
  static-analysis) — adequate for its narrow purpose.
- Criterion 3 (report structure carries the field, parsed not
  string-matched): confirmed via direct Go-struct field assertions on
  `Build()`'s return value. Depth: L2 (behavioral). Not L3 end-to-end (no
  CLI-level JSON-output round-trip test was found), but the criterion text
  only asks for structure-parsing over the fixture, which is satisfied.
