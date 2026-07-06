Status: draft
Priority: P2
Discovered-from: specs/absorb-agent-tools/tasks/06-workboard-priority-select-unset.md
Spec: ../SPEC.md
Blocking: no

# Antigravity mirror of workboard.py missing task 06's PRIORITY_RE addition

Task 06 added `PRIORITY_RE` extraction to `.claude/skills/workboard/workboard.py` (a spec's `Priority:` header now flows through to the rendered `<select>`), but `antigravity/.agents/skills/workboard/workboard.py` (the mirror) was outside task 06's `Touch` and did not receive the equivalent change — no task in this spec lists it, and task 04 (the spec's attended closeout) is already done. Per CLAUDE.md's mirroring convention, this ships un-mirrored to the Antigravity port until a follow-up carries it.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
