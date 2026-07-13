# Verification: Task 04 — untyped_fanout guard metric

Verdict: **PASS**

Branch: task/04-untyped-fanout-metric
Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-a3c1a7d6097d2ba3b
Base for append-only diff: 2d89ae60949bfa6b3a3e0697e588834125240b07

## Task-file append-only check

`git diff 2d89ae60949bfa6b3a3e0697e588834125240b07 -- specs/untyped-agent-fanout/tasks/04-untyped-fanout-metric.md`

Only change: insertion of the `<!-- PLAN (delete at close-out) -->` comment
block after the header fields. Goal/Steps/Touch/Budget/Acceptance text is
byte-identical to base. Status line remains `in-progress` (not yet flipped
to done, no checkbox ticks made) — consistent with an unfinished-status
task whose work is otherwise complete; no illegal edits found. PASS.

## Acceptance criteria

1. `cd agentprof && go test ./internal/costsummary/` → PASS.
   All tests green including:
   `TestBuildUntypedFanoutCountsAdjacentUntypedChainDepth`,
   `TestBuildUntypedFanoutTypedFrameBreaksChain`,
   `TestBuildUntypedFanoutExcludesClaudeCodeGuide`,
   `TestBuildUntypedFanoutTransparentMarkersDoNotBreakChain`,
   `TestBuildUntypedFanoutSingleFrameCountsButDepthOne`,
   `TestBuildUntypedFanoutTypedOnlyAndAgentlessExcluded`,
   `TestBuildUntypedFanoutByModelNonNilWhenEmpty`.
   `ok github.com/sticklane/agentprof/internal/costsummary 0.224s`

2. `cd agentprof && go build -o /tmp/agentprof-v . && /tmp/agentprof-v claude --days 7 --summary /tmp/sv.json -o /dev/null && jq -e '.untyped_fanout | has("calls") and has("cost_microusd") and has("by_model") and has("max_depth")' /tmp/sv.json`
   → `true` (exit 0). Build done to /tmp per instructions (tree not dirtied).
   Sample output: `{"calls":14347,"cost_microusd":970869994,"by_model":{...},"max_depth":5}`.

3. `grep -c 'untyped_fanout' agentprof/SCHEMA.md` → `3` (≥ 1). PASS.

4. `bash agentprof/scripts/check.sh` → `check: format-check ok / check: lint ok / check: tests ok`. Green.

5. `bash agent-console/scripts/check.sh` → `py_compile: ok`, `render: ok (65 skills, adapter seam ok)`,
   `Ran 157 tests in 7.196s / OK / check: PASS`. Includes
   `RenderUntypedFanoutLine.test_untyped_fanout_line_rendered_when_section_present`,
   `test_untyped_fanout_line_absent_when_section_missing`, and
   `test_untyped_fanout_none_is_omitted_gracefully` — present/absent/None
   cases all present and asserted (not just "runs without error"):
   present case asserts `"untyped"` label and rendered `$1.23` cost string
   appear; absent case asserts `"untyped"` is NOT in output and the rest of
   the panel (`"Cost (7d)"`) still renders.

## SPEC R4 semantics verification

Read agentprof/internal/costsummary/costsummary.go (Summary/UntypedFanout
structs, `untypedAgents` set, `Build`, `untypedFanout`, `untypedRunDepth`)
and its tests, plus agent-console/agent-console.py's cost-panel render diff
and agent-console/tests/test_cost_panel.py.

- **Exact-match untyped set**: `untypedAgents` map (costsummary.go:55-60)
  contains exactly `agent:claude`, `agent:agentic:claude`,
  `agent:general-purpose`, `agent:agentic:general-purpose`, tested via Go
  map membership (`_, ok := untypedAgents[f]`) — a true exact match, not
  `strings.HasPrefix`. `TestBuildUntypedFanoutExcludesClaudeCodeGuide`
  confirms `agent:claude-code-guide` (shares the `agent:claude` prefix) is
  excluded entirely (max_depth 0, calls 0, cost 0, empty ByModel). PASS.

