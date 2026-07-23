# Task 01: Add the empty-diff pre-check as verifier.md's new step 0

Status: done
Depends on: none
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirements R1, R2)
Touch: .claude/agents/verifier.md

## Goal

`.claude/agents/verifier.md`'s Process gains a new step 0, run before the
existing step 1 ("read the acceptance criteria"), that mechanically checks
for an empty diff and short-circuits to `FAIL` before any acceptance
command, project gate, or scope-creep check runs. The check must correctly
handle untracked new files, tasks with no `Touch:` list, and reuse the
file's own existing base-resolution logic rather than inventing a second
one — see Steps for the exact behavior each acceptance criterion checks.

## Touch

Only `.claude/agents/verifier.md`. Do not change the Output format
section's verdict-value list (still exactly `PASS`/`FAIL`/`INCOMPLETE`),
and do not restate or duplicate step 6's base-resolution logic — step 0
must reuse it by reference (e.g. "resolve the base the same way step 6
does"), not redefine it.

**Depth ceiling:** this is a prompt-file edit — every acceptance criterion
below is L0 (text-presence / phrase-anchored), the deepest feasible level
without a live model run. Behavioral complement: confirming the verifier
*actually* skips steps 1–7 on a real no-op diff, before running any
acceptance command, is deferred to a human or follow-up eval run, per the
spec's own Depth ceiling note.

## Steps

1. Read `.claude/agents/verifier.md` in full, including step 6 (the
   append-only task-file diff check, which already defines base
   resolution: "the base commit the caller passed, or in a drain/
   tournament worktree the worktree's merge-base with the default
   branch") and the Output format section (step 7's mandatory
   per-requirement criteria-adequacy line).
2. Also read `.claude/skills/build/SKILL.md`'s "Pre-commit review"
   section for the staging pattern it already uses
   (`git add -A && git diff <step0-base> --numstat`) to see untracked new
   files.
3. Insert a new step 0, before the existing step 1, implementing:
   - Resolve the base exactly as step 6 does (passed base, or — in a
     drain/tournament worktree — the worktree's merge-base with the
     default branch). Do not define a separate "missing base" branch;
     if no base can be resolved at all, proceed to step 1 unchanged.
   - Stage everything first (`git add -A`, mirroring build's own
     pre-commit review gate) so untracked new files are visible, then
     diff against the resolved base.
   - If the task file carries a `Touch:` list, restrict the diff to
     those paths; if it carries none (a bare SPEC.md, or a pre-`Touch:`
     task file), diff unrestricted — do not treat an empty Touch list as
     "diff nothing" (that would always false-FAIL).
   - If the resulting diff is empty, return `FAIL` immediately with the
     single finding "no changes made — working tree matches base,"
     explicitly stating that steps 1–7 (all of them, including step 7's
     mandatory per-requirement criteria-adequacy line) are skipped and no
     acceptance command ran — state this exemption in the same
     paragraph/sentence as (or immediately adjacent to) wherever the
     Output format section's adequacy-line requirement is described, so
     the two don't silently contradict each other.
   - If the diff is non-empty (or no base could be resolved), proceed to
     step 1 exactly as today.
4. Run every acceptance command below and confirm all pass.

## Acceptance

- [ ] `grep -qi 'no changes made' .claude/agents/verifier.md` → matches
- [ ] `grep -qi 'empty diff\|diff is empty' .claude/agents/verifier.md` → matches
- [ ] `grep -qi 'git add -A\|stage.*untracked\|untracked' .claude/agents/verifier.md` → matches (untracked-file trap explicitly handled)
- [ ] `grep -qiE 'skip(s|ping)? (steps? 1|all remaining steps)' .claude/agents/verifier.md` → matches (skip scope stated as 1–7, or "all remaining steps" — not "2–7")
- [ ] `tr '\n' ' ' < .claude/agents/verifier.md | grep -qiE 'adequacy[^.]*exempt|exempt[^.]*adequacy'` → matches (step-0 FAIL's exemption from the mandatory criteria-adequacy line is stated)
- [ ] `grep -qiE 'no (touch|touch-list|touch list)|without.*restrict' .claude/agents/verifier.md` → matches (no-Touch-list case addressed, not left undefined)
- [ ] MANUAL: the new step 0 is positioned before step 1 in the file's line order (`grep -n` both markers, confirm step 0's line number is lower)
- [ ] MANUAL: step 0's base-resolution language points at step 6's resolution (same fallback: passed base, or worktree merge-base with default branch) rather than defining an independent "missing base" branch
- [ ] MANUAL: the Output format section still lists exactly three verdict values (`PASS`/`FAIL`/`INCOMPLETE`) — unchanged
