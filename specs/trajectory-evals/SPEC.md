# Evals v2: opt-in trajectory assertions

Status: open
Priority: P2

## Problem

The evals runner grades artifacts only — "v1 grades artifacts only — what
a run produced, not the trajectory it took"
(`.claude/skills/evals/SKILL.md`), a scope
decision recorded in `specs/archive/skill-evals/SPEC.md` ("Trajectory
assertions (transcript greps) — v2, per scope decision"). Every
`assert.sh` runs with CWD `$EVAL_DIR` and sees only produced files; the
session transcript is never exposed to assertions.

Some skill regressions are trajectory-shaped and artifact-invisible: a
skill that stops delegating to the scout and reads files into main
context produces the same artifact at 10× the token cost; a worker that
skips its verifier dispatch can still leave a plausible-looking diff; a
skill that was told to dispatch scout-tier quietly dispatches the session
model. "The New SDLC With Vibe Coding" (adopted-practice record in
docs/external-playbooks.md) splits evaluation into output evals and
trajectory evals for exactly this reason. This spec promotes the recorded
v2 into the pipeline.

## Solution

The runner (`evals/run.sh`) exposes the session transcript to each
scenario's `assert.sh` via a new environment variable, `EVAL_TRANSCRIPT`
— an absolute path to the headless run's transcript (JSONL as produced by
the harness). Assertions remain plain shell: a scenario that cares about
trajectory greps `"$EVAL_TRANSCRIPT"`; a scenario that doesn't never
touches it.

- Opt-in per scenario: no existing `assert.sh` is edited by this spec,
  and every existing evalset passes unchanged.
- If the harness run produces no locatable transcript, the runner sets
  `EVAL_TRANSCRIPT` to an empty string and prints a warning; an assertion
  that requires it must fail with a message saying the transcript was
  unavailable (never silently pass).
- Typical assertions: expected dispatches present
  (`grep -q '"subagent_type":"scout"'`), banned patterns absent (no
  `Read` of a path the skill promises to delegate), gate steps reached.
- `.claude/skills/evals/SKILL.md` and `.claude/skills/evals/reference.md`
  document the variable, the
  opt-in stance, and one worked trajectory-assertion example; the "v1
  grades artifacts only" line is updated to name the v2 mechanism.

## Requirements

- R1: `evals/run.sh` sets `EVAL_TRANSCRIPT` for every `assert.sh`
  invocation, pointing at the scenario run's transcript file, or empty
  (with a runner warning) when none is locatable.
- R2: Existing evalsets pass with no edits — the variable's presence is
  the only observable change for artifact-only scenarios.
- R3: At least one committed scenario exercises a trajectory assertion
  (a new scenario for an existing evalset, asserting an expected dispatch
  or the absence of a banned pattern) and passes.
- R4: `.claude/skills/evals/SKILL.md` + `.claude/skills/evals/reference.md`
  document `EVAL_TRANSCRIPT`,
  keep artifact assertions primary, and keep the ~10-line failure-message
  budget for trajectory failures too.
- R5: The antigravity mirror (`antigravity/.agents/workflows/evals.md`)
  receives the equivalent documentation, or — if Agent Manager runs
  expose no transcript file — a reviewed carve-out recorded as evidence,
  never a silent skip (CLAUDE.md's mirroring convention); plugin.json is
  bumped; some task's `Touch:` lists these paths.

## Out of scope

- Rewriting existing scenarios to add trajectory assertions — they
  accrete when regressions bite, same as evalsets themselves.
- Structured trajectory parsing (JSON-path assertion helpers) — plain
  grep against the JSONL is v2's whole mechanism; helpers are v3 if greps
  prove too brittle.
- CI wiring — unchanged from the v1 scope decision.

## Acceptance criteria

- [ ] `grep -q "EVAL_TRANSCRIPT" evals/run.sh && bash -n evals/run.sh` (R1)
- [ ] `./evals/run.sh breakdown` passes with no scenario edits (R2 — paid
      headless run; human-launched).
- [ ] `grep -rl "EVAL_TRANSCRIPT" evals/*/ | grep -q assert.sh` — at least
      one committed scenario asserts against the transcript (R3).
- [ ] `grep -q "EVAL_TRANSCRIPT" .claude/skills/evals/SKILL.md || grep -q "EVAL_TRANSCRIPT" .claude/skills/evals/reference.md` (R4)
- [ ] `grep -q "EVAL_TRANSCRIPT" antigravity/.agents/workflows/evals.md` or
      an evidence file records the reviewed carve-out; plugin.json version
      is higher than before (R5).

## Open questions

(none)
