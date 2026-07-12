# Task 11: retrofit tdd-git-hooks orientation docs

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: 03
Priority: P2
Budget: 4 turns
Spec: ../SPEC.md (requirement R9)
Touch: ~/tdd-git-hooks, specs/prose-review/evidence/retrofit-tdd-git-hooks.md

## Goal

Run /prose-review (per its shipped SKILL.md) over ~/tdd-git-hooks's orientation
docs — README.md, plus AGENTS.md when present, else docs/*.md — record
BEFORE counts (Vale + rubric), apply fixes IN that repo per its commit
conventions (worktree the other repo per
docs/memory/drain-dispatch-lessons.md), record AFTER counts with residual
Vale jargon itemized. PRECONDITION before any commit there: verify the
repo's push-triggered workflows ignore docs-only commits (paths-ignore
**.md or equivalent) or use its documented docs-safe path; record the
check in the evidence file.

## Acceptance

- [ ] `test -s specs/prose-review/evidence/retrofit-tdd-git-hooks.md` → before/after Vale AND rubric counts + CI-precondition line present (MANUAL: content)
- [ ] MANUAL: after-state shows rubric findings resolved; residual Vale findings itemized as domain jargon
