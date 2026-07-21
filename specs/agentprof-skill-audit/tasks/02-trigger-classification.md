# Task 02: Trigger classification (population scoping + resolution + possible-miss)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: 01
Priority: P1
Budget: 22 turns
Spec: ../SPEC.md (requirements R3, R3a, R4, R5)
Touch: agentprof/cmd_skillcheck_trigger.go, agentprof/cmd_skillcheck_trigger_test.go

## Goal

A `ClassifyTriggers` function (or similarly-named entry point in
`cmd_skillcheck_trigger.go`) takes the `SkillInvocations` output from task
01 and a resolved skill-set (SKILL.md descriptions) and returns, per
invocation, one of `correctly-triggered` / `misfired` / `unresolvable` /
`explicit_invocation` / `self_chained`, plus a separate list of
`possible-miss` candidates for non-triggering user turns.

## Touch

Only `agentprof/cmd_skillcheck_trigger.go` and its test file. Do not touch
`agentprof/cmd_skillcheck_outcome.go` (task 03 — Touch-disjoint sibling,
may land concurrently), `agentprof/main.go`, or `agentprof/cmd_skillcheck.go`
(task 04's entrypoint/wiring).

## Steps

1. Implement the population split first (SPEC.md Solution step 2):
   `explicit_invocation` for a preceding `<command-name>` tag,
   `self_chained` for no intervening user turn, `explicit_invocation` for
   every invocation of a skill carrying `disable-model-invocation: true`
   (R4) — write failing tests for each case against task 01's
   `SkillInvocations` fixture shapes first.
2. For the remaining model-auto-trigger population, implement SKILL.md
   resolution in the fixed order SPEC.md Solution step 3 states: (a)
   `.claude/skills/<name>/SKILL.md` relative to the transcript's recorded
   `cwd`; (b) the plugin-cache path; (c) `unresolvable` if neither exists.
   Once a path resolves, call task 01's `claude.SkillFrontmatter` to read
   its `description:`/`disable-model-invocation:` fields — **do not write
   your own frontmatter parser**; task 01 owns the single shared one task
   03 also calls, so a second one here would collide with it in this same
   `package main` at merge time. Test all three resolution paths with
   fixtures.
3. For each resolved invocation, call the task-01 `Judge` interface (via
   its `Fake` in tests) with a trigger-correctness prompt comparing the
   skill's description against the preceding user turn(s); classify
   `correctly-triggered`/`misfired` from the judge's answer.
4. Implement the possible-miss detector (R5): deterministic keyword/phrase
   match (no judge call) between every currently-installed skill's
   declared trigger phrases (read via `claude.SkillFrontmatter`, same as
   step 2 — not a separate parser) and non-triggering user turns' text.
   "Currently-installed" enumerates from `.claude/skills/*/SKILL.md` under
   the invocation cwd plus the plugin-cache layout from step 2 — test with
   a fixture skill set and a turn containing (and one not containing) a
   matching phrase.

## Acceptance

- [ ] `cd agentprof && go build ./...` succeeds.
- [ ] `cd agentprof && go test ./... -run TestClassifyTrigger` passes
      (red-first), covering: explicit_invocation via command-tag,
      self_chained via no-preceding-user-turn, disable-model-invocation
      exemption, all three SKILL.md resolution paths (including
      `unresolvable`), correctly-triggered vs misfired via the fake judge,
      and possible-miss keyword matching (both a hit and a clean miss).
- [ ] The fake judge in at least one test asserts the trigger-judge prompt
      it received contains the invoked skill's actual description text
      (proving the classification is grounded in the real description, not
      a hardcoded stand-in).
