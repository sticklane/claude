# Task 01: COVERAGE.md tier table, lint-eval-coverage.sh, and its self-test

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. -->

Status: done
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

- [x] `bash tests/test_eval_coverage_lint.sh` → exit 0, with a
      failing-fixture case per R2 violation class
      → PASS (exit 0): one fixture per class — no-coverage-row,
      tier-a-too-few-scenarios, tier-a-no-adversarial, tier-b-missing-test,
      tier-c-empty-reason — plus a conforming tree. Evidence:
      specs/eval-coverage-tiers/evidence/01-coverage-table-and-lint.md
- [x] `test -f evals/COVERAGE.md && grep -c 'lint-eval-coverage'
evals/COVERAGE.md` → ≥ 1 (file exists and names its lint; phrase
      0 today, verified 2026-07-19)
      → PASS: grep -c = 2 (≥ 1).
- [x] `bash evals/lint-eval-coverage.sh; test $? -ne 0` → exit 0 at
      THIS task's close (the real tree still has known Tier A gaps —
      the lint must report them, not pass; spec-level green is task
      08's closing criterion)
      → PASS: lint reports 17 Tier A gap violations and exits 1, so
      `test $? -ne 0` → exit 0.

## Discovered

- critique already satisfies the Tier A bar (2 scenarios incl.
  `evals/critique/02-adv-gameable-criterion`), so it is absent from the 17
  gap findings — guidance for task 07's R4 existence-conditional (no stub;
  dedupes against task 07's scope).
- The 17 real-tree gaps span breakdown (no adv), build/drain/evals
  (1 scenario + no adv), and distill/gate/idea/onboard/prioritize
  (0 scenarios) — the exact set tasks 02–07 must close for task 08's
  lint-green criterion (no stub; dedupes against tasks 02–08).
- lint-eval-coverage.sh passes vacuously when `.claude/skills` is missing
  or empty under `$ROOT`/`LINT_ROOT` (nullglob empty loop → "OK", exit 0)
  — late code-review finding on this task's dispatch; stub
  `09-lint-vacuous-pass-missing-skills-dir.md`.
