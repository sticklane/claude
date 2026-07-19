# Task 01: Cross-spec admission model in drain's SKILL.md and reference.md

Status: pending
Depends on: none
Priority: P0
Budget: 20 turns
Spec: ../SPEC.md (requirements R1, R2, R4, R5, R6, R7, R8, R9, R11, R12)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md

## Goal

`/drain` widens from "at most one spec-level dispatch lease at a time" to
claiming up to 3 simultaneously-held, Touch-disjoint spec leases, with a
matching cross-spec task-admission layer and a two-level worker cap (each
spec's own `W` stays ≤5; all claimed specs together share one ≤10 pool).
`.claude/skills/drain/SKILL.md` stays ≤500 lines; the new admission-rule
prose lives in `.claude/skills/drain/reference.md`'s existing
"Rolling-window admission & merge (R1–R4)" section (renamed or extended to
cover the new rules).

## Touch

Both files in scope share the same admission-rule prose and must be edited
together as one coherent unit — this is why they are not split across
tasks (they are not Touch-disjoint from each other, and the exact wording
of SKILL.md's pointer must match what actually lands in reference.md).
Do not touch `.claude/rules/token-discipline.md` (task 02),
`antigravity/.agents/workflows/drain.md`, `codex/.agents/skills/drain/SKILL.md`,
or `.claude-plugin/plugin.json` (task 03), or any new test file under
`tests/` (task 04) — those are siblings' scope.

## Steps

1. Read ../SPEC.md in full, especially R1, R2, R4, R5, R6, R7, R9, R11, R12
   and their acceptance criteria — the design is fully pinned after 9
   critique rounds; this task implements it, it does not re-decide it.
2. In `SKILL.md`: remove the exact phrase "At most one dispatch lease is
   held at a time" and replace with a one-line pointer to the widened rule
   in reference.md (R1). Update the step-1 owner-lease claim procedure
   description to claim up to 3 simultaneously-held spec leases, pairwise
   Touch-footprint-disjoint (R1, R4, R5).
3. In `SKILL.md`: reconcile the existing "**Hard cap: W ≤ 5** on TOTAL live
   workers" statement (currently line 144) with the new two-level cap — a
   single spec's own `W` stays ≤5 (unchanged), but all claimed specs
   together share one ≤10 pool (R12). State this in place, or relocate it
   into reference.md as part of the R9 line-budget rebalancing — either is
   fine, but it must not ship unreconciled in either location.
4. In `reference.md`'s "Rolling-window admission & merge (R1–R4)" section:
   state that spec-level lease claiming (R1) fires independent of this
   section's own "these rules bind only when W > 1" preamble (R11) — a
   newly-claimed spec dispatches its first eligible task immediately even
   at drain's default W=1.
5. In the same section: keep same-spec semantics (Touch-disjointness,
   `Group:`-line co-admissibility, "runs only alone (window empty)")
   unchanged for a pair of tasks from the SAME claimed spec, but re-scope
   "window empty" explicitly to that task's own spec's in-flight set
   (never the global in-flight set across all claimed specs) — edit the
   existing sentence in place rather than leaving it standing unqualified
   alongside new prose (R2).
6. Add the new cross-spec layer: two tasks in different, both-claimed
   specs co-admit whenever their `Touch:` sets are disjoint, full stop — no
   `Group:` line and no window-empty check apply across specs (R2). Edit
   the existing co-admissibility sentence in place to state it is
   spec-scoped, rather than leaving it standing unqualified (R2).
7. State the two-level cap explicitly: a claimed spec's own `W` (≤5)
   still bounds its own concurrency; what's dropped is treating each
   claimed spec's budget as independently summable — all claimed specs
   instead share one global window capped at ≤10 total live workers,
   admitted via the existing Priority-then-path tie-break across the whole
   pool once it is full (R2, R12).
8. State R6: R1 (spec-claim eligibility) and R2 (task-admission
   eligibility) together are the complete, sole mechanism for cross-spec
   Touch collision detection — do not add a third, separate check anywhere
   (including `/breakdown`'s own decision-coupling test) while
   implementing this task.
9. In `reference.md`'s "Spec-completion review worker" section: when
   dispatching that worker for a spec whose diff range overlaps a path
   another concurrently-claimed spec's own committed
   `evidence/spec-review.md` already covers, the dispatch prompt names
   which lines/sections are attributable to THIS spec, cites the sibling's
   `evidence/spec-review.md` by path, and instructs the worker to exclude
   anything that file already covers (R7). Adopt the phrasing in
   `docs/memory/drain-dispatch-lessons.md:134-151` (the "already-green
   `evidence/spec-review.md`" language) verbatim.
10. In `reference.md`: state R8 — cross-spec merges from different claimed
    specs land through one single global serial merge queue in
    commit-arrival order, two specs' DONE verdicts arriving
    near-simultaneously never racing on the push, reusing today's
    intra-spec "merges stay serial in landing order" guarantee (the
    existing serial-merge-queue prose already in reference.md is currently
    scoped intra-spec only; this extends it explicitly to span
    concurrently-claimed specs).
11. Confirm `wc -l < .claude/skills/drain/SKILL.md` is ≤500 — relocate
    content into reference.md as needed (R9); do not just delete existing
    unrelated content to hit the budget.
12. Run `evals/lint-skill-size-gate.sh` and the full gate suite before
    calling this task done.

## Acceptance

- [ ] `grep -c "At most one dispatch lease is held at a time" .claude/skills/drain/SKILL.md` → 0
- [ ] `grep -ci "swarm" .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md` → combined count ≥ 3
- [ ] `grep -c "up to 3 simultaneously-held spec leases" .claude/skills/drain/reference.md` → ≥ 1
- [ ] `grep -c "≤10\|<= 10\|10 total" .claude/skills/drain/reference.md` → ≥ 1
- [ ] `wc -l < .claude/skills/drain/SKILL.md` → ≤ 500 (the file stands at 505 today, verified 2026-07-19 — already over budget before this task starts, so step 11's relocation into reference.md is mandatory, not conditional; satisfiable in-scope because both files are in Touch)
- [ ] `grep -A5 -i "already-green" .claude/skills/drain/reference.md | grep -ci "spec-review.md"` → ≥ 1
- [ ] `grep -ci "single global serial merge queue\|one single global" .claude/skills/drain/reference.md` → ≥ 1
- [ ] `grep -c "in-flight tasks from that task's OWN spec" .claude/skills/drain/reference.md` → ≥ 1 (this exact literal — earlier looser patterns were found vacuous, matching unrelated pre-existing substrings; do not substitute different wording)
- [ ] `grep -c '"Window empty" means zero live' .claude/skills/drain/reference.md` → 0 (the original unqualified sentence must be edited in place, not left standing)
- [ ] `grep -c "with every in-flight task — two tasks may run together" .claude/skills/drain/reference.md` → 0 (the original unqualified co-admissibility sentence must be edited in place, not left standing)
- [ ] `grep -c "fires independent of the per-spec" .claude/skills/drain/reference.md` → ≥ 1 (this exact literal — earlier looser patterns were found vacuous, matching unrelated pre-existing tournament/baton text; do not substitute different wording)
- [ ] `grep -c "Hard cap: W ≤ 5.*on TOTAL" .claude/skills/drain/SKILL.md` → 0
- [ ] `grep -c "on TOTAL" .claude/skills/drain/reference.md` → 0 (already 0 today, verified 2026-07-19 — a regression guard paired with the previous check, ensuring the unreconciled phrase is not merely relocated here; it certifies no work by itself)
- [ ] ``grep -c "own `W`" .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md`` → combined count ≥ 1 (anchor replaced 2026-07-19: the earlier `grep -c "W ≤ 5"` form already matched the very "Hard cap" line another check here removes, so it passed vacuously with no work; "own `W`" — the per-spec-cap phrasing this task's Goal and steps 3/7 mandate — is absent from both files today, verified 2026-07-19)
- [ ] `grep -ci "shared global window\|one shared global\|one global window\|shared pool" .claude/skills/drain/reference.md` → ≥ 1 (alternation widened 2026-07-19 to include step 7's own phrasing, so a worker following the step verbatim still matches)
- [ ] `git diff --name-only <task-base-commit>..HEAD | grep -c '.claude/skills/breakdown/\|antigravity/.agents/workflows/breakdown\|codex/.agents/skills/breakdown/'` → 0
- [ ] `bash evals/lint-skill-size-gate.sh` → exits 0
- [ ] Every project gate this repo runs at merge time (`specs/status.sh`, `claude plugin validate .`, every `tests/test_*.sh`, `./bin/check-agent-model-pins`, `evals/lint-ultra-gate.sh`, `evals/lint-skill-size-gate.sh`) exits 0

Depth ceiling (the phrase greps above): L0 text-presence against prose
skill procedure — the honest ceiling for a skill-text artifact. Behavioral
complement: `tests/test_drain_swarm_admission.sh` (task 04) exercises the
same admission algorithm as runnable logic, and a manual-pending human
read of the edited SKILL.md/reference.md sections at review confirms the
prose states the procedure the greps only sample.
