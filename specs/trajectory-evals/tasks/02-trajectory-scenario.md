# Task 02: committed trajectory-assertion scenario

Status: in-progress
Depends on: 01
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirement R3)
Touch: evals/breakdown/

<!-- PLAN (build step 1):
Create evals/breakdown/02-scout-delegation/ modeled on 01-small-spec:
  - allowed-tools.txt: same set (Task tool present so scout can be spawned).
  - setup.sh: fixture git repo with MULTIPLE existing source files whose
    sourcing interdependencies are non-obvious, and a 2-requirement spec
    that extends existing code — so breakdown's step-2 file-dependency
    check is genuinely unclear and delegates to a scout (per breakdown
    SKILL.md step 2). No open questions.
  - assert.sh: R2 artifact checks (>=2 task files w/ Status/Depends on/
    ## Acceptance + backticked cmd; Parallelization section) FIRST, THEN a
    loud EVAL_TRANSCRIPT guard (empty -> fail with "transcript"), THEN the
    trajectory grep '"subagent_type":"scout"'.
Order of build: write assert.sh; test criterion-2 (empty EVAL_TRANSCRIPT
fails loudly) directly against a hand-built fixture with artifacts present;
then criterion-1 grep. Criterion-3 (live paid run) stays Manual-pending.
Risk: exact JSONL field name unconfirmable without a paid run -> reversible
default = documented Claude Code stream-json Task tool `subagent_type`
input param; recorded as Decision + Manual-pending (task-01 precedent).
-->

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

- [ ] `grep -rl "EVAL_TRANSCRIPT" evals/breakdown/*/assert.sh` finds the
      new scenario's `assert.sh`
- [ ] The new scenario's `assert.sh` fails loudly (non-zero, with a
      message naming the transcript as unavailable) when given an empty
      `EVAL_TRANSCRIPT` — test this directly: `EVAL_TRANSCRIPT="" bash
evals/breakdown/02-*/assert.sh` (from within a fixture dir with the
      expected artifacts already present) exits non-zero and prints a
      message mentioning "transcript"
- [ ] **Manual-pending** (paid headless run, human-launched): `./evals/run.sh
breakdown` passes including the new scenario —
      docs/memory/unattended-worker-tool-limits.md
