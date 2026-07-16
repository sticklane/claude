# Verification: specs/trajectory-evals/tasks/02-trajectory-scenario.md

Verdict: PASS

## Criterion 1 — grep finds new assert.sh

Command: `grep -rl "EVAL_TRANSCRIPT" evals/breakdown/*/assert.sh`
Output: `evals/breakdown/02-scout-delegation/assert.sh`
Result: PASS.

## Criterion 2 — empty EVAL_TRANSCRIPT fails loudly

Built fixture via `EVAL_DIR=<tmp> bash evals/breakdown/02-scout-delegation/setup.sh`,
then hand-created `specs/toolkit/tasks/01-json-mode.md` and
`02-quiet-mode.md` (each with `Status:`, `Depends on:`, `## Acceptance`
with a backticked command) and appended a `## Parallelization` section to
`specs/toolkit/SPEC.md`, committed, then ran from within that dir:

```
EVAL_TRANSCRIPT="" bash <abs>/evals/breakdown/02-scout-delegation/assert.sh
```

Output: `ASSERT FAIL: EVAL_TRANSCRIPT is empty or missing; cannot check the
scout-delegation trajectory (transcript unavailable)`
Exit code: 1
Result: PASS (non-zero, mentions "transcript").

## Criterion 3 — Manual-pending / plumbing

Task file marks the criterion `**Manual-pending** (paid headless run,
human-launched)`, citing docs/memory/unattended-worker-tool-limits.md — did
NOT run a live `./evals/run.sh breakdown`. Confirmed discovery/plumbing:

```
EVAL_DRY_RUN=1 ./evals/run.sh breakdown
```

Output included:

```
DRY-RUN [claude-code] runner: claude -p "<prompt>" ... --allowed-tools Read,Edit,Write,Glob,Grep,Bash(git *),Bash(ls *),Bash(wc *),Task
PASS  breakdown/01-small-spec
DRY-RUN [claude-code] runner: ...
PASS  breakdown/02-scout-delegation
2/2 scenarios passed
```

Result: PASS (scenario DISCOVERED and plumbing resolves).

## Sanity checks

(a) assert.sh R2 checks confirmed exercised: the same fixture-artifact run
above required >=2 well-formed task files and a Parallelization section
before reaching the trajectory check (verified by reading assert.sh: R2
block precedes R3 block, lines 12-26 vs 28-42).

(b) Trajectory grep pass/fail with synthetic 1-line JSONL:

- `{"type":"tool_use","name":"Task","input":{"subagent_type":"scout",...}}`
  → `assert: all checks passed (2 task files, scout delegation present)`,
  exit 0.
- `{"type":"tool_use","name":"Read","input":{"file_path":"lib/args.sh"}}`
  → `ASSERT FAIL: transcript shows no scout delegation ...`, exit 1.
  Both as expected.

(c) Task-file diff vs base (fdcfb3cfab2e1d526186e2ce7e3150d3d6941658),
path-scoped:

```
git diff fdcfb3cfab2e1d526186e2ce7e3150d3d6941658 -- 'specs/trajectory-evals/tasks/*.md'
```

Only changes: (1) a `<!-- PLAN (build step 1): ... -->` comment block
inserted after the header fields, (2) `Status:` unchanged at
`in-progress` (already so at base — not altered by this diff), (3) one
purely cosmetic reflow at the very end of the Manual-pending bullet: the
continuation word "breakdown\`" moved from a 2-space-indented wrapped line
to column 0 — no word added/removed/reordered, same text content. No
Goal/Steps/Touch/Acceptance _content_ was altered. Flagged below as a
minor finding since it is technically an edit inside the Acceptance
section (whitespace-only, semantically inert).

## Scope creep check

`git diff fdcfb3cfab2e1d526186e2ce7e3150d3d6941658 --stat`:

```
 evals/breakdown/02-scout-delegation/allowed-tools.txt          |  1 +
 evals/breakdown/02-scout-delegation/assert.sh                  | 44 +++
 evals/breakdown/02-scout-delegation/prompt.txt                 |  1 +
 evals/breakdown/02-scout-delegation/setup.sh                   | 88 +++
 specs/trajectory-evals/tasks/02-trajectory-scenario.md         | 22 +++/-1
```

`git status --porcelain` on the worktree: clean (all committed). Matches
the task's `Touch: evals/breakdown/` (plus its own task file, permitted).
No edits to `evals/breakdown/01-small-spec/`, `evals/run.sh`, or
`.claude/skills/evals/` — consistent with the task's stated Touch
restriction. No scope creep found.

## Overfitting check

assert.sh's trajectory grep pattern (`"subagent_type":"scout"`) is a
generic JSONL field match, not keyed to any literal from the fixture's
spec/prompt text; it passed/failed correctly against independently
constructed synthetic transcripts in sanity check (b), not just the
fixture's own hypothetical output. No special-casing observed.

## Findings

- Minor: the task file's own Manual-pending bullet line was reflowed
  (whitespace-only) between base and current — technically inside the
  Acceptance section text, though content-identical. Not scope creep in
  the substantive sense (no criterion text changed), but worth noting for
  the append-only mechanical check.
