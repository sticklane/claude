# Task 03: antigravity /idea mirror gets its own grounding-check step

Status: pending
Depends on: none
Priority: P1
Budget: 8 turns
Spec: ../SPEC.md (requirement R7)
Touch: antigravity/.agents/skills/idea/SKILL.md

## Goal

`antigravity/.agents/skills/idea/SKILL.md` gains an equivalent
grounding-check step, inserted between antigravity's own current step 1
(Scout) and step 2 (Interview) — antigravity's SKILL.md has its own
independent 5-step numbering (1. Scout, 2. Interview, 3. Write the spec, 4. Adversarial pass, 5. Hand off), NOT `.claude`'s 6-step one; do not
apply `.claude`'s renumbering instruction here. Inserting the step
renumbers antigravity's own steps 2-5 to 3-6. The new step describes the
fresh/stale/absent decision logic INLINE, in its own words (the 90-day
`Verified:` window and the branching from Solution/R2/R3) — it does NOT
cite `check-freshness.sh`'s path, since that's `.claude`-only tooling and
antigravity has no runtime shape to invoke a `.claude`-rooted script from
(a non-resolving cross-reference otherwise). Step 4 ("Adversarial pass")
contains one internal cross-reference, "step 5's hand-off," which becomes
"step 6's hand-off" in the same edit.

## Touch

Do not touch `.claude/skills/idea/SKILL.md` or
`.claude/skills/idea/test-fixtures/` — those are tasks 01 and 02. Do not
touch `antigravity/.agents/workflows/idea.md` — confirmed (per the spec)
to be a thin launcher stub with no step text of its own; nothing to
mirror there.

## Steps

1. Read `antigravity/.agents/skills/idea/SKILL.md` in full; confirm its
   current 5-step structure and the "step 5's hand-off" cross-reference
   in step 4 (re-verify fresh — don't trust the spec's line numbers).
2. Insert the new grounding-check step between steps 1 and 2, in
   antigravity's own words: name the 90-day window and the fresh/stale/
   absent branching (fresh → cite existing doc location, no research
   dispatch; stale/absent → dispatch research the existing way, then
   write/refresh a `Verified: <today>` stamp) — no citation of
   `check-freshness.sh`'s path anywhere in this step.
3. Renumber old steps 2-5 to 3-6.
4. Update step 4's "step 5's hand-off" reference to "step 6's hand-off"
   (step 4 itself is now step 5 after renumbering — the cross-reference
   inside it still points at the hand-off step, now numbered 6).

## Acceptance

- [ ] `grep -c "90.day\|90 day" antigravity/.agents/skills/idea/SKILL.md` → 1 or more
- [ ] `grep -c "check-freshness.sh" antigravity/.agents/skills/idea/SKILL.md` → 0
- [ ] `grep -c "step 6's hand-off" antigravity/.agents/skills/idea/SKILL.md` → 1 or more
- [ ] `grep -n "^## [0-9]\." antigravity/.agents/skills/idea/SKILL.md` — manually confirm exactly 6 numbered steps, sequential 1-6, with the new grounding-check step at position 2
