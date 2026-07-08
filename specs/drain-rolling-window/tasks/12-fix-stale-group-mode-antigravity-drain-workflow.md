Status: in-progress
Discovered-from: specs/drain-rolling-window/tasks/07-fix-stale-group-mode-reference.md
Spec: ../SPEC.md
Blocking: no

# Stale "group mode" cross-reference in the antigravity drain workflow mirror's push-guard paragraph

Task 07 fixed `.claude/skills/drain/SKILL.md`'s push-guard parenthetical ("drain's own group mode follows it" → "drain's own rolling-window merges follow it"), scoped only to that file. `antigravity/.agents/workflows/drain.md` (the antigravity mirror) carries the identical stale phrase at lines 237-238: "**Push guard (canonical; build cites this, and drain's own group mode follows it, extended here to every bookkeeping commit...**". Per CLAUDE.md's mirroring convention, this ships un-mirrored until a follow-up task carries the equivalent fix (the antigravity file's own rolling-window content already exists elsewhere, e.g. line 172 — only this one cross-reference paragraph is stale).

Decision (2026-07-06): apply the known fix — replace the stale phrasing at `antigravity/.agents/workflows/drain.md` lines ~237-238 ("drain's own group mode follows it", line-wrapped as "drain's own group / mode follows it") with the wording task 07 used in `.claude/skills/drain/SKILL.md` line ~249: "drain's own rolling-window merges follow it".

## Acceptance

- [ ] `! grep -q "drain's own group" antigravity/.agents/workflows/drain.md` → exits 0 (stale phrase gone; currently present at line 237)
- [ ] `grep -q "rolling-window merges" antigravity/.agents/workflows/drain.md` → exits 0 (task 07's wording in place; currently absent)
