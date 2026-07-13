Status: done
Depends on: none
Priority: P3
Budget: 4 turns
Discovered-from: specs/drain-rolling-window/tasks/05-ship-gates-and-mirrors.md
Spec: ../SPEC.md
Touch: antigravity/.agents/skills/breakdown/SKILL.md
Blocking: no

# Stale "group throughput mode" reference in antigravity breakdown/SKILL.md's Hand off section

`antigravity/.agents/skills/breakdown/SKILL.md`'s "Hand off" section still says "its group throughput mode hands you concurrent Agent Manager launches" — task 05 renamed that mode to the rolling window in `antigravity/.agents/workflows/drain.md`, so this cross-reference now points at terminology that no longer exists. One-line fix, left out of task 05's scope since it's a Hand off section detail, not the Group: grammar content task 05 owned.

## Steps

1. In `antigravity/.agents/skills/breakdown/SKILL.md`'s "Hand off" section, replace "its group throughput mode hands you concurrent Agent Manager launches" with wording naming the rolling window (matching `antigravity/.agents/workflows/drain.md`'s current terminology after task 05).

## Acceptance

- [x] `grep -c "group throughput mode" antigravity/.agents/skills/breakdown/SKILL.md` → 0 (verifier PASS; evidence/09-fix-stale-group-mode-antigravity-handoff.md)
- [x] `grep -ci "rolling.window" antigravity/.agents/skills/breakdown/SKILL.md` → 3 (verifier PASS; evidence/09-fix-stale-group-mode-antigravity-handoff.md)

## Discovered

- `.claude/skills/breakdown/SKILL.md`'s Hand off section (line ~122-123) still describes throughput in pre-rolling-window terms ("dispatch independent groups concurrently") — doesn't use the retired literal phrase so was out of this task's Touch, but is stale-adjacent — see specs/drain-rolling-window/tasks/13-breakdown-handoff-throughput-wording-stale-adjacent.md
