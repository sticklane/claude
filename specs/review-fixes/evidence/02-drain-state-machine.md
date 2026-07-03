# Verification: Task 02 — Drain state machine

Verdict: **PASS** (one scope-creep finding, non-blocking)

Verified: 2026-07-03, working tree of branch `task/02-drain-state-machine`
(uncommitted changes, verified as-is) at
`/Users/sjaconette/claude/.claude/worktrees/agent-a443e7789b322d966`.
Verifier: independent (did not write this code).

## Acceptance criteria

All commands run from the repo root; exit codes observed directly.

1. ✓ `grep -q "or drain, for headless workers" .claude/skills/drain/reference.md`
   → exit 0. Status-table done row now reads
   `| done | branch merged, project gates green | the merge (from /build); or drain, for headless workers |`.

2. ✓ `grep -qi "flip" .claude/skills/drain/SKILL.md && grep -A3 -i "headless" .claude/skills/drain/SKILL.md | grep -qi "done"`
   → exit 0. Read-verification (as the criterion requires, not just the grep):
   SKILL.md lines 56–60 (headless-fallback passage in step 2):
   > Headless workers, unlike /build workers, never flip the task's
   > `Status: done`: after a headless DONE verdict and the post-merge
   > acceptance re-run, drain itself flips the status to `done` and
   > commits the flip.
   This genuinely instructs the orchestrator (drain) to flip and commit.
   reference.md headless section (lines 207–210) mirrors it: "on DONE,
   that includes flipping the task's `Status: done` and committing the
   flip yourself (a headless worker, unlike /build, never writes it)".

3. ✓ `grep -q "routes per the tournament skip" .claude/skills/drain/SKILL.md`
   → exit 0. The BLOCKED bullet (SKILL.md lines 89–93) adds the
   exception routing BLOCKED-over-budget-after-relaunch to the
   tournament's verdict routing instead of `Status: blocked`.

4. ✓ `! grep -rq "either prior attempt" .claude/skills/drain antigravity/.agents/workflows/drain.md`
   → exit 0. Reworded in all three files: SKILL.md lines 79–84 and
   reference.md lines 111–116 and antigravity drain.md step 4 now say
   the skip triggers when attempt 2 (the relaunch) returned BLOCKED over
   budget, with the reasoning that attempt 1 must have returned DONE to
   reach a merge, so only attempt 2 can be BLOCKED-over-budget.

5. ✓ `! grep -q "two failed attempts" .claude/skills/drain/reference.md && grep -q "tournament exhausted or skipped per cost gate" .claude/skills/drain/reference.md`
   → exit 0. Failed row: `| failed | tournament exhausted or skipped per cost gate; evidence recorded | /drain |`.

6. ✓ `test "$(grep -c 'git merge --abort' .claude/skills/drain/SKILL.md)" -ge 2`
   → exit 0 (count = 2). Read-verified both are in the right paths:
   slot-machine path (line 67, "run `git merge --abort` first (a failed
   merge leaves the checkout wedged in a conflicted state), then slot
   machine") and tournament next-ranked path (lines 76–78, "If the
   tournament winner's merge fails, likewise run `git merge --abort`
   before moving to the next-ranked survivor"). reference.md's
   tournament Merge section also gained it (1 occurrence, correct spot).

7. ✓ `grep -q "git merge --abort" antigravity/.agents/workflows/drain.md && grep -q "routes per the tournament skip" antigravity/.agents/workflows/drain.md`
   → exit 0. Antigravity mirror has 2 `git merge --abort` occurrences
   (step 3 slot-machine, step 4 next-ranked-survivor bullet), the
   BLOCKED-over-budget routing exception, and the attempt-2 rewording —
   all three fixes mirrored.

## Gates

- No standard build/lint/test gates exist (prose/skill repo; no
  package.json/Makefile). CLAUDE.md's /evals gate applies only to skills
  with a stored evalset; `evals/` contains only `breakdown` — no drain
  evalset, so nothing to run.
- SKILL.md remains well under the 500-line convention limit.

## Overfitting check

Changes are substantive prose edits, not keyword-stuffing: each grep
target sits inside a coherent instruction with rationale, and the
attempt-2 rewording carries an explanation rather than a bare phrase
swap. No test files exist to have been gamed.

## Scope-creep findings

- `.claude-plugin/plugin.json`: version bumped 0.6.0 → 0.6.1. Not in the
  task's Touch list. Motivated by the repo convention "bump `version` in
  `plugin.json` whenever skill behavior changes" (CLAUDE.md), but the
  Touch list is binding — reporting the convention rather than accepting
  the edit. Non-blocking; caller should decide whether to keep or split
  the bump.
- `specs/review-fixes/tasks/02-drain-state-machine.md`: Status
  pending → in-progress. This is the drain dispatch lock on the task
  file itself (expected workflow state), noted for completeness.
