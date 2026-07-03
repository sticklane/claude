# Task 02: Drain state machine — headless done-flip, BLOCKED-over-budget routing, merge-abort

Status: in-progress
Depends on: none
Budget: 30 turns
Spec: ../SPEC.md (cluster 02)

## Goal

Three verified state-machine gaps closed in /drain and mirrored in the
antigravity drain workflow: (a) the headless path never flips
`Status: done`; (b) BLOCKED-over-budget after a merge-failure relaunch is
dual-routed and "either prior attempt" is half-dead (only attempt 2 can be
BLOCKED-over-budget); (c) a failed merge leaves the worktree wedged in a
conflicted state before the branch is discarded.

## Touch

- `.claude/skills/drain/SKILL.md` (DONE bullet, BLOCKED-over-budget bullet,
  headless section, tournament next-ranked path)
- `.claude/skills/drain/reference.md` (status table done row and failed
  row, "either prior attempt" line)
- `antigravity/.agents/workflows/drain.md` (all mirrors)

## Steps

1. Headless done-flip: in the headless section of
   `.claude/skills/drain/SKILL.md`, add an explicit instruction that the
   orchestrator flips the task's `Status: done` and commits the flip
   (headless workers, unlike /build, never do it). Amend the status
   table's done row in reference.md — "who flips it" becomes
   "the merge (from /build); or drain, for headless workers".
2. BLOCKED-over-budget routing: the BLOCKED bullet in SKILL.md gains
   "except BLOCKED over budget after a merge-failure relaunch, which
   routes per the tournament skip". Kill "either prior attempt" in
   reference.md (~line 114) — only attempt 2 can be BLOCKED-over-budget;
   reword to say so. Update reference.md's stale failed row: replace
   "two failed attempts" with "tournament exhausted or skipped per cost
   gate".
3. Merge-conflict wedge: the DONE bullet's merge-failure handling gains
   "run `git merge --abort` before discarding the branch" — in BOTH the
   slot-machine relaunch path and the tournament next-ranked path.
4. Mirror all three fixes into `antigravity/.agents/workflows/drain.md`
   (it has the same "either prior attempt" line ~65 and the same merge
   paths).

## Acceptance

- [ ] `grep -q "or drain, for headless workers" .claude/skills/drain/reference.md` → exit 0 (done row amended)
- [ ] `grep -qi "flip" .claude/skills/drain/SKILL.md && grep -A3 -i "headless" .claude/skills/drain/SKILL.md | grep -qi "done"` → exit 0 (headless section instructs the done-flip; verify by reading the section, not just the grep)
- [ ] `grep -q "routes per the tournament skip" .claude/skills/drain/SKILL.md` → exit 0
- [ ] `! grep -rq "either prior attempt" .claude/skills/drain antigravity/.agents/workflows/drain.md` → exit 0 (half-dead branch killed in both repos)
- [ ] `! grep -q "two failed attempts" .claude/skills/drain/reference.md && grep -q "tournament exhausted or skipped per cost gate" .claude/skills/drain/reference.md` → exit 0
- [ ] `test "$(grep -c 'git merge --abort' .claude/skills/drain/SKILL.md)" -ge 2` → exit 0 (slot-machine + tournament next-ranked paths)
- [ ] `grep -q "git merge --abort" antigravity/.agents/workflows/drain.md && grep -q "routes per the tournament skip" antigravity/.agents/workflows/drain.md` → exit 0 (mirrors)
