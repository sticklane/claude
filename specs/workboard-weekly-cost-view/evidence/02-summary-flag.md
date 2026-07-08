# Verification: Task 02 — agentprof claude --summary flag (R3)

Verdict: PASS

Repo: /Users/sjaconette/claude/.claude/worktrees/agent-add86baf6547a77de
Branch: task/02-summary-flag
Base commit for diff check: 6b0a47a4a769f578d616e42d0421a6aa60e20b2c

## Acceptance criteria

### 1. `cd agentprof && go test ./...` must pass

Command: `cd agentprof && go test ./...`

Output (tail):
```
ok  	github.com/sticklane/agentprof	(cached)
ok  	github.com/sticklane/agentprof/internal/bqtime	(cached)
ok  	github.com/sticklane/agentprof/internal/claude	(cached)
ok  	github.com/sticklane/agentprof/internal/costsummary	(cached)
ok  	github.com/sticklane/agentprof/internal/fixturegen	(cached)
ok  	github.com/sticklane/agentprof/internal/gcp	(cached)
ok  	github.com/sticklane/agentprof/internal/merge	(cached)
ok  	github.com/sticklane/agentprof/internal/naming	(cached)
ok  	github.com/sticklane/agentprof/internal/otel	(cached)
ok  	github.com/sticklane/agentprof/internal/output	(cached)
ok  	github.com/sticklane/agentprof/internal/pprofenc	(cached)
ok  	github.com/sticklane/agentprof/internal/pricing	(cached)
ok  	github.com/sticklane/agentprof/internal/schema	(cached)
ok  	github.com/sticklane/agentprof/internal/vertex	(cached)
```
Result: PASS.

Fixture coverage confirmed by reading
`agentprof/internal/costsummary/costsummary_test.go`:
- `TestBuildGroupsSamplesByProject/BySkill/ByAgentType/ByModel` +
  `TestBuildSumsTotalsAcrossAllSamples` — full grouped shape from a fixture
  with known project/skill/agent/model frames.
- `groupingFixture()` includes a 4th sample shaped `["proj",
  "(unlinked)", "agent:(unknown)", "claude-haiku-4-5"]` (no `skill:`/`(no
  skill)` frame at all). `TestBuildGroupsSamplesBySkill` asserts it lands
  in `by_skill["(no skill)"]` (700 = 300 explicit-no-skill + 400 unlinked)
  while `TestBuildGroupsSamplesByProject`/`ByModel`/`SumsTotalsAcrossAllSamples`
  confirm it still counts in `by_project`, `by_model`, and `totals`.
- `TestBuildSessionsAddedCountsDistinctFreshSessions` (=3 for
  s1/s1/s2/s3) and `TestBuildSessionsAddedZeroForEmptyFresh` (=0 for `nil`
  fresh) cover `sessions_added`.
