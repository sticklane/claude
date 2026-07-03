---
name: build
description: Executes one task file (or a small SPEC.md) end to end - explore via scouts, plan proportionally, implement test-first, verify with an independent agent, commit. The attended inner loop of the pipeline; run it in a fresh session per task.
argument-hint: "[path/to/task.md or SPEC.md]"
disable-model-invocation: true
---

Execute the task at $ARGUMENTS. This skill is the inner loop of the pipeline:
it assumes an agent-ready task/spec with runnable acceptance criteria and is
designed to run in a fresh session.

## 0. Load only the task

Read the task file (and its spec's Requirements section if referenced). Mark
the task's Status as `in-progress` (a bare SPEC.md has no Status field — skip
the bookkeeping steps for it and work from its acceptance criteria directly). Do NOT preload the codebase: for anything
unclear about existing code, fan out `scout` agents and work from their
reports. Read a file directly only when you're about to edit it.

If the task file has no runnable acceptance criteria, stop and say the task
isn't agent-ready — improvising weaker criteria silently is how "looks done"
replaces "is done".

## 1. Plan proportionally

- Diff describable in one sentence → skip planning, implement.
- Otherwise → write a short plan (files to change, in what order, what could
  go wrong) as a comment block in the task file, placed below the header lines
  (never between them — dispatchers parse the headers and the block must not
  break them). Think hard on genuinely tricky design points; don't burn
  extended thinking on mechanical steps.
- Plan contradicts the task or reveals a missing decision → stop and surface
  it rather than guessing.

## 2. Implement, verification-first

- Where acceptance criteria are test-shaped: write the failing tests FIRST,
  run them, confirm they fail for the right reason, commit the tests, then
  implement until green — without modifying the tests.
- Match the surrounding code's style and idiom; no drive-by refactors (that's
  scope creep the verifier will flag).
- Run the narrowest relevant test after each meaningful change, not the whole
  suite every time.

## 3. Verify with fresh eyes

1. Run every acceptance command yourself; fix until all pass.
2. Run the project's standard gates (build/lint/tests per CLAUDE.md).
3. Spawn the `verifier` agent with the task file path and instruct it to
   verify the working tree against the acceptance criteria. It has no memory
   of your implementation and won't rationalize shortcuts. Also pass it an
   evidence file path derived from the task file's location:
   `specs/<slug>/tasks/<name>.md` → `specs/<slug>/evidence/<name>.md`; a
   bare `specs/<slug>/SPEC.md` → `specs/<slug>/evidence/spec.md`; any other
   layout → pass no path (the verifier then writes nothing; note at
   close-out that evidence was not persisted). The verifier writes its full
   report there; a re-verify overwrites it.
4. Collect every subagent's result within your current turn — ending a
   turn while a verifier or monitor is still pending orphans its report
   (the observed stall mode in drained runs). If a subagent goes silent,
   respawn it once and continue.
5. On FAIL: fix and re-verify. After two failed fix attempts on the same
   issue, stop and report — repeated correction in a degraded context is the
   known failure mode; a fresh session with a better task file beats a long
   session of thrashing.

## 4. Close out

- Simplification pass over the code touched this session: run the bundled
  `/simplify` if available, otherwise apply its principles yourself — never
  change what the code does, only how; remove comments that describe obvious
  code, redundant abstractions, and defensive handling for cases that can't
  happen. Re-run the acceptance commands after.
- Update the task file: Status `done`, tick acceptance boxes, one line of
  evidence each citing the `evidence/` file (from the verifier's report,
  not your own claim) rather than duplicating output; delete the plan
  comment block from step 1.
- Commit code + task file + the verifier's `evidence/` file with a message
  referencing the task. Push / open a PR only if the user asked.
- Report: what shipped, evidence summary, anything learned the hard way — and
  if there WAS such a learning, run /distill before ending.
- Tell the user to `/clear` before starting the next task.
