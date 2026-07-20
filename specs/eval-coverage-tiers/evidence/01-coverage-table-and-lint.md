# Verification: Task 01 — coverage table and lint

Verdict: PASS

Base commit: f9778021fffd610c79304d445ab9cf463de2d7ec
Branch: task/01-coverage-table-and-lint (worktree
/home/user/claude/.claude/worktrees/agent-ac627c95e090bd260)

## Acceptance command 1

Command: `bash tests/test_eval_coverage_lint.sh`
Result: exit 0.
Output tail:

```
eval-coverage lint selftest: OK (conforming + 5 violation classes)
```

Confirmed by reading `tests/test_eval_coverage_lint.sh`: it builds a
conforming fixture (case 0, exit 0) plus exactly one fixture per R2
violation class:

- case 1: `no-coverage-row: dd` (skill dir `dd` added with no COVERAGE.md row)
- case 2: `tier-a-too-few-scenarios: aa` (1 conforming scenario, need >=2)
- case 3: `tier-a-no-adversarial: aa` (2 scenarios, neither NN-adv-\*)
- case 4: `tier-b-missing-test: bb` (Tier B row names a test file that was removed)
- case 5: `tier-c-empty-reason: cc` (Tier C row with blank reason cell)
  All 5 classes covered; each asserts non-zero exit AND the specific
  violation tag via grep on the lint's own output. Self-test isolates via
  `mktemp -d` + `LINT_ROOT` override, never touches the real repo tree.

## Acceptance command 2

Command: `test -f evals/COVERAGE.md && grep -c 'lint-eval-coverage' evals/COVERAGE.md`
Result: exit 0, count = 2 (>= 1). File exists and names its own lint
script twice (intro paragraph + "Run it directly" sentence).

## Acceptance command 3

Command: `bash evals/lint-eval-coverage.sh; test $? -ne 0`
Result: outer `test` exits 0 (i.e. lint's own exit code was non-zero:
observed 1). Lint reported 17 violations, ALL in the
`tier-a-too-few-scenarios` / `tier-a-no-adversarial` classes for
breakdown, build, distill, drain, evals, gate, idea, onboard,
prioritize — exactly the known Tier A evalset gaps this task
deliberately leaves for tasks 02-07. No `no-coverage-row`,
`tier-b-missing-test`, or `tier-c-empty-reason` violations appeared,
confirming COVERAGE.md's non-Tier-A rows are structurally conforming
already.

## R1 — evals/COVERAGE.md content

`ls .claude/skills` (excluding `_shared`) enumerates 21 skill dirs:
breakdown, build, critique, design, distill, drain, evals, factcheck,
fleet, gate, handoff, harness-audit, idea, list-specs, onboard,
prioritize, prose-review, qa-sweep, resume-handoff, workboard,
workflow-author.

COVERAGE.md has exactly 21 data rows, one per skill, no duplicates:

- Tier A (10): breakdown, build, critique, distill, drain, evals, gate,
  idea, onboard, prioritize — matches SPEC's proposed Tier A set
  exactly (idea, critique, breakdown, build, drain, evals, prioritize,
  distill, gate, onboard).
- Tier B (2): list-specs → `.claude/skills/list-specs/test_list_specs.py`;
  workboard → `.claude/skills/workboard/test_workboard.py` — paths
  match spec verbatim, both files exist (confirmed indirectly: real-tree
  lint run above raised no `tier-b-missing-test` violation).
- Tier C (9): design, factcheck, fleet, handoff, harness-audit,
  prose-review, qa-sweep, resume-handoff, workflow-author — matches
  SPEC's proposed Tier C set exactly (fleet, qa-sweep, factcheck,
  harness-audit, design, workflow-author, prose-review, handoff,
  resume-handoff). No empty reasons (confirmed: no
  `tier-c-empty-reason` violations in the real-tree lint run).

10 + 2 + 9 = 21 = skill-dir count. Set membership matches SPEC's
proposed tier table exactly; no skill listed twice.

## R2 — evals/lint-eval-coverage.sh

Read in full. Enforces all five violation classes with stable tags:
`no-coverage-row`, `tier-a-too-few-scenarios`, `tier-a-no-adversarial`,
`tier-b-missing-test`, `tier-c-empty-reason`. Parses COVERAGE.md's
markdown table via awk (4+ pipe-delimited columns, tier cell in
{A,B,C}), enumerates skill dirs with the spec's `[!_]*` glob, and
exits 0 only when `violations` stays 0. Pure bash/awk/grep — no model
calls, no `evals/run.sh` reference except a documentation comment
noting it is "never wired into evals/run.sh". Direct-invoke: runs
standalone via `bash evals/lint-eval-coverage.sh` with no
dependencies beyond the repo tree (confirmed by acceptance command 3
running clean).

## Append-only task-file check

Command: `git diff f9778021fffd610c79304d445ab9cf463de2d7ec --
specs/eval-coverage-tiers/tasks/01-coverage-table-and-lint.md`
Result: empty diff — no changes at all to the task file since base
(Status remains `in-progress`, acceptance checkboxes remain
unticked). An empty diff trivially satisfies "no edits outside the
allowed set." Note (not a FAIL per the given criteria, but worth
flagging to the caller): the worker never flipped Status to a
terminal value or ticked the acceptance checkboxes/added evidence
citations, despite the implementation being functionally complete and
all three acceptance commands passing.

## Touch scope check

Command: `git diff --name-only f9778021fffd610c79304d445ab9cf463de2d7ec`
Result:

```
evals/COVERAGE.md
evals/lint-eval-coverage.sh
tests/test_eval_coverage_lint.sh
```

Exactly matches the task's `Touch:` header (evals/COVERAGE.md,
evals/lint-eval-coverage.sh, tests/test_eval_coverage_lint.sh). No
scope creep; task file itself shows zero diff (see above).

## Commit history on this branch (informational)

```
5ad41c2 docs: add eval-coverage tier table (COVERAGE.md)
71d164a feat: add model-free eval-coverage lint
fa9937a test: add failing self-test for eval-coverage lint
f977802 drain: eval-coverage-tiers task 01 in-progress
```

TDD order observed: test → feat → docs, consistent with
quality-discipline.md's red/green/refactor commit-at-each-step
convention.

## Criteria-adequacy

- Acceptance command 1 (self-test green + fixture-per-class): L2
  behavior — actually executes the lint against constructed fixture
  trees and asserts both exit code and violation-tag text per class.
  Entails R3.
- Acceptance command 2 (COVERAGE.md exists + self-names lint): L1
  artifact-structure (existence + grep-count), acceptable per the
  task's own criterion phrasing (not a behavioral claim beyond file
  presence).
- Acceptance command 3 (real-tree lint reports gaps, doesn't
  false-pass): L2 behavior — executes the lint against the actual
  repo tree and asserts it correctly flags known incompleteness rather
  than trivially passing.
- R1 (tier table correctness): verified by direct enumeration/diffing
  against SPEC's proposed table — L1 artifact-structure, adequate for
  a table-conformance requirement with no separate behavioral claim
  (the behavioral enforcement is R2/command 3, already at L2).
- R2 (lint enforces 5 classes, model-free, direct-invoke): L2 —
  exercised directly via real-tree run (found exactly the classes
  expected: tier-a-\* only) and via the self-test's per-class fixtures.

No INCOMPLETE findings; all requirements this task closes (R1, R2, R3)
have L1/L2 evidence appropriate to their claim shape.