- **Depth edge rule**: `untypedRunDepth` (costsummary.go:162-178) iterates
  stack frames; non-`agent:` frames (`wf:`, `stage:`, `role:`, model, main,
  project) are `continue`d (transparent, don't break adjacency); an
  `agent:` frame in the untyped set increments/extends `run`; any other
  `agent:` frame resets `run` to 0. Confirmed by tests:
  `agent:claude>agent:claude` → max_depth 2
  (`TestBuildUntypedFanoutCountsAdjacentUntypedChainDepth`);
  `agent:claude>agent:scout>agent:claude` → max_depth 1
  (`TestBuildUntypedFanoutTypedFrameBreaksChain`, comment explicitly notes
  "not depth 2"); `wf:`/`role:` markers between two untyped frames do not
  break the run — depth stays 2
  (`TestBuildUntypedFanoutTransparentMarkersDoNotBreakChain`). Matches
  SPEC.md lines 86-90 exactly, including the explicit "depth 1 twice, not
  depth 2" language. PASS.

- **Additive-only diff**: `git diff <base> -- agentprof/internal/costsummary/costsummary.go`
  contains zero removed (`-`) lines outside the `---` diff header — pure
  addition of the `UntypedFanout` field/struct/set/functions and their
  wiring into `Build`. `costsummary_test.go` diff is likewise pure
  addition (no removed lines). PASS.

- **--merge path respected**: `s.UntypedFanout = untypedFanout(forGrouping)`
  (costsummary.go:124) is computed from `forGrouping`, the same argument
  `reprimeRollup` and `sessionStats` use — in `--merge` mode this is the
  merged post-eviction rolling window, not `fresh` alone — matching the
  established reprime/sessions pattern in this same function. No separate
  merge-specific logic exists to diverge. PASS (by code-path inspection;
  no dedicated merge-mode untyped_fanout test exists, but the shared
  code path with reprime/sessions — which IS merge-tested via
  `TestBuildGroupingFromMergedWhileSessionsAddedFromFreshOnly` — makes
  divergence structurally implausible).

- **Touch discipline**: `git diff --stat <base>` touches only
  `agent-console/agent-console.py`, `agent-console/tests/test_cost_panel.py`,
  `agentprof/SCHEMA.md`, `agentprof/internal/costsummary/costsummary.go`,
  `agentprof/internal/costsummary/costsummary_test.go`, and the task file
  itself. `agentprof/internal/claude/` does NOT appear in the diff stat —
  confirmed untouched, per the task's explicit prohibition. PASS.

- **Workboard renderer present/absent**: `agent-console.py`'s
  `render_workboard` adds an `if fanout:` block (falsy-safe: also handles
  `None` per test 3) rendering one `<div class="sub">Untyped fan-out (7d)</div>`
  line with calls/depth/cost, appended only after the existing reprime
  block, guarded by `cost.get("untyped_fanout")`. Confirmed by
  `test_cost_panel.py`'s three new tests (present/absent/None), all of
  which assert on actual rendered content (label text, `$` cost string),
  not merely "doesn't throw". PASS.

## Gates

- `bash agentprof/scripts/check.sh` → green (format-check, lint, tests).
- `bash agent-console/scripts/check.sh` → green (157 tests, includes new
  untyped-fanout renderer cases).

## Scope creep

None found. Diff stat is scoped exactly to the task's `Touch:` list plus
the task file itself (plan-comment addition only, permitted).

## Overfitting check

Tests exercise structural boundary cases (adjacency, typed-break,
prefix-vs-exact match, transparency, empty/nil safety) rather than
hard-coding literal fixture outputs the implementation special-cases
around. The implementation is a general map-membership + adjacency-scan
algorithm, not a lookup table keyed to test fixture values — it would
survive reasonable input variation (e.g. a new untyped-set member, a
deeper chain, additional transparent marker prefixes not literally
`wf:`/`stage:`/`role:` since the code treats "not agent:" generically as
transparent, which is a superset of the spec's named markers and does not
violate the spec's edge rule since it's still limited to `agent:` frames
for run-breaking purposes).

## Overall verdict: PASS
