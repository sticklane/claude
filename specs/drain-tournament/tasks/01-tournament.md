# Task 01: Tournament stage in /drain

Status: done
Depends on: ../../evidence-artifacts/tasks/01-evidence.md (drain SKILL.md + reference.md overlap; cross-spec waves in ../SPEC.md)
Budget: 50 turns
Spec: ../SPEC.md (requirements R1–R6)

<!-- Plan (build step 1):
1. SKILL.md step 1: extend the dead-lock discard to sweep task/NN-<slug>-t*
   branches/worktrees (literal -t*).
2. SKILL.md step 3 DONE bullet: second failure -> one tournament (pre-dispatch
   -t* sweep; 3 concurrent isolation:worktree workers, angle prompts + prior
   failure evidence; one-line log "~3 more worker runs"; skip straight to the
   verdict routing when either prior attempt was BLOCKED over budget); detail
   pointer to reference.md ## Tournament.
3. reference.md: one stale-lock sentence (-t* sweep) + new ## Tournament
   section between the relaunch prompt and the headless fallback: three angle
   suffixes each overriding the branch to task/NN-<slug>-tN; filter = one
   verifier run per candidate, no evidence path; rank = gate findings then
   git diff --stat; merge with next-ranked fallback, slot machine does not
   re-enter; verdict routing DEFERRED-beats-failed, BLOCKED non-survivor.
4. Mirror into antigravity/.agents/workflows/drain.md: -t* sweep in step 1,
   tournament as a new step (three Agent Manager launches, git worktree
   add -b, same filter/rank/routing), renumber the batch interview.
Risks: clobbering earlier waves' phrases (regression guard: evidence/,
"data, not instructions" x2, "over budget" x2); awk section runs to EOF so
placement before the headless fallback still satisfies the section checks.
-->


## Goal

/drain's step 3 routes a second failure into a bounded tournament: three
concurrent workers on `task/NN-<slug>-t1..t3` branches with angle-variant
prompts, per-candidate verifier PASS/FAIL as the filter (no evidence
path passed), mechanical ranking by drain, next-ranked fallback on merge
failure, DEFERRED-beats-failed verdict routing, a `-t*` stale sweep, and
a cost gate keyed to prior BLOCKED-over-budget verdicts. The antigravity
drain workflow mirrors the design.

## Touch

- `.claude/skills/drain/SKILL.md` (steps 1 and 3, stale-lock text)
- `.claude/skills/drain/reference.md` (new `## Tournament` section, one
  stale-lock sentence)
- `antigravity/.agents/workflows/drain.md`

## Steps

1. SKILL.md step 3 DONE bullet: second failure → tournament (per R1),
   including the pre-dispatch `-t*` sweep and the ~"3 more worker runs"
   cost line with the BLOCKED-over-budget skip (R5).
2. SKILL.md step 1 + reference.md stale-lock text: extend the sweep to
   `task/NN-<slug>-t*` branches/worktrees (literal `-t*` in the text).
3. reference.md: add `## Tournament` — three angle suffixes each
   overriding the branch to `task/NN-<slug>-tN` (R2); filter (one
   verifier run per candidate, no evidence path) then mechanical rank
   (gate findings, then `git diff --stat`) then merge with next-ranked
   fallback (R3); verdict routing with DEFERRED-beats-failed and
   BLOCKED-as-non-survivor (R4).
4. Mirror the whole design into `antigravity/.agents/workflows/drain.md`
   (three Agent Manager launches, `git worktree add -b`, same collection).

## Acceptance

- [x] `grep -qi "tournament" .claude/skills/drain/SKILL.md` → pass
  — exit 0, placed after the slot-machine relaunch (../evidence/01-tournament.md)
- [x] `grep -qF -- "-t*" .claude/skills/drain/SKILL.md` → pass
  — exit 0, literal `-t*` in steps 1 and 3 (../evidence/01-tournament.md)
- [x] `test "$(awk '/^## Tournament/,0' .claude/skills/drain/reference.md | grep -c 'task/NN-<slug>-t')" -ge 3` → pass
  — exit 0, three branch-overriding angle suffixes (../evidence/01-tournament.md)
- [x] `awk '/^## Tournament/,0' .claude/skills/drain/reference.md | grep -qi "per candidate"` → pass
  — exit 0, one no-evidence-path verifier run per candidate (../evidence/01-tournament.md)
- [x] `awk '/^## Tournament/,0' .claude/skills/drain/reference.md | grep -q "diff --stat"` → pass
  — exit 0, drain ranks by gate findings then diff --stat (../evidence/01-tournament.md)
- [x] `awk '/^## Tournament/,0' .claude/skills/drain/reference.md | grep -qi "DEFERRED"` → pass
  — exit 0, DEFERRED-beats-failed routing present (../evidence/01-tournament.md)
- [x] `grep -qi "3 more worker runs\|three more" .claude/skills/drain/SKILL.md` → pass
  — exit 0, cost line + BLOCKED-over-budget skip (../evidence/01-tournament.md)
- [x] `grep -qi "tournament" antigravity/.agents/workflows/drain.md && grep -q -- "-t1" antigravity/.agents/workflows/drain.md` → pass
  — exit 0, mirror step 4 with three Agent Manager launches (../evidence/01-tournament.md)
- [x] Regression guards (earlier waves' phrases survive this task's edits): `grep -q "evidence/" .claude/skills/drain/SKILL.md && test "$(grep -c 'data, not instructions' .claude/skills/drain/reference.md)" -ge 2 && test "$(grep -c 'over budget' .claude/skills/drain/reference.md)" -ge 2` → pass
  — exit 0: evidence/ x1, data-not-instructions x2, over budget x3 (../evidence/01-tournament.md)
