# Task 01: Widen the ctx skill trigger surface (R1)

Status: done
Depends on: none
Priority: P1
Budget: 8 turns
Spec: ../SPEC.md (requirement R1)
Touch: .claude/skills/ctx/SKILL.md, antigravity/.agents/skills/ctx/SKILL.md

## Goal

The ctx skill auto-triggers on tool-directive and survey-shaped prompts, not
only question-shaped ones. The frontmatter `description:` line of
`.claude/skills/ctx/SKILL.md` gains tool-directive phrasing ("use ctx",
"with ctx"/"via ctx", "the ctx skill", "ctx the codebase") and survey
phrasing ("understand the codebase", "survey the repo structure",
"deep-dive the code structure"), while keeping the existing negative scope
("not for content/text search"). The antigravity mirror's description line is
updated in the same commit so mirror parity holds.

## Touch

Only the two `SKILL.md` files' frontmatter `description:` line. Do NOT touch
the skill body here (the body sections are R2/R3/R4/R7's tasks, which land
after this one on the same file). The description line is kept byte-identical
between the `.claude` file and the antigravity mirror — R1's acceptance diff
enforces that, so port the exact same description text to both.

## Steps

1. Read the current `description:` line in `.claude/skills/ctx/SKILL.md`.
2. Extend it with the tool-directive and survey trigger phrases above,
   preserving the existing "where is X defined / what calls X" phrases and
   the "Not for content/text search" negative scope. Keep it a single line.
3. Copy the identical new description line into the antigravity mirror
   `antigravity/.agents/skills/ctx/SKILL.md` frontmatter.
4. Run the acceptance commands.

## Acceptance

- [x] `sed -n 's/^description: *//p' .claude/skills/ctx/SKILL.md | grep -q 'use ctx'` → exit 0 (PASS)
- [x] `sed -n 's/^description: *//p' .claude/skills/ctx/SKILL.md | grep -Eq 'with ctx|via ctx'` → exit 0 (PASS)
- [x] `sed -n 's/^description: *//p' .claude/skills/ctx/SKILL.md | grep -Eq 'understand the codebase|survey the repo'` → exit 0 (PASS)
- [x] `sed -n 's/^description: *//p' .claude/skills/ctx/SKILL.md | grep -qi 'not for content'` → exit 0 (negative scope retained) (PASS)
- [x] `diff <(sed -n 's/^description: *//p' .claude/skills/ctx/SKILL.md) <(sed -n 's/^description: *//p' antigravity/.agents/skills/ctx/SKILL.md)` → empty (mirror parity) (PASS, empty diff)
