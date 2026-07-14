# Task 01: Create the skill-doc size/TOC lint gate script

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Depends on: none
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (requirements R1, R2, R3)
Touch: evals/lint-skill-size-gate.sh

## Goal

A new standalone script `evals/lint-skill-size-gate.sh` exists that
mechanically checks the two CLAUDE.md authoring conventions across every
`.claude/skills/*/SKILL.md` and `.claude/skills/*/reference.md`: (a) no
SKILL.md exceeds 500 lines, (b) no reference.md over 100 lines lacks a
`## Table of contents` / `## Contents` heading (case-insensitive) within
its first 20 lines. It follows `evals/lint-ultra-gate.sh`'s conventions
exactly and is invoked directly — not wired into `evals/run.sh`. This task
only adds the script; it is expected to report violations (drain/SKILL.md
and 8 reference.md files currently fail) and does NOT need to exit 0 —
remediation lands in later tasks in this spec.

## Touch

Do not edit any `.claude/skills/*` file in this task — detection only, no
remediation. Do not edit `evals/run.sh`.

## Steps

1. Read `evals/lint-ultra-gate.sh` for the exact shape to mirror: `set -u`,
   `ROOT` resolved from `BASH_SOURCE`, a discovery loop, per-violation
   output, a final status line, non-zero exit on violation.
2. Write `evals/lint-skill-size-gate.sh`:
   - Discover files by glob (`.claude/skills/*/SKILL.md` and
     `.claude/skills/*/reference.md`), not a hardcoded list — a new
     skill's files must be covered automatically.
   - For each `SKILL.md`: if `wc -l` > 500, print
     `<path>:<count>: exceeds 500-line SKILL.md budget` and mark failure.
   - For each `reference.md`: if `wc -l` > 100 AND no line among the first
     20 lines matches (case-insensitive)
     `^## (Table of [Cc]ontents|Contents)\b`, print
     `<path>:<count>: missing TOC heading in first 20 lines` and mark
     failure.
   - Print a final `lint-skill-size-gate: OK` (all compliant) or
     `lint-skill-size-gate: FAIL` (any violation) line.
   - Exit 0 only if every checked file is compliant; exit 1 otherwise.
3. Make it executable (`chmod +x`) and run it against the current repo to
   confirm it correctly reports today's known violations (see Acceptance).

## Acceptance

- [x] `test -x evals/lint-skill-size-gate.sh` → file exists and is
      executable. Evidence: `executable:yes`.
- [x] `bash evals/lint-skill-size-gate.sh; echo "exit:$?"` → prints
      `lint-skill-size-gate: FAIL` and `exit:1` (remediation hasn't landed
      yet in this task; a green gate is this spec's final acceptance, not
      this task's). Evidence: prints `lint-skill-size-gate: FAIL` and `exit:1`
      (7 reference.md TOC violations remain).
- [ ] `bash evals/lint-skill-size-gate.sh 2>&1 | grep -q "drain/SKILL.md"` →
      match (the script correctly flags the current 517-line file).
      STALE CRITERION: drain/SKILL.md was trimmed to 489 lines by commit
      2f19e4d (already on main), so it is correctly NOT flagged. Script
      behavior is correct; the expected-517 fact is outdated.
- [ ] `bash evals/lint-skill-size-gate.sh 2>&1 | grep -c "missing TOC heading"`
      → 8 (drain/reference.md plus the 7 other over-100-line reference.md
      files with no qualifying heading today).
      STALE CRITERION: drain/reference.md gained a `## Table of contents`
      heading via commit 982b278 (already on main), so it is correctly NOT
      flagged. Script returns 7 (the 7 remaining offenders); behavior is
      correct, the expected-8 count is outdated.
- [x] `grep -c "evals/run.sh" evals/lint-skill-size-gate.sh` → 0 (the script
      must NOT reference or wire itself into `evals/run.sh`). Evidence: `0`.

## Decisions

- [2026-07-14 /drain] Acceptance criteria 3 and 4 anchored on a stale
  codebase snapshot (drain/SKILL.md at 517 lines, 8 reference.md TOC
  gaps) that this same drain run's task 03 already resolved (commits
  2f19e4d, 982b278) before this task dispatched. Reversible default
  taken by the worker: built the script to reflect current reality
  (correctly NOT flagging drain/SKILL.md; reporting 7 remaining TOC
  gaps) rather than forcing a false match against outdated numbers. An
  independent verifier confirmed the script is a correct, non-overfit
  implementation of the Goal. Reverse by editing the two criteria's
  expected values (517→489/non-match, 8→7) to match current reality, or
  by re-deriving them fresh if the spec is revisited.

## Discovered

- [2026-07-14 /drain] The spec's remaining tasks (02, 04, 05) may
  reference stale counts/expectations tied to the same pre-task-03
  snapshot this task hit — worth a pass confirming their acceptance
  criteria still match current reality before treating their gates as
  final. See `specs/skill-doc-size-guards/tasks/06-recheck-stale-counts.md`.
