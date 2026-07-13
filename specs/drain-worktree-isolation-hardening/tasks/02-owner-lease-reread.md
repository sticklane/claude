# Task 02: Owner-lease re-read before every status-flip commit (R2)

Status: pending
Depends on: 01
Priority: P1
Budget: 18 turns
Spec: ../SPEC.md (requirement R2)
Touch: .claude/skills/drain/reference.md, .claude/skills/drain/SKILL.md

## Goal

The existing claim-time CAS re-read (multi-session-coordination R1: "after
committing, re-read the file at HEAD and confirm YOUR `Run-token` is the one
present") is extended to run immediately before EVERY subsequent
status-flip commit within the same claimed spec's dispatch/collect cycle —
not only at the initial claim. A mismatched `Run-token:` at any of these
re-reads means the session lost ownership mid-cycle (a crossed-yield race,
or a liveness-based reclaim by another session), and the flip is aborted,
never committed, with drain treating the spec as lost per the existing R2
refuse path from multi-session-coordination.

## Touch

Primary edit is `.claude/skills/drain/reference.md`'s "Owner lease"
section. `.claude/skills/drain/SKILL.md` gets only a short pointer from
step 2's existing "flip is compare-and-swap" paragraph to the expanded
reference.md text — do not restate the full re-read procedure in SKILL.md.
Do NOT touch R1's orchestrator-isolation text (task 01, already landed), the
preflight-sweep section (R3, task 03), or the branch-deletion ordering (R4,
task 04).

## Steps

1. Read `../SPEC.md`'s R2 requirement and Problem-section incident #2 in
   full.
2. Confirm the "failing test": `grep -c "re-read.*DRAIN-OWNER\|DRAIN-OWNER.*re-read" .claude/skills/drain/reference.md` currently returns 0.
3. Read `.claude/skills/drain/reference.md`'s "Owner lease" section and
   `.claude/skills/drain/SKILL.md` step 2's "flip is compare-and-swap"
   paragraph to find the exact language of the existing claim-time CAS
   re-read.
4. In reference.md's "Owner lease" section, add text stating the SAME
   re-read-and-confirm check runs immediately before EVERY subsequent
   status-flip commit within the claimed dispatch/collect cycle, using
   language that will match the acceptance grep below (a phrase like
   "before every subsequent status-flip commit" or "before every subsequent
   ... commit"). State the abort behavior on mismatch: the flip is never
   committed, and drain treats the spec as lost per the existing refuse
   path.
5. In SKILL.md step 2, add a one-line pointer from the existing "flip is
   compare-and-swap" paragraph to this expanded reference.md text (do not
   duplicate the procedure).
6. Run `bash evals/lint-ultra-gate.sh` and fix any drift.
7. Confirm the "green test": re-run the grep from step 2 (still 0 is
   expected — that phrase names the INITIAL claim only) and the R2
   acceptance grep below (should now be ≥ 1).

## Acceptance

- [ ] `grep -c "re-read.*DRAIN-OWNER\|DRAIN-OWNER.*re-read" .claude/skills/drain/reference.md` — record the value (informational; the spec's authoring-time baseline was 0 for the initial-claim-only phrasing, this criterion is not the pass/fail gate for R2)
- [ ] `grep -n "before every.*status-flip\|before every subsequent.*commit" .claude/skills/drain/reference.md` → ≥ 1 hit, located in the "Owner lease" section
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0
