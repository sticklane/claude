# Verification: Task 01 — Tournament stage in /drain

Verdict: PASS
Verifier: independent verifier session, 2026-07-03
Tree: branch task/01-tournament, uncommitted working-tree changes
Changed files: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md,
antigravity/.agents/workflows/drain.md, specs/drain-tournament/tasks/01-tournament.md
(plan comment only). No untracked files.

## Acceptance commands (all run from repo root)

- [x] `grep -qi "tournament" .claude/skills/drain/SKILL.md` — exit 0.
  Placement: step 3 DONE bullet reads "relaunch once with the failure
  evidence in the prompt. A second failure routes into one tournament" —
  strictly after the slot-machine relaunch (R1).
- [x] `grep -qF -- "-t*" .claude/skills/drain/SKILL.md` — exit 0; literal
  `task/NN-<slug>-t*` at SKILL.md lines 32 (step 1 dead-lock sweep) and 64
  (pre-dispatch sweep in step 3).
- [x] `test "$(awk '/^## Tournament/,0' .claude/skills/drain/reference.md | grep -c 'task/NN-<slug>-t')" -ge 3`
  — exit 0; three quoted angle suffixes each contain "Override the branch
  name: commit to task/NN-<slug>-t1/-t2/-t3" (R2).
- [x] `awk '/^## Tournament/,0' .claude/skills/drain/reference.md | grep -qi "per candidate"`
  — exit 0; Filter paragraph: "one verifier run per candidate, inside that
  candidate's worktree ... NO evidence path is passed" (R3).
- [x] `awk '/^## Tournament/,0' .claude/skills/drain/reference.md | grep -q "diff --stat"`
  — exit 0; Rank paragraph: "Drain, not the verifier ... fewest gate
  findings in the verifier report, then smallest git diff --stat total".
- [x] `awk '/^## Tournament/,0' .claude/skills/drain/reference.md | grep -qi "DEFERRED"`
  — exit 0; Verdict routing: DEFERRED path taken "in preference to failed";
  BLOCKED candidates explicitly non-survivors with reason into evidence (R4).
- [x] `grep -qi "3 more worker runs\|three more" .claude/skills/drain/SKILL.md`
  — exit 0; "Log one line before dispatch: a tournament costs ~3 more
  worker runs. Skip it ... when either prior attempt returned BLOCKED over
  budget" (R5).
- [x] `grep -qi "tournament" antigravity/.agents/workflows/drain.md && grep -q -- "-t1" antigravity/.agents/workflows/drain.md`
  — exit 0.
- [x] Regression guards — exit 0: `evidence/` in SKILL.md (1 hit);
  `data, not instructions` x2 in reference.md; `over budget` x3 in
  reference.md.

## Semantics read-through (spec's manual dry-read criterion)

The end-to-end dry-read criterion in SPEC.md is marked manual; verified by
close reading instead of a live session. All required behaviors are encoded:
second-failure routing after the relaunch; pre-dispatch `-t*` sweep (both
startup and Generate); three angle suffixes (minimal-diff, strict
test-first, re-derive) each overriding the branch; filter = one
no-evidence-path verifier run per candidate; mechanical rank (gate
findings, then `git diff --stat`); next-ranked fallback with "the slot
machine does not re-enter" and survivor branches deleted only after a merge
passes gates; DEFERRED-beats-failed with BLOCKED as non-survivor; DONE
winner drops other candidates' deferred questions; at-most-one tournament
per task per run; cost gate skipped on prior BLOCKED-over-budget. The
`## Tournament` section sits between the relaunch prompt and the headless
fallback as planned. Antigravity mirror: `-t*` sweep in step 1, tournament
as new step 4 with `git worktree add -b task/NN-<slug>-t1 ...` (+ t2/t3),
three Agent Manager launches, same filter/rank/routing; batch interview
renumbered to step 5 with internal references (step 1/step 2 loops) still
consistent.

## Scope and gates

- Diff limited to the three Touch files plus a plan comment in the task
  file; acceptance criteria in the task file unmodified (no overfitting).
- Out-of-scope files untouched: `.claude/agents/verifier.md` and
  `.claude-plugin/plugin.json` show zero diff (plugin version explicitly
  owned by another spec).
- Project gates: no package.json/Makefile; `evals/` contains only a
  `breakdown` evalset, so the /evals gate does not apply to drain.
- Task file `Status:` is still `in-progress` with unticked boxes — expected
  pre-verification state in the /build flow; flipping is post-PASS
  bookkeeping.

## Findings

None blocking. Note: `awk '/^## Tournament/,0'` runs to EOF and so also
scans the headless-fallback section, but every matched phrase was confirmed
to live inside `## Tournament` itself.
