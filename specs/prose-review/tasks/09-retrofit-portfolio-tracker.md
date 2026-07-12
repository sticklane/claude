# Task 09: retrofit portfolio-tracker orientation docs

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: 03
Priority: P2
Budget: 4 turns
Spec: ../SPEC.md (requirement R9)
Touch: ~/portfolio-tracker, specs/prose-review/evidence/retrofit-portfolio-tracker.md

## Goal

Run /prose-review (per its shipped SKILL.md) over ~/portfolio-tracker's orientation
docs — README.md, plus AGENTS.md when present, else docs/*.md — record
BEFORE counts (Vale + rubric), apply fixes IN that repo per its commit
conventions (worktree the other repo per
docs/memory/drain-dispatch-lessons.md), record AFTER counts with residual
Vale jargon itemized. PRECONDITION before any commit there: verify the
repo's push-triggered workflows ignore docs-only commits (paths-ignore
**.md or equivalent) or use its documented docs-safe path; record the
check in the evidence file.
EXTRA CAUTION: this repo auto-pushes on commit -> auto-deploy; the
paths-ignore precondition is MANDATORY before committing, and if not
satisfiable, stop with the finding recorded instead of committing.

## Acceptance

- [ ] `test -s specs/prose-review/evidence/retrofit-portfolio-tracker.md` → before/after Vale AND rubric counts + CI-precondition line present (MANUAL: content)
- [ ] Fixes committed and pushed in the target repo (portfolio-tracker), now that the CI precondition is confirmed satisfied

## Progress

- 2026-07-12 — Attempt 1 (gen 9) returned BLOCKED. Done: full Vale+rubric+reader review of README.md and docs/*.md, BEFORE/AFTER counts, 6 Google-style fixes applied on disk (uncommitted) in the target-repo worktree, evidence file + task close-out committed on the toolkit branch and merged. Remaining: a human must confirm the portfolio-tracker GCP Cloud Build trigger is disabled or docs-path-filtered before the on-disk README fix can be committed and pushed (auto-deploy risk). Target-repo worktree left uncommitted at /private/tmp/claude-501/-Users-sjaconette-claude/2ef60b45-2141-4410-8eb4-a2985babd531/scratchpad/pt-worktree, branch task/09-retrofit-portfolio-tracker — discarded per the no-persistent-worktree convention; a future attempt starts fresh once unblocked.

## Answers

- 2026-07-12 /drain — Q: Is the GCP Cloud Build trigger for portfolio-tracker (per cloudbuild.yaml, deploys Cloud Run on push to main) disabled, or does it have an includedFiles filter excluding README.md/docs/**? A (Steven, live conversation): the trigger is disabled. The docs-only commit is safe to make and push from a fresh target-repo worktree; re-verify the trigger is still disabled in-worktree before committing (state may have changed since this answer), then proceed to commit and push per the task's Steps.
