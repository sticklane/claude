# Task 04: align ~/automation/HUMAN.md (cross-repo)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: 01
Priority: P2
Budget: 3 turns
Spec: ../SPEC.md (requirement R5)
Touch: /Users/sjaconette/automation/HUMAN.md, specs/human-blockers-doc/evidence/04-automation-align.md

## Goal

~/automation/HUMAN.md gains an empty `## Agent-filed blockers` section
below its narrative; narrative untouched. CROSS-REPO: record automation's
HEAD SHA in the evidence file BEFORE editing; work per
docs/memory/drain-dispatch-lessons.md (worktree the other repo);
automation's own commit conventions apply (it has a check.sh gate;
docs-only change).

## Acceptance

- [ ] `grep -qi 'Agent-filed blockers' /Users/sjaconette/automation/HUMAN.md` → hit
- [ ] `git -C ~/automation diff <recorded-base> -- HUMAN.md` (base SHA from the evidence file) → additions only, all inside the new section
- [ ] `test -s specs/human-blockers-doc/evidence/04-automation-align.md` → base SHA + diff summary recorded