- `TestBuildGroupingFromMergedWhileSessionsAddedFromFreshOnly` — a
  `--merge`-style case: `Build(merged, fresh)` with disjoint session sets;
  asserts totals come from `merged` (500+300=800, not fresh's 999) and
  `sessions_added` counts fresh only (=1).
- `TestBuildEmptyForEmptyGroupingSet` — empty maps, not nil, so JSON
  emits `{}` not `null`.

All required R3 fixture scenarios from the task's Steps 1 are present.

### 2. CLI run writes summary with expected keys

Command:
```
cd agentprof && go run . claude --days 1 -o /tmp/wwcv-y --summary /tmp/wwcv-summary.json \
  && python3 -c "import json; d=json.load(open('/tmp/wwcv-summary.json')); print(sorted(d))"
```
Output:
```
['by_agent_type', 'by_model', 'by_project', 'by_skill', 'sessions_added', 'totals']
```
Exit code: 0. Result: PASS.

### 3. `gofmt -l . | wc -l` must be 0

Command: `cd agentprof && gofmt -l . | wc -l`
Output: `0`
Result: PASS.

## SPEC.md R3 contract checks

Read `agentprof/internal/costsummary/costsummary.go` end to end.

- Shape: `Summary{ByProject, BySkill, ByAgentType, ByModel, Totals,
  SessionsAdded}` with json tags `by_project, by_skill, by_agent_type,
  by_model, totals, sessions_added` — matches spec exactly. Each group
  value is `map[string]int64` (sample_type -> total). Confirmed via CLI
  run above (all 6 keys present).
- project = `smp.Stack[0]` — matches "project = Stack[0]".
- skill = first frame matching `^skill:` or exactly `(no skill)`, else
  bucket `(no skill)` — matches spec, and the unlinked-sample test proves
  it doesn't drop.
- agent_type = first `^agent:` frame, samples with none join no bucket —
  matches spec ("first ^agent:").
- model = last (reverse-iterated) leaf frame skipping `tool:`/`role:`/
  `stage:` prefixes — matches spec's "last leaf frame that isn't
  tool:/role:/stage:".
- `--merge` semantics: `cmd_claude.go`'s `mergeClaude` calls
  `writeCostSummary(merged, fresh, summaryPath)` — grouping/totals from
  `merged` (final post-eviction set), `sessions_added` from `fresh` only,
  matching spec. Verified structurally (staged diff) and via the
  `TestBuildGroupingFromMergedWhileSessionsAddedFromFreshOnly` unit test.
  Not independently exercised end-to-end against a live `--merge` CLI run
  in this pass (task's own acceptance list does not require it; R2's
  merge behavior is task 01's concern and already has its own test
  coverage per SPEC's acceptance-criteria list).
- Non-merge path: `cmdClaude` calls `writeCostSummary(samples, samples,
  *summaryPath)` after `output.Write` — both grouping and sessions_added
  from the same fresh set, matching spec's "without it, from fresh
  Collect() output."

## Pre-existing `-o summary` feature (unrelated, must not break)

`agentprof/summary.go` diff against base commit is empty (file
untouched):
```
git diff 6b0a47a4a769f578d616e42d0421a6aa60e20b2c -- agentprof/summary.go
(no output)
```

Exercised directly:
```
cd agentprof && go run . claude --days 1 -o summary
```
Exit 0, emitted the expected per-(session,model) JSON array (unchanged
shape: session/model/input_tokens/output_tokens/cache_read_tokens/
cache_write_tokens/cost_microusd/priced). Confirms the new `--summary`
flag (distinct flag name, distinct helper `writeCostSummary`, separate
package `costsummary`) did not collide with or break this feature.

## Touch compliance / scope creep

```
git diff 6b0a47a4a769f578d616e42d0421a6aa60e20b2c --name-only
agentprof/cmd_claude.go
agentprof/internal/costsummary/costsummary.go
agentprof/internal/costsummary/costsummary_test.go
specs/workboard-weekly-cost-view/tasks/02-summary-flag.md
```
Touch allowed: `agentprof/cmd_claude.go, agentprof/internal/,
agentprof/testdata/`. All three agentprof files are within Touch. No
`agentprof/testdata/` changes were needed or made. No scope creep found.

## Append-only task-file diff check

```
git diff 6b0a47a4a769f578d616e42d0421a6aa60e20b2c -- 'specs/workboard-weekly-cost-view/tasks/*.md'
```
Only change across all task files in the spec: a single addition to
`02-summary-flag.md` — an HTML `<!-- PLAN ... -->` comment block inserted
between the header fields and `## Goal`. No other task file in the spec
changed. Goal/Steps/Touch/Budget/Acceptance criterion text is byte-identical
to the base commit (confirmed no diff hunks touch those sections — the
diff is a pure insertion before `## Goal`). Status line still reads
`in-progress` (unchanged) and acceptance checkboxes are still unchecked
`[ ]` (expected — implementer ticks them at close-out). This is within
the allowed append-only set (plan comment block).

## Overall verdict: PASS

All three task-file acceptance commands pass with the required output.
The costsummary package correctly implements the R3 grouping/shape
contract, including the (no skill) bucketing for unlinked samples, fresh-
only sessions_added (including the merge-divergence case), and empty-map
JSON shape. The pre-existing unrelated `-o summary` feature is untouched
and still works. No scope creep; Touch list respected. Task-file diff is
append-only (plan comment block only).
