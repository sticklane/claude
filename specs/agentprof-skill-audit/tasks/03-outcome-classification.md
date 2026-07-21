# Task 03: Outcome classification (generic + custom rubric, anti-false-success judge)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 01
Priority: P1
Budget: 22 turns
Spec: ../SPEC.md (requirements R6, R7, R8, R9)
Touch: agentprof/cmd_skillcheck_outcome.go, agentprof/cmd_skillcheck_outcome_test.go

## Goal

A `ClassifyOutcome` function (or similarly-named entry point in
`cmd_skillcheck_outcome.go`) takes ONE of task 01's `SkillInvocation`
values (already assumed by the caller to be `correctly-triggered` — this
task's own package never imports or references anything from task 02's
`cmd_skillcheck_trigger.go`; task 04 is what adapts a trigger-classified
invocation into the call this function expects) plus that invocation's
resolved `SKILL.md` path, and scores `success`/`failure`/`unknown` using
either the invoked skill's `outcome-rubric:` frontmatter (if present,
judged as ONE dimension/one call) or the generic rubric's three questions
(each a separate call) — every outcome-judge prompt explicitly instructs
the judge not to trust the invocation's own closing message.

## Touch

Only `agentprof/cmd_skillcheck_outcome.go` and its test file. Do not touch
`agentprof/cmd_skillcheck_trigger.go` (task 02 — Touch-disjoint sibling,
may land concurrently; this task's code must compile and its tests must
pass with task 02's files entirely absent from the tree, since both may be
worked in separate isolated worktrees before either merges), `agentprof/
main.go`, or `agentprof/cmd_skillcheck.go` (task 04's entrypoint/wiring,
which performs the trigger→outcome adaptation and the
`misfired`/`unresolvable` gating — this task's functions only need to
handle input already known to be `correctly-triggered`).

## Steps

1. Read `outcome-rubric:` via task 01's `claude.SkillFrontmatter` — **do
   not write your own frontmatter parser**; task 01 owns the single shared
   one task 02 also calls, so a second one here would collide with it in
   this same `package main` at merge time. Write a failing test first: a
   fixture `SKILL.md` with the field present, one without.
2. Implement the generic rubric as three fixed judge-call prompts (terminal
   non-error state; explicit error/blocked/deferred signal; user
   correction/redo shortly after) per SPEC.md's Solution "Generic outcome
   rubric" bullet — each is a separate call to the task-01 `Judge`
   interface, each may independently answer `unknown` (R8).
3. Implement the custom-rubric path: when `outcome-rubric:` is present,
   ONE judge call over its full text replaces all three generic calls.
4. Every outcome-judge prompt (both generic and custom) must contain the
   explicit "do not trust the invocation's own closing message; require
   concrete in-transcript evidence" instruction (R7) — assert this via the
   fake judge's recorded prompt text in a test, not via any report field.
5. Aggregate per-invocation: `success` when the applicable judge call(s)
   affirm, `failure` when they don't, `unknown` when any applicable call
   returns `unknown` and none affirms — state and test the exact
   aggregation rule for the 3-call generic case (e.g. majority, or
   any-failure-dominates — pick one, document it in a code comment, and
   test it explicitly since the spec doesn't pin this and it's local to
   this task's own implementation, not a cross-task contract).

## Acceptance

- [ ] `cd agentprof && go build ./...` succeeds.
- [ ] `cd agentprof && go test ./... -run TestClassifyOutcome` passes
      (red-first), covering: `outcome-rubric:` present vs absent routing,
      the custom rubric as a single fake-judge call over its full text, the
      generic rubric as three separate fake-judge calls, the
      anti-closing-message instruction present in every outcome-judge
      prompt (asserted on the fake's recorded prompt strings), and the
      3-call aggregation rule (success/failure/unknown) with a case for
      each outcome.
