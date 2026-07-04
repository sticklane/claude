# Task 01: Liveness-checked sweep, parked tasks, rescue branches

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: in-progress
Depends on: none
Priority: P1
Budget: 40 turns
Spec: ../SPEC.md (requirements R1–R10)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, antigravity/.agents/workflows/drain.md

## Goal

Drain's startup sweep is no longer blind: reference.md defines a
stale-lock liveness check (TaskList first, then a multi-worktree activity
scan with a 15-minute named grace window), parked-task control flow with a
4-extension zombie bound, the pid caveat, and the residual-risk note;
sweeps preserve `rescue/NN-<slug>-<shortsha>` branches instead of deleting
them, DONE bookkeeping deletes a task's rescues after its merge passes
gates, the worker prompt gains the vanished-worktree clause, and the
sweep-race BLOCKED verdict routing is defined. SKILL.md's step-1 and
step-4 sentences reference the check. The antigravity drain workflow
mirrors the semantics.

## Touch

The two drain skill files are the spec's whole scope; the antigravity
drain workflow is mirrored per CLAUDE.md convention. Must NOT touch:
autopilot or parallel skills (spec Out of scope), any harness config,
`.claude-plugin/plugin.json` (version bump deferred to this queue's
bump-carrying tasks — orchestrator-context 05 / ultra-mode 03 /
workflow-token-efficiency 05).

## Steps

1. Run every acceptance grep below and confirm each fails (RED).
2. Write the "Stale-lock liveness check" section in reference.md: R1's
   ordered procedure (TaskList → activity scan over the task's worktree
   and any `-t*` tournament worktrees/branches, newest of file mtimes
   excluding node_modules/.git and branch tip-commit times), the grace
   window as a named default of 15 minutes stated once (R3), the pid
   caveat (R4), and the residual-risk sentence (R10).
3. Amend SKILL.md steps 1 and 4 plus the reference section with R2's
   parked-task flow: park inside the window, keep draining others,
   re-check before the batch interview (sleeping out the remaining window
   when idle), sweep-and-return-to-step-1 on confirmed death, 4-extension
   zombie escalation (report, treat like blocked, status stays
   in-progress, one-line logs).
4. Replace the delete-outright sweep instructions in both files with R5's
   rescue-branch procedure (shortsha naming, tip-dedup, pre-existing
   rescue counts, worktrees force-removed first, forensic-only, post-Filter
   tournament losers unchanged).
5. Add R6's DONE-bookkeeping rescue cleanup at both exact insertion
   points, R7's clause inside the verbatim worker prompt block, R8's
   sweep-race verdict routing, and R9's step-1 rewording.
6. Mirror the semantics into antigravity/.agents/workflows/drain.md.
7. Run acceptance; run the three R-e2e promptable checks with one
   scout/`claude -p` call each given only the two amended files.

## Acceptance

- [ ] `grep -qi "grace window" .claude/skills/drain/reference.md` → exit 0, section names TaskList, the `-t*` sweep, mtimes and tip-commit signals
- [ ] `grep -qi "park" .claude/skills/drain/SKILL.md && grep -qi "park" .claude/skills/drain/reference.md` → exit 0; step-4 trigger mentions parked tasks; `grep -qi "zombie" .claude/skills/drain/reference.md` → exit 0 with the 4-extension bound in exactly one place
- [ ] `test "$(grep -o "15 min" .claude/skills/drain/reference.md | wc -l)" -le 1` → named-default rule holds
- [ ] `grep -qi "not a liveness signal" .claude/skills/drain/reference.md` → exit 0
- [ ] `grep -q "rescue/NN-<slug>-" .claude/skills/drain/reference.md && grep -q "rescue/" .claude/skills/drain/SKILL.md && ! grep -q "discard its branch/worktree" .claude/skills/drain/SKILL.md && ! grep -q "discard the dead run's worktree/branch" .claude/skills/drain/reference.md` → exit 0
- [ ] rescue cleanup present in SKILL.md's step-3 DONE bullet AND reference.md's DONE-bookkeeping passage (check each individually)
- [ ] `grep -q "worktree or branch disappears" .claude/skills/drain/reference.md` → exit 0, inside the worker prompt block
- [ ] `grep -qi "sweep race" .claude/skills/drain/reference.md || grep -qi "sweep race" .claude/skills/drain/SKILL.md` → exit 0; routing distinguishes task-status cases and never counts toward relaunch/tournament thresholds
- [ ] `grep -q "liveness check" .claude/skills/drain/SKILL.md` → exit 0
- [ ] `grep -qi "residual" .claude/skills/drain/reference.md || grep -qi "safety net" .claude/skills/drain/reference.md` → exit 0
- [ ] Three promptable e2e scenarios from the spec (4-min mtime → park; 40-min → sweep with named rescue branch; 4 windows of refreshing mtimes → zombie report) each answered correctly by a fresh agent given only the amended files
- [ ] `grep -qi "rescue" antigravity/.agents/workflows/drain.md` → exit 0 (mirror)
