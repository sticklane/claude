# Task 02: committed trajectory-assertion scenario

Status: done
Depends on: 01
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirement R3)
Touch: evals/breakdown/

## Goal

At least one committed scenario under `evals/breakdown/` exercises a
trajectory assertion via `EVAL_TRANSCRIPT` — asserting an expected
dispatch pattern or the absence of a banned pattern — demonstrating the
mechanism task 01 built actually works end to end.

## Touch

Only add a new scenario directory under `evals/breakdown/` (e.g.
`evals/breakdown/02-<name>/`). Do not edit `evals/breakdown/01-small-spec/`
or any other existing evalset. Do not touch `evals/run.sh` (task 01
owns it) or `.claude/skills/evals/` (task 03).

## Steps

1. Look at `evals/breakdown/01-small-spec/` (`prompt.txt`, `setup.sh`,
   `assert.sh`) as the model for scenario structure.
2. Create `evals/breakdown/02-scout-delegation/` (or a name reflecting
   what it actually checks) with its own `prompt.txt`/`setup.sh` running
   a small breakdown-shaped task, and an `assert.sh` that does its
   existing artifact checks (per R2, unaffected) **plus** a new
   trajectory check: `grep -q '"subagent_type":"scout"' "$EVAL_TRANSCRIPT"`
   (or the equivalent JSONL field this harness actually emits — confirm
   the field name by inspecting a real `transcript.jsonl` produced by
   task 01's change before hardcoding the grep pattern) to confirm
   `/breakdown`'s file-dependency-unclear step actually delegates to a
   `scout` agent rather than reading the codebase directly, per
   `.claude/skills/breakdown/SKILL.md` step 2's stated contract.
3. If `EVAL_TRANSCRIPT` is empty (runner warning case from task 01),
   the assertion must fail loudly with a message naming the transcript
   as unavailable — never silently pass.
4. Run the scenario locally to confirm both the artifact checks and the
   new trajectory check pass together.

## Acceptance

- [x] `grep -rl "EVAL_TRANSCRIPT" evals/breakdown/*/assert.sh` finds the
      new scenario's `assert.sh`
      — evidence/02-trajectory-scenario.md: returns only
      `evals/breakdown/02-scout-delegation/assert.sh`. — verifier PASS (2026-07-16 sweep)
- [x] The new scenario's `assert.sh` fails loudly (non-zero, with a
      message naming the transcript as unavailable) when given an empty
      `EVAL_TRANSCRIPT` — test this directly: `EVAL_TRANSCRIPT="" bash
evals/breakdown/02-*/assert.sh` (from within a fixture dir with the
      expected artifacts already present) exits non-zero and prints a
      message mentioning "transcript"
      — evidence/02-trajectory-scenario.md: exit 1, message
      "EVAL_TRANSCRIPT is empty or missing ... transcript unavailable". — verifier PASS (2026-07-16 sweep)
- [ ] **Manual-pending** (paid headless run, human-launched): `./evals/run.sh
breakdown` passes including the new scenario —
      docs/memory/unattended-worker-tool-limits.md
      — Manual-pending: unattended worker cannot launch a paid non-dry-run
      `claude -p` session. Plumbing confirmed: `EVAL_DRY_RUN=1 ./evals/run.sh
  breakdown` discovers `breakdown/02-scout-delegation` (2/2 scenarios).

## Decisions

- JSONL trajectory field unconfirmable without a paid run → defaulted to
  Claude Code's documented stream-json Task tool_use `subagent_type` input
  param (task-01 precedent). Grep is whitespace-tolerant
  (`"subagent_type"[[:space:]]*:[[:space:]]*"scout"`) so it matches both
  compact and spaced serializations. Reverse/adjust: run `./evals/run.sh
breakdown` once for real, inspect `session.log`, and if the field is
  nested/named differently, edit the grep in
  `evals/breakdown/02-scout-delegation/assert.sh`.
