Status: pending
Depends on: none
Priority: P2
Budget: 8 turns
Discovered-from: specs/absorb-agent-tools/tasks/06-workboard-priority-select-unset.md
Spec: ../SPEC.md
Touch: antigravity/.agents/skills/workboard/workboard.py
Blocking: no

# Antigravity mirror of workboard.py missing task 06's PRIORITY_RE addition

Task 06 added `PRIORITY_RE` extraction to `.claude/skills/workboard/workboard.py` (a spec's `Priority:` header now flows through to the rendered `<select>`), but `antigravity/.agents/skills/workboard/workboard.py` (the mirror) was outside task 06's `Touch` and did not receive the equivalent change — no task in this spec lists it, and task 04 (the spec's attended closeout) is already done. Per CLAUDE.md's mirroring convention, this ships un-mirrored to the Antigravity port until a follow-up carries it.

## Steps

1. Read the current `.claude/skills/workboard/workboard.py`'s `PRIORITY_RE` addition (task 06) and port the equivalent change into `antigravity/.agents/skills/workboard/workboard.py`, verbatim where the antigravity mirror's structure matches.

## Acceptance

- [ ] `grep -n 'PRIORITY_RE' antigravity/.agents/skills/workboard/workboard.py` → pattern definition present, matching the Claude-side version's regex
- [ ] `diff <(grep -A2 'PRIORITY_RE' .claude/skills/workboard/workboard.py) <(grep -A2 'PRIORITY_RE' antigravity/.agents/skills/workboard/workboard.py)` → no meaningful divergence (path/import differences aside)
