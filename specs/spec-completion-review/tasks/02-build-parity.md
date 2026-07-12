# Task 02: build close-out parity sentence for bare-SPEC runs

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Depends on: none
Priority: P2
Budget: 2 turns
Spec: ../SPEC.md (requirement R4)
Touch: .claude/skills/build/SKILL.md

## Goal

Build's close-out gains one sentence: a /build run whose target was a
bare SPEC.md (no tasks/) runs the spec-completion review over its diff
using the existing pre-commit review machinery (cite
specs/spec-completion-review); task-file /build runs are unchanged
(their per-task pass covers them). Anchor: "spec-completion review"
(0-hit in build SKILL.md today). Ultra-path file: run
`bash evals/lint-ultra-gate.sh` before commit.

## Acceptance

- [x] `grep -qi 'spec-completion review' .claude/skills/build/SKILL.md` → hit
  - verified: exit 0, hit in close-out at the added sentence (evidence/02-build-parity.md)
- [x] `bash evals/lint-ultra-gate.sh` → OK
  - verified: `lint-ultra-gate: OK — all ultra mentions gated in 4 files`, exit 0 (evidence/02-build-parity.md)
