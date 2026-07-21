# Verification: Task 01 — claude accessor and judge interface

Verdict: PASS

## Acceptance criteria

1. ✓ `cd agentprof && go build ./...`
   Command run from worktree root. Exit clean, no output.

2. ✓ `cd agentprof && go test ./internal/claude/... -run TestSkillInvocations`
   Output: `--- PASS: TestSkillInvocationsPairsResultsCommandTagsAndUserTurns (0.00s)` / `ok`.
   Single test exercises all three fixture shapes (model-auto-triggered plain
   turn, self-chain with no intervening user turn, command-tag-opened turn
   with args) and asserts Name/Args/Result/CommandTag/PrecededByUserTurn per
   invocation — behavioral (L2), not just structural presence.

3. ✓ `cd agentprof && go test ./internal/claude/... -run TestSkillFrontmatter`
   Output: 4/4 PASS — `ReadsDescription`, `ReadsOutcomeRubricBlockScalar`,
   `ReadsDisableModelInvocation`, `MinimalHasNoOptionalFields`. All four
   fixture cases from Step 4 are covered; block-scalar parsing verified by
   substring assertions on the joined lines.

4. ✓ `cd agentprof && go test ./internal/judge/...`
   Output: 3/3 PASS — `TestCLIJudgeCommandSetsScratchConfigDirAndFlags`,
   `TestCLIJudgeCommandUsesFreshScratchDirPerInvocation`,
   `TestFakeJudgeRecordsPromptAndTier`. The command-construction test asserts
   `CLAUDE_CONFIG_DIR` env var (under scratch root, not argv), `--model
<tier>`, `--output-format json` on the built `*exec.Cmd` without ever
   calling `.Output()`/`.Run()` — confirmed by reading `cli.go`: `command()`
   only builds `exec.CommandContext`, execution happens only in the separate
   `Judge()` method.

5. ✓ `cd agentprof && bash scripts/check.sh`
   Output: `check: format-check ok` / `check: lint ok` / `check: tests ok`.

## Implementation review (not vacuous)

- `SkillInvocations` (skill_invocations.go): walks JSONL reusing package's
  `transcriptLine`/`turnPrompt`, pairs `Skill` tool_use blocks (by id) with
  `tool_result` content, tracks `curCommandTag` and
  `userTurnSinceLastSkill` to flip false only on a same-turn/self-chain
  invocation. Matches Goal item (1) exactly.
- `SkillFrontmatter` (skill_frontmatter.go): hand-parsed top-level frontmatter
  reader; handles block-scalar indicators (`|`, `>`, etc.) by consuming
  subsequent more-indented lines; returns zero Frontmatter, no error, for a
  minimal file. Matches Goal item (2); single shared parser, no duplication.
- `judge` package: `Judge` interface (judge.go), `CLIJudge` (cli.go) with
  `command()` split out for testability (mirrors `naming/cli.go`'s pattern —
  confirmed shape matches: build-then-execute split), and `Fake` (fake.go)
  recording `[]FakeCall{Prompt,Tier}`. Matches Goal item (3).

## Touch-list check

`git diff 8f3d162 --stat -- agentprof/` shows exactly 8 changed files, all
newly added, all within the task's `Touch:` list:
`skill_frontmatter.go`, `skill_frontmatter_test.go`,
`skill_invocations.go`, `skill_invocations_test.go`,
`judge/cli.go`, `judge/cli_test.go`, `judge/fake.go`, `judge/judge.go`.
No file outside the Touch list changed. `agentprof/main.go` and
`cmd_skillcheck*.go` untouched (task 04 scope, correctly avoided).

## Append-only task-file check

`git diff 8f3d162 -- specs/agentprof-skill-audit/tasks/01-claude-accessor-and-judge-interface.md`
is empty — no edits to the task file at all (Status line still `pending`,
no acceptance boxes ticked). This matches the caller's note that Status was
already `in-progress`... actually observed Status is `pending` in the
current file (header shows `Status: pending`), and close-out has not yet
occurred. No Goal/Steps/Touch/Budget/acceptance text was altered (diff is
empty against base). Nothing to flag.

## Red-first note (informational, not disqualifying)

Each of the three git commits (6e995e6, 05fb575, 08044f0) bundles the test
file and implementation file together in one commit, so post-hoc git
history cannot independently confirm the test was run red before the
implementation was written (the criterion's own red-first parenthetical is
therefore unverifiable from the repository state alone). All tests
currently pass and are behavioral, non-trivial, non-tautological — no
evidence of overfitting to literal fixture strings; frontmatter parser
handles generic key/value and block-scalar shapes, not hardcoded fixture
values. Judge command test asserts general properties (dir under root,
env-not-argv, distinct dirs per call), not the exact fixture path — a
reasonable variation (different prompt/tier/root) would still pass.

## Scope creep

None found. Diff is limited to the 8 touched files, all additive (no
existing file modified).

## Gate

`bash scripts/check.sh` (format-check, lint, tests) — all green.

## Criteria-adequacy

- R2/R4/R5/R6/R9/R12 (SkillInvocations pairing, frontmatter parsing incl.
  block scalar, CLAUDE_CONFIG_DIR self-pollution guard): each backed by a
  behavioral test that asserts parsed/returned field values against a
  representative fixture, not mere text presence — L2 (behavior) evidence.
  Entailment holds: passing these tests requires the accessor/parser/command
  builder to actually produce correct structured output, not just exist.
- No criterion in this task requires end-to-end (L3) exercise (e.g. a live
  `claude` CLI call) — the Steps explicitly ask for a command-construction
  test that avoids executing a subprocess, which is faithfully what was
  built.
