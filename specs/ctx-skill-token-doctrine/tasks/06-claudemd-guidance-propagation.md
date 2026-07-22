# Task 06: Propagate index-first doctrine to onboard + token-discipline (R6)

Status: in-progress
Depends on: none
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirement R6)
Touch: .claude/skills/onboard/SKILL.md, antigravity/.agents/skills/onboard/SKILL.md, .claude/rules/token-discipline.md

## Goal

The doctrine the toolkit distributes teaches index-first reading. (a) The
`/onboard` skill procedure (`.claude/skills/onboard/SKILL.md`, a prose
procedure) gains an instruction: when the target repo has a ctx index
(`.context/` present or `ctx` resolves per the skill's binary-resolution
order), write an "Answering structure questions" section — modeled on
fooszone's, including the reading ladder's rung order — into the repo's
**CLAUDE.md** (conventions file, per onboard's orientation/conventions
split). (b) The toolkit's token-discipline rule
(`.claude/rules/token-discipline.md`) names index-first reading as the
default for structural questions, before scout dispatch. The onboard change
is mirrored into the antigravity onboard skill.

## Touch

`.claude/skills/onboard/SKILL.md` + its antigravity mirror, and
`.claude/rules/token-discipline.md` (a rule — NOT mirrored in antigravity;
there is no antigravity rules tree). This task shares no files with the ctx
SKILL.md chain (tasks 01/03/04/05) or scout (task 02), so it is
parallel-safe with the no-dep group. Do NOT touch the ctx SKILL.md,
scout.md, or plugin.json here.

## Steps

1. Read the relevant `/onboard` procedure region (it already recommends
   `Bash(ctx *)` in the allowlist when a repo is indexed — extend that).
2. Add the "Answering structure questions" instruction: gate on index
   presence, name CLAUDE.md as the destination, include the reading-ladder
   rung order.
3. Mirror the instruction into
   `antigravity/.agents/skills/onboard/SKILL.md`.
4. Add index-first-for-structural-questions guidance to
   `.claude/rules/token-discipline.md` in the structural-questions /
   scout-dispatch context.
5. Run the acceptance commands.

## Acceptance

- [ ] `grep -q 'Answering structure questions' .claude/skills/onboard/SKILL.md` → exit 0
- [ ] `grep -q 'Answering structure questions' .claude/skills/onboard/SKILL.md && grep -qi 'CLAUDE.md' .claude/skills/onboard/SKILL.md && grep -qi '\.context\|indexed' .claude/skills/onboard/SKILL.md` → exit 0 (names CLAUDE.md + the index-presence condition)
- [ ] `grep -qi 'ctx' .claude/rules/token-discipline.md` → exit 0 (index-first named in structural-question context)
- [ ] `grep -qi 'structure question\|ctx\|index-first' antigravity/.agents/skills/onboard/SKILL.md` → exit 0 (mirror coverage)
