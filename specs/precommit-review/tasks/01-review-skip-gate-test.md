# Task 01: model-free review-skip gate test

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P0
Budget: 12 turns
Spec: ../SPEC.md (requirement R6; gate command + patterns pinned in Solution)
Touch: tests/test_review_skip.sh

## Goal

`tests/test_review_skip.sh` exists and passes: a self-contained bash test
that builds a throwaway git repo (`mktemp -d`) with a recorded step-0
base, mid-stream commits, staged edits, unstaged edits, and untracked
files, then runs the spec's pinned gate command
(`git add -A && git diff <step0-base> --numstat`) plus the NON-product
classifier and <25 threshold, asserting seven cases: docs-only → skip,
tests-only → skip (including `.test.ts` / `.spec.ts` names), 24 product
lines → skip, 26 product lines → review, mixed docs+26-product → review,
untracked new 26-line product file → review, committed-then-modified
lines counted exactly once.

## Touch

Only the new test file. Do NOT edit build's SKILL.md (task 02) or the
antigravity workflow (task 03). The test encodes the SPEC's pinned
command and pattern list directly — it must stay green regardless of
whether task 02 has merged.

## Steps

1. Write the failing skeleton (seven named cases, default fail), confirm
   it fails, then implement case by case; follow sibling
   `tests/test_*.sh` output conventions; cleanup trap for temp dirs.
2. Implement the classifier exactly as pinned (pattern list verbatim
   from ../SPEC.md Solution; sum added+deleted over product paths).
3. Full `for t in tests/test_*.sh` sweep green; commit.

## Acceptance

- [ ] `bash tests/test_review_skip.sh` → exit 0, output names all seven cases as PASS
- [ ] `grep -c "git add -A" tests/test_review_skip.sh` → ≥ 1 (tests the pinned command, not a variant)
- [ ] `grep -cE "\.test\.|\.spec\." tests/test_review_skip.sh` → ≥ 1 (JS/TS test-name coverage)
- [ ] `for t in tests/test_*.sh; do bash "$t" || exit 1; done` → exit 0
