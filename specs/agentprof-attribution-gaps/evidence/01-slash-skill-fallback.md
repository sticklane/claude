# Verification: 01-slash-skill-fallback

Verdict: PASS

## Criterion 1 — `cd agentprof && go test ./internal/claude/` passes, including 4 fixture cases

Command: `cd agentprof && go test ./internal/claude/ -v`
Result: `ok github.com/sticklane/agentprof/internal/claude 0.200s` — all tests pass, including:

- (a) `TestCollectCommandNameSuppliesSkillFrameWhenAttributionAbsent` — builds a
  transcript with `userCommandLine("/parallel")` + `assistantLine("m1")` (no
  attributionSkill), asserts single sample's Stack[2] == `"skill:parallel"`. PASS.
- (b) `TestCollectBuiltinCommandKeepsNoSkillFrame` — `/clear` turn, asserts
  Stack[2] == `"(no skill)"`. PASS.
- (c) `TestCollectAttributionSkillWinsOverCommandName` — `/parallel` command tag
  + `assistantLineWithSkill("m1", "build")`, asserts Stack[2] == `"skill:build"`
  (attributionSkill wins over command fallback). PASS.
- (d) `TestCollectNamespacedCommandNameStripsPluginPrefix` — `/agentic:drain`
  tag, asserts Stack[2] == `"skill:drain"`. PASS.

All four drive the real `claude.Collect()` entry point against synthetic
transcript fixtures (via `writeMain`/`userCommandLine`/`assistantLine` helpers
that already existed pre-task, reused not duplicated) and assert on parsed
`Stack[2]` — not implementation internals or tautologies. An existing golden
(`TestCollectDedupsRepeatedMessageIDCountingUsageOnce`) was updated from
`(no skill)` to `skill:parallel` for the msg_a2 `/parallel` turn, consistent
with the new fallback behavior — not overfitting, since it reflects the one
behavior change the task specifies.

## Criterion 2 — `bash agentprof/scripts/check.sh` green

Command: `bash agentprof/scripts/check.sh`
Output:
```
check: format-check ok
check: lint ok
check: tests ok
```
PASS.

## Sanity checks

- **attributionSkill always wins**: confirmed by code
  (`internal/claude/claude.go`, assistant case: `if l.AttributionSkill == ""
  { ... use cmdFrame }` — the fallback is gated strictly behind an empty
  attributionSkill) and by test (c) above.
- **Harness builtins map to (no skill)**: `builtinDenylist` map covers
  `clear`, `model`, `reload-plugins`, `rate-limit-options`; `commandSkillFrame`
  returns `""` for any of them. Verified for `/clear` via test (b); the other
  three builtins are covered by the denylist map itself (not independently
  fixture-tested, but the mapping is table-driven and structurally identical
  for all four entries — low risk).
- **Namespace stripping consistent with `normalizeSkillFrame`**:
  `commandSkillFrame` explicitly calls `normalizeSkillFrame(name)` (same
  function used elsewhere for attributionSkill normalization), confirmed by
  test (d) and by direct code inspection of the diff.

## Diff scope check

`git diff c42b6b7cb26ecf61371a84f54553f9253d70d2d6 --stat`:
```
 agentprof/internal/claude/claude.go                | 58 +++++++++++++++++----
 agentprof/internal/claude/claude_test.go           | 60 +++++++++++++++++++++-
 agentprof/testdata/claude-dir.expected.json        |  2 +-
 .../tasks/01-slash-skill-fallback.md               | 15 ++++++
 4 files changed, 123 insertions(+), 12 deletions(-)
```
All code/test/fixture changes fall within the task's Touch
(`agentprof/internal/claude/`, `agentprof/testdata/`). No other task files
under `specs/agentprof-attribution-gaps/tasks/` were touched.

## Task-file append-only check

`git diff c42b6b7cb26ecf61371a84f54553f9253d70d2d6 -- specs/agentprof-attribution-gaps/tasks/01-slash-skill-fallback.md`
shows only a 15-line insertion: the `PLAN (delete at close-out)` HTML comment
block, added directly under the header fields. This is exactly the
plan-comment-block category the append-only rule permits. `Status:` line
remains `in-progress` (not flipped to done) and acceptance checkboxes remain
unticked — the worker did not claim completion in the task file, which is
consistent with running this as a pre-close verification pass. No criterion
text, Goal/Steps/Touch/Acceptance body, or other task file was modified.

## Scope creep

None found. No changes outside Touch; no unrelated files modified.
