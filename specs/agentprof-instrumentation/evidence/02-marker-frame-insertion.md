# Verification: Task 02 — Role/stage marker detection and frame insertion

Verdict: PASS

Base commit for append-only diff: 8f63edeb63698c740b9f3f86609e2c6fd98da4c3
HEAD at verification time: 08a2de5 (feat commit), preceded by 94d7def (test commit)

## Criterion 1 — go test ./... and named tests

Command: `cd agentprof && go clean -testcache && go test ./...`
Result: all 12 packages `ok`.

Command: `cd agentprof && go test ./internal/claude/ -run 'TestCollectInsertsRoleFrameBeforeAgentFrameFromSubagentMarker|TestCollectInsertsStageFrameAfterSkillWithBoundaryHandoff|TestCollectMarkerlessTranscriptKeepsByteIdenticalStacks|TestCollectBuildsExpectedStacksIncludingNestedWorkflowAgent' -v`
Output tail:
```
=== RUN   TestCollectBuildsExpectedStacksIncludingNestedWorkflowAgent
--- PASS: TestCollectBuildsExpectedStacksIncludingNestedWorkflowAgent (0.00s)
=== RUN   TestCollectInsertsRoleFrameBeforeAgentFrameFromSubagentMarker
--- PASS: TestCollectInsertsRoleFrameBeforeAgentFrameFromSubagentMarker (0.00s)
=== RUN   TestCollectInsertsStageFrameAfterSkillWithBoundaryHandoff
--- PASS: TestCollectInsertsStageFrameAfterSkillWithBoundaryHandoff (0.00s)
=== RUN   TestCollectMarkerlessTranscriptKeepsByteIdenticalStacks
--- PASS: TestCollectMarkerlessTranscriptKeepsByteIdenticalStacks (0.00s)
PASS
ok  	github.com/sticklane/agentprof/internal/claude	0.158s
```
PASS.

## Criterion 2 — gofmt

Command: `cd agentprof && gofmt -l . | wc -l`
Output: `0`
PASS.

## Criterion 3 — spec-fidelity (R6/R7)

Inspected `agentprof/internal/claude/claude.go` diff (base→HEAD):
- `role:<role>` frame: built via
  `agentFrames = slices.Concat([]string{"role:" + r.role}, agentFrames)` where
  `agentFrames` started as `[]string{a.frame, r.model}` (`a.frame` is the
  sub-agent's `agent:<type>` frame) — role lands immediately before
  `agent:<type>`, not after/appended. Confirmed by test
  `TestCollectInsertsRoleFrameBeforeAgentFrameFromSubagentMarker`, which also
  asserts the pre-marker (role-less) stack shape no longer occurs.
- `stage:<stage>` frame: `stack := []string{project, turn, r.skill}`, then
  conditionally `stack = append(stack, "stage:"+r.stage)`, then
  `stack = append(stack, "main", r.model)` — stage lands immediately after
  `skill:<name>` and before `main`. The same `stack` slice is passed to both
  `r.sample(...)` (model-call) and `r.toolSamples(...)` (tool: samples), so
  both sample kinds get the stage frame. Confirmed by
  `TestCollectInsertsStageFrameAfterSkillWithBoundaryHandoff`: 2 dispatch
  model-call samples (marker's own line + one after), 1 dispatch tool:Bash
  sample, 1 collect model-call sample after the second marker (re-staging).
- Boundary handoff: `activeRole`/`activeStage` are package-scope-per-parse
  locals in `parseTranscript`, updated when a marker regex matches text on an
  assistant line, and carried into every subsequent `response{role: ...,
  stage: ...}` until overwritten by the next marker of the same kind or EOF —
  matches "from marker position until next marker of same kind or transcript
  end".
- Regex constants match exactly:
  `roleMarkerRe = regexp.MustCompile(`<!-- agentprof:role=([a-z0-9-]+) -->`)`
  `stageMarkerRe = regexp.MustCompile(`<!-- agentprof:stage=([a-z0-9-]+) -->`)`
  Plain `regexp` package only; no LLM/API call anywhere in the diff.
- R7 markerless byte-identical stacks: `TestCollectMarkerlessTranscriptKeepsByteIdenticalStacks`
  asserts the exact pre-change stack shape and asserts no `role:`/`stage:`
  frame anywhere. The pre-existing full-fixture test
  `TestCollectBuildsExpectedStacksIncludingNestedWorkflowAgent` is byte-for-byte
  unmodified in the diff (`git diff base HEAD -- claude_test.go | grep` for
  that test name returns nothing) and passes unchanged.
- Full diff of claude.go (base→HEAD) is a clean additive change: existing
  stack-building lines were restructured into `append` sequences but produce
  identical output when role/stage are empty; no frame renamed, reordered, or
  removed for markerless input.
PASS.

## Criterion 4 — append-only task-file check

Command: `git diff 8f63edeb63698c740b9f3f86609e2c6fd98da4c3 -- specs/agentprof-instrumentation/tasks/` (working tree)
Output: empty (no diff at all).

Command: `git diff 8f63edeb63698c740b9f3f86609e2c6fd98da4c3 HEAD -- specs/agentprof-instrumentation/tasks/`
Output: empty (no diff across the two commits that implemented this task either).

Finding (not a criterion violation, but a process gap): the task file
`specs/agentprof-instrumentation/tasks/02-marker-frame-insertion.md` still
reads `Status: in-progress` with both acceptance checkboxes unticked and no
evidence-citation lines added, identical to the base commit. Since there are
zero edits to the task file, there is nothing that violates append-only (no
forbidden Goal/Steps/Touch/criterion-text edits occurred), but the worker
never recorded completion in its own task file as the append-only contract
expects it to. PASS on "no disallowed edits" per se; flagging the missing
Status/checkbox update as a gap for the orchestrator to address.

## Criterion 5 — scope check

Command: `git diff 8f63edeb63698c740b9f3f86609e2c6fd98da4c3 HEAD --stat`
Output:
```
 agentprof/internal/claude/claude.go      |  40 ++++++++++-
 agentprof/internal/claude/claude_test.go | 115 +++++++++++++++++++++++++++++++
 2 files changed, 152 insertions(+), 3 deletions(-)
```
Only files under `agentprof/internal/` changed (within Touch:
`agentprof/internal/, agentprof/testdata/`). No `agentprof/testdata/` changes
(not required — tests use inline fixture writers, not committed testdata
files). No edits to `.claude/skills/`, `antigravity/`, or `.claude-plugin/`.
PASS.

## Gates

`cd agentprof && go test ./...` — all packages ok (fresh, testcache cleared).
`cd agentprof && gofmt -l . | wc -l` — 0.
Both are the repo's stated canonical checks per agentprof/CLAUDE.md
(`bash scripts/check.sh`); ran the two explicit commands the task specifies,
consistent with that gate's format+test layers.

## Summary

All five criteria PASS. Implementation is a clean, additive, regex-only
change; both new marker tests and the pre-existing full-fixture test pass;
gofmt clean; no scope creep. Only finding: task file Status/checkboxes were
never updated to reflect completion (process/record-keeping gap, not a code
defect).
