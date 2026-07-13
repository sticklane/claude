# Task 03: Mechanical preflight sweep at drain startup (R3)

Status: in-progress
Depends on: 02
Priority: P1
Budget: 22 turns
Spec: ../SPEC.md (requirement R3)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md

## Goal

At drain startup (gen-1, before step 1's spec-scoped work begins), drain
runs one mechanical pass that: (a) identifies every `DRAIN-OWNER.md` under
the drained scope whose owner liveness is ALL STALE and reclaims each
exactly as the existing per-spec reclaim does; (b) enumerates every
checkout/worktree of the repo the VCS reports and prunes any with no
corresponding live `in-progress` task or live session, using a mechanically
defined "live session" test with a fail-safe skip-don't-prune when
liveness can't be determined. This sweep covers EVERY spec in the drain
run's launched scope, not only the one about to be claimed, replacing the
manual "kill any zombie drains" ritual. It reports a one-line summary in
the existing gen-1 startup advisories.

## Touch

Primary edit is `.claude/skills/drain/SKILL.md`'s gen-1 startup sequence
(add the sweep as a new startup step, using the literal phrase "mechanical
preflight sweep" so the acceptance grep matches, and a one-line summary
alongside the existing session-sweep/hub-economics advisories). Put the
sweep's mechanics (stale-lease reclaim reuse, worktree enumeration, the
"live session" liveness definition, and the fail-safe skip rule) in
`.claude/skills/drain/reference.md` to keep SKILL.md's addition small — it's
already at 517 lines against a 500-line convention. Do NOT touch R1's
orchestrator-isolation text (task 01) or R2's owner-lease re-read text
(task 02), both already landed, or the branch-deletion ordering (R4, task
04, not yet landed).

## Steps

1. Read `../SPEC.md`'s R3 requirement and Problem-section incident #3 in
   full.
2. Confirm the "failing test": `grep -c "mechanical preflight sweep"
.claude/skills/drain/SKILL.md` currently returns 0.
3. Read `.claude/skills/drain/SKILL.md`'s "Gen-1 startup advisories" section
   and `.claude/skills/drain/reference.md`'s existing per-spec reactive
   reclaim (in "Owner lease") and the existing "stale-lock liveness"
   definition, so the new sweep reuses rather than redefines that logic.
4. In reference.md, document the sweep's two mechanical passes: (a) reclaim
   every spec-under-scope's dead `DRAIN-OWNER.md` lease using the existing
   liveness definition (newest of the last commit touching that spec's
   `specs/<slug>/` path, or its in-progress tasks' stale-lock signals) plus
   the foreign-reclaim tightening already in R3's spec text (stale signals
   AND no worktree/checkout on the task's branch); (b) enumerate every
   checkout/worktree the VCS reports and prune any with no corresponding
   live `in-progress` task or live session — define "live session"
   mechanically (a session reported by the harness's live-session listing,
   e.g. `claude agents --json`, whose `cwd` resolves into that worktree's
   path, mirroring `.claude/rules/concurrent-sessions.md`'s own pre-flight)
   and state the fail-safe using this exact phrase: "skip that worktree
   rather than prune" — this literal wording is required (confirmed absent
   from both files at task start), the acceptance grep below is not
   lenient to paraphrase.
5. In SKILL.md, add the sweep as a gen-1 startup step using the literal
   phrase "mechanical preflight sweep," scoped explicitly to EVERY spec in
   the drain run's launched scope (not just the one about to be claimed),
   and add its one-line summary (leases reclaimed, worktrees pruned) to the
   existing "Gen-1 startup advisories" list, stated best-effort/never-
   blocking like its neighbors.
6. Check `.claude/skills/drain/SKILL.md`'s line count (`wc -l`). Your net
   addition to SKILL.md must not exceed 6 lines (this sweep's mechanics
   belong in reference.md, which has no line-budget convention) — this
   keeps task 05's closing line-budget trim achievable.
7. Run `bash evals/lint-ultra-gate.sh` and fix any drift.
8. Confirm the "green test": re-run the grep from step 2, and the two
   anchor-phrase greps in Acceptance below — all should now return ≥ 1.

## Acceptance

- [ ] `grep -c "mechanical preflight sweep" .claude/skills/drain/SKILL.md` → ≥ 1
- [ ] `grep -c "skip that worktree rather than prune" .claude/skills/drain/reference.md` → ≥ 1 (confirmed absent — baseline 0 — at task start; this is the fail-safe skip rule's specific anchor, distinct from the pre-existing generic "fail-safe/skip" hits already present in this file)
- [ ] `grep -n "live session" .claude/skills/drain/reference.md` shows YOUR
      new mechanical definition (a session reported by the harness's
      live-session listing whose `cwd` resolves into the worktree's path),
      not only the pre-existing "foreign live session" phrase already at
      reference.md:62 — confirm by reading the surrounding lines you added
- [ ] Net new lines added to `.claude/skills/drain/SKILL.md` by this task's
      diff ≤ 6 (`git diff HEAD~1 -- .claude/skills/drain/SKILL.md`)
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0
