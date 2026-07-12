# Task 01: human-blockers rule + CLAUDE.md pointer

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: pending
Depends on: none
Priority: P1
Budget: 4 turns
Spec: ../SPEC.md (requirement R1)
Touch: .claude/rules/human-blockers.md, CLAUDE.md

## Goal

New always-on rule `.claude/rules/human-blockers.md` defines: the
`## Agent-filed blockers` section marker, the entry grammar
(`- [ ] <ISO date> · <source path> · <ask|run|provision|decide> — <one-line action>`),
open-items-only (not a log), same-commit filing and deletion, the
bootstrap rule (no HUMAN.md → create title + section), and
agents-never-edit-prose-outside-the-section. CLAUDE.md gets a one-line
pointer citing the rule. Keep the rule short — grammar + five rules, not
an essay.

## Acceptance

- [ ] `test -f .claude/rules/human-blockers.md && grep -qi 'Agent-filed blockers' .claude/rules/human-blockers.md` → hits (anchor 0-hit everywhere before this spec)
- [ ] `grep -qi 'human-blockers' CLAUDE.md` → hit (0 today, verified)
- [ ] `wc -l < .claude/rules/human-blockers.md` → < 60
