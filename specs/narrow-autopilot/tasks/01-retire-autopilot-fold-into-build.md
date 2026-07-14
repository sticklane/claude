# Task 01: Delete /autopilot, create build/reference.md, fold gate+triggers into build/SKILL.md

Status: pending
Depends on: none
Priority: P0
Budget: 8 turns
Spec: ../SPEC.md (requirements R1, R2)
Touch: .claude/skills/autopilot/, .claude/skills/build/SKILL.md, .claude/skills/build/reference.md

## Goal

`.claude/skills/autopilot/` (SKILL.md and reference.md) no longer exists.
`.claude/skills/build/reference.md` is a new file holding six sections moved
from the old `autopilot/reference.md`: scoped-permissions JSON template,
`/goal` pattern, containment ladder, headless template, pre-cap baton
boundary, and failure recovery (the last landing alongside the walk-away
contract's escalation triggers, per Solution). The "background worktree
agent" section is dropped, not moved — `build/reference.md` gets one line
pointing unattended fire-and-forget work at `/drain` instead.
`.claude/skills/build/SKILL.md` gains, near its start (after its existing
first-30-lines launch-authorization block, not inside it): the go/no-go
classification gate, the walk-away contract's two escalation triggers
(verbatim, including the literal sentence "Two triggers escalate to a
human"), and a pointer to `build/reference.md`'s pre-cap baton section.

## Touch

This task owns `.claude/skills/autopilot/` (deleted) and both
`.claude/skills/build/{SKILL.md,reference.md}`. Do not touch any other
skill's pointers to autopilot (onboard, drain, gate, breakdown) — those are
Task 02. Do not touch docs/, README.md, CLAUDE.md, codex/, or antigravity/
— those are later tasks. This task restructures `build/SKILL.md`'s
top section (new content lands after its existing launch-authorization
block) — a hard prerequisite noted in the spec's Problem section for the
sibling `build-doc-currency-check` spec, which must not be decomposed or
drained concurrently against this same file (see Task 06's sequencing
check).

## Steps

1. Read `.claude/skills/autopilot/SKILL.md` and `.claude/skills/autopilot/reference.md`
   in full to identify the six section boundaries in `reference.md` (by
   heading) and the classification-gate / escalation-trigger content in
   `SKILL.md`.
2. Create `.claude/skills/build/reference.md` with the six sections moved
   verbatim (byte-identical body text per section), in the order given in
   Solution. Replace the "background worktree agent" section with one line
   pointing unattended fire-and-forget work at `/drain`.
3. Edit `.claude/skills/build/SKILL.md`: insert the go/no-go classification
   gate and the walk-away contract's two escalation triggers (verbatim,
   preserving the literal sentence "Two triggers escalate to a human" —
   see Acceptance below for why this exact wording matters) after the
   existing first-30-lines launch-authorization block, plus a pointer to
   `build/reference.md`'s pre-cap baton section.
4. Delete `.claude/skills/autopilot/` (both files).
5. Run `bash evals/lint-ultra-gate.sh` — `build/SKILL.md` is one of the
   four ultra-path skills it checks; this task edits it directly.

## Acceptance

- [ ] `[ ! -d .claude/skills/autopilot ]`
- [ ] `.claude/skills/build/reference.md` exists and contains the six named
      sections. For each of permissions template, `/goal` pattern,
      containment ladder, headless template, pre-cap baton: extract the
      section's text from `git show HEAD~1:.claude/skills/autopilot/reference.md`
      (pre-deletion) by its heading and diff it against the corresponding
      section in `build/reference.md` — the diff must be empty. Failure
      recovery is exempt from the strict empty-diff check (its content may
      be adjacent to the new escalation-trigger material) but its full text
      must be present verbatim somewhere in `build/reference.md`.
- [ ] `! grep -q "background worktree agent" .claude/skills/build/reference.md`
      (the section is dropped, not moved) and `grep -q '/drain' .claude/skills/build/reference.md`
      (the one-line pointer replacing it exists).
- [ ] `.claude/skills/build/SKILL.md` contains the classification gate and
      the two escalation triggers, plus a pointer to `build/reference.md`'s
      baton section.
- [ ] `grep -qF 'Two triggers escalate to a human' .claude/skills/build/SKILL.md`
      (pins the literal sentence a later task's mirror-manifest canary line
      depends on — the coverage test skips silently if this source leg
      lacks the phrase, so this fold-in must preserve it verbatim, not
      just convey the same meaning in different words).
- [ ] `bash evals/lint-ultra-gate.sh` exits 0.
