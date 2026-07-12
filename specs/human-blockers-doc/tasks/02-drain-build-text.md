# Task 02: drain files/clears entries; attended build blocked-stop pair

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: pending
Depends on: 01
Priority: P1
Budget: 6 turns
Spec: ../SPEC.md (requirements R2, R3)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, .claude/skills/build/SKILL.md

## Goal

Per SPEC R2: drain's exit-checklist step also files the FIVE
drain-collected entry types into the repo's HUMAN.md (each mapped to its
checklist section per the spec) in the same commit wave, and the batch
interview deletes a task's entry in the same commit as its ## Answers
write; manual-pending items are explicitly NOT drain-scanned. Per R3:
attended /build's blocked stop becomes a same-COMMIT two-edit pair (task
file's intra-file Status+Unblock atomicity unchanged; HUMAN.md entry
matches the Unblock type); drained workers never write HUMAN.md.
Ultra-path files: run `bash evals/lint-ultra-gate.sh` before committing.
SEQUENCING NOTE: if specs/drain-wake-cost/tasks/04 (drain SKILL.md
extraction) is still pending or in-progress, this task must not dispatch
until it merges (Touch overlap serializes this mechanically).

## Acceptance

- [ ] `grep -qi 'Agent-filed blockers' .claude/skills/drain/SKILL.md && grep -qi 'Agent-filed blockers' .claude/skills/build/SKILL.md` → hits
- [ ] MANUAL: five types mapped to sections; interview deletion same-commit; build pair same-commit, attended-scoped
- [ ] `bash evals/lint-ultra-gate.sh` → OK
