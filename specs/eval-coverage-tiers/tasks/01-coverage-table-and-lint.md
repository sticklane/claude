# Task 01: COVERAGE.md tier table, lint-eval-coverage.sh, and its self-test

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. -->

Status: in-progress
Depends on: none
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirements R1, R2, R3)
Touch: evals/COVERAGE.md, evals/lint-eval-coverage.sh, tests/test_eval_coverage_lint.sh

## Goal

`evals/COVERAGE.md` exists with exactly one row per `[!_]*` skill dir
(the spec's tier table verbatim; Tier B rows carry repo-relative test
paths). `evals/lint-eval-coverage.sh` enforces R2's five violation
classes and exits 0 only on a conforming tree.
`tests/test_eval_coverage_lint.sh` proves the lint's own failure
behavior fixture-by-fixture, `runner-selftest.sh`-style.

## Steps

1. Read SPEC.md R1–R3, `evals/lint-ultra-gate.sh` (the invocation
   pattern to mirror), and `evals/runner-selftest.sh` (the self-test
   pattern).
2. Write the failing self-test first: a conforming fixture tree → 0,
   plus one failing fixture per violation class, each named in output.
3. Write the lint until the self-test is green.
4. Write COVERAGE.md from the spec's table. The lint against the REAL
   tree will still fail (Tier A gaps are tasks 02–07's work) — that is
   correct behavior now; do not weaken the lint to force early green.

## Acceptance

- [ ] `bash tests/test_eval_coverage_lint.sh` → exit 0, with a
      failing-fixture case per R2 violation class
- [ ] `test -f evals/COVERAGE.md && grep -c 'lint-eval-coverage'
  evals/COVERAGE.md` → ≥ 1 (file exists and names its lint; phrase
      0 today, verified 2026-07-19)
- [ ] `bash evals/lint-eval-coverage.sh; test $? -ne 0` → exit 0 at
      THIS task's close (the real tree still has known Tier A gaps —
      the lint must report them, not pass; spec-level green is task
      08's closing criterion)
