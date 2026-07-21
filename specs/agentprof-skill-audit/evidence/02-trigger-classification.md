# Verification: task 02 — trigger classification

Verdict: DONE (all acceptance criteria pass; one process note — Status/checkboxes were not flipped by the worker, see note below)

Branch: task/02-trigger-classification
Base commit: 8ea2d7ebf791047840dabb7ee6a08114457cc403

## Criterion 1: `cd agentprof && go build ./...` succeeds

Command: `cd agentprof && go build ./... ; echo EXIT:$?`
Result: `EXIT:0`, no output. PASS.

## Criterion 2: `go test ./... -run TestClassifyTrigger` passes and covers the required cases

Command: `cd agentprof && go test ./... -run TestClassifyTrigger -v`
Result: 11/11 tests PASS in package `main`:

```
TestClassifyTriggerExplicitViaCommandTag            PASS
TestClassifyTriggerSelfChainedNoPrecedingUserTurn    PASS
TestClassifyTriggerDisableModelInvocationExempt      PASS
TestClassifyTriggerResolvesLocalSkillPath            PASS
TestClassifyTriggerResolvesPluginCachePath           PASS
TestClassifyTriggerUnresolvableWhenNeitherPathExists PASS
TestClassifyTriggerCorrectlyTriggeredFromJudge       PASS
TestClassifyTriggerMisfiredFromJudge                 PASS
TestClassifyTriggerJudgePromptContainsSkillDescription PASS
TestClassifyTriggerPossibleMissMatchesPhrase         PASS
TestClassifyTriggerPossibleMissCleanMiss             PASS
```

Read `agentprof/cmd_skillcheck_trigger_test.go` in full (240 lines) and confirmed each required
case genuinely exists and exercises real behavior, not just a passing label:

- explicit_invocation via command-tag: `TestClassifyTriggerExplicitViaCommandTag` sets
  `CommandTag: "drain"` and asserts `ClassExplicitInvocation` + zero judge calls.
- self_chained via no-preceding-user-turn: `TestClassifyTriggerSelfChainedNoPrecedingUserTurn`
  sets `PrecededByUserTurn: false` and asserts `ClassSelfChained` + zero judge calls.
- disable-model-invocation exemption: `TestClassifyTriggerDisableModelInvocationExempt` writes a
  real SKILL.md with `disable-model-invocation: true`, asserts `ClassExplicitInvocation` and zero
  judge calls (exemption happens before judge dispatch).
- All three SKILL.md resolution paths: `TestClassifyTriggerResolvesLocalSkillPath` (cwd-relative
  `.claude/skills/<name>/SKILL.md`), `TestClassifyTriggerResolvesPluginCachePath` (glob under a
  separate `PluginCacheRoot`, no local skill present), and
  `TestClassifyTriggerUnresolvableWhenNeitherPathExists` (neither path populated →
  `ClassUnresolvable`, zero judge calls).
- correctly-triggered vs misfired via the fake judge:
  `TestClassifyTriggerCorrectlyTriggeredFromJudge` (fake replies "correctly-triggered") and
  `TestClassifyTriggerMisfiredFromJudge` (fake replies "misfired") — same skill/fixture, only the
  fake's reply differs, proving the classification branches on the judge's answer.
- possible-miss keyword matching, hit and clean miss:
  `TestClassifyTriggerPossibleMissMatchesPhrase` (turn contains the quoted trigger phrase → 1
  miss returned) and `TestClassifyTriggerPossibleMissCleanMiss` (turn "what is the capital of
  France" → 0 misses). No `judge.Fake` is passed to `DetectPossibleMisses` at all — confirms it's
  deterministic/no judge call, matching R5 and the plan.

## Criterion 3: fake judge asserts the received prompt contains the ACTUAL skill description

`TestClassifyTriggerJudgePromptContainsSkillDescription` writes a SKILL.md with a distinctive,
non-generic description ("Decomposes a SPEC.md into independent task files sized for one clean
session.") for a skill named `breakdown`, then asserts
`strings.Contains(fake.Calls[0].Prompt, desc)` where `desc` is that exact string read back from
the fixture file — not a hardcoded/generic stand-in. Also asserts the prompt contains the actual
preceding user turn text. PASS — grounded in the real description, confirmed by reading the test
source directly (not just trusting the green run).

## Implementation reuse check

`grep -rn "func.*Frontmatter" --include="*.go" .` (excluding `_test.go`) finds exactly one
definition: `internal/claude/skill_frontmatter.go:25: func SkillFrontmatter(path string)`.
`cmd_skillcheck_trigger.go` calls `claude.SkillFrontmatter(path)` at both call sites (population
split and possible-miss enumeration) — no second frontmatter parser was written. PASS.

## Scope / Touch check

`git diff 8ea2d7ebf791047840dabb7ee6a08114457cc403..HEAD --stat`:

```
 agentprof/cmd_skillcheck_trigger.go                | 223 +++++++++++++++++++
 agentprof/cmd_skillcheck_trigger_test.go           | 240 +++++++++++++++++++++
 .../tasks/02-trigger-classification.md             |  19 ++
 3 files changed, 482 insertions(+)
```

Exactly the two Touch-listed files plus the task's own .md file. No changes to
`cmd_skillcheck_outcome.go`, `main.go`, or `cmd_skillcheck.go` (all explicitly off-limits per the
task's own Touch section). PASS — no scope creep.

## Append-only task-file check

`git diff 8ea2d7ebf791047840dabb7ee6a08114457cc403..HEAD -- specs/agentprof-skill-audit/tasks/02-trigger-classification.md`
shows a single added hunk: the `<!-- PLAN ... -->` HTML comment block (19 lines) inserted between
the `Touch:` header and `## Goal`. This is the sanctioned "maintain plan comment block" append.
No Status flip, no checkbox ticks, no evidence-citation lines, and Goal/Steps/Touch/Budget/
acceptance-criteria text is byte-identical to the base. PASS on append-only-ness.

**Process note (not a criterion failure, but worth flagging):** the `Status:` header is still
`in-progress` and none of the three acceptance checkboxes are ticked, despite the implementation
being complete, tested, and passing all gates on disk. Per repo convention this task would
normally be flipped to `needs-verification` with ticked boxes and evidence-citation lines before
a verifier runs. Since the actual criteria all independently verify as passing against the code
on disk, this does not block a DONE verdict on the acceptance criteria themselves, but the task
file's own bookkeeping is stale/incomplete relative to the work performed.

## Gate

`bash scripts/check.sh` (run from `agentprof/`):

```
check: format-check ok
check: lint ok
check: tests ok
```

PASS.

## Verdict

DONE — all three acceptance criteria pass, verified by running the actual commands and reading
the test file in full to confirm the required cases are genuinely present (not just green by
accident). No scope creep; task-file diff is append-only. Full `scripts/check.sh` is green.
