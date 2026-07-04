# Task 02: Autopilot pre-cap baton + parallel collect-phase baton

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: in-progress
Depends on: 01
Priority: P1
Budget: 30 turns
Spec: ../SPEC.md (requirements R2, R3)
Touch: .claude/skills/autopilot/SKILL.md, .claude/skills/autopilot/reference.md, .claude/skills/parallel/SKILL.md, antigravity/.agents/workflows/autopilot.md, antigravity/.agents/workflows/parallel.md

## Goal

Autopilot's launched run writes the baton and relaunches at its last safe
boundary BEFORE `--max-turns` (~80%), judging advancement by new commits
since launch — no new commits since the previous baton means stop for
spec repair, not respawn. Parallel's collect/merge phase merges what's
verified, commits, writes a baton listing unmerged branches, and
relaunches when collection will outlive the session budget. Both cite
drain's baton grammar and generations cap (from task 01) rather than
restating them.

## Touch

Depends on 01 for the baton grammar and cap. Must NOT touch: the drain
skill files, breakdown, runtimes/, the workboard scanner, plugin.json.

## Steps

1. Confirm acceptance greps fail (RED).
2. Add the pre-emptive baton rule to autopilot SKILL.md with the exact
   config detail (the ~80% boundary and flag notes) in its reference.md.
3. Add the collect-phase boundary rule to parallel SKILL.md.
4. Mirror both to antigravity ("write the baton and stop" adaptation).
5. Run acceptance.

## Acceptance

- [ ] `grep -qi "baton" .claude/skills/autopilot/SKILL.md` → exit 0 with the pre-cap (~80% of --max-turns) boundary and the no-new-commits → spec-repair rule
- [ ] `grep -qi "baton" .claude/skills/parallel/SKILL.md` → exit 0 with the merge-verified/commit/list-unmerged-branches rule
- [ ] Both files reference the generations cap rather than restating trigger mechanics (read-verified)
- [ ] `grep -qi "baton" antigravity/.agents/workflows/autopilot.md && grep -qi "baton" antigravity/.agents/workflows/parallel.md` → exit 0
