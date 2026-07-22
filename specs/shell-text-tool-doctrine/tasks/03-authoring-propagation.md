# Task 03: Point authoring skills at the shell-text-tools rule

Status: pending
Depends on: 01, 02
Priority: P2
Budget: 6 turns
Spec: ../SPEC.md (requirement R3)
Touch: .claude/skills/idea/SKILL.md, .claude/skills/breakdown/SKILL.md, .claude/skills/critique/SKILL.md

## Touch

Adds one pointer line to each authoring skill's acceptance-criteria guidance
section referencing `.claude/rules/shell-text-tools.md`. Depends on Task 02
because that task may edit embedded examples in idea/SKILL.md and
breakdown/SKILL.md — serialize to avoid a same-file collision.

## Steps

1. In idea/SKILL.md, breakdown/SKILL.md, and critique/SKILL.md — wherever
   acceptance-criteria authoring guidance lives (idea ~L118 anchored-criteria
   block; breakdown's anchored-acceptance guidance; critique's under-scoped
   acceptance-command finding) — add one line pointing at
   `.claude/rules/shell-text-tools.md` so newly authored specs inherit the
   anchored-and-bounded acceptance style (cite it, don't restate it).
2. If a mirrored antigravity counterpart of any edited skill embeds the same
   guidance, mirror the pointer per mirror-procedure-discipline.md in the same
   commit.

## Acceptance

- [ ] `grep -l 'shell-text-tools' .claude/skills/idea/SKILL.md .claude/skills/breakdown/SKILL.md` → matches both files
- [ ] `grep -c 'shell-text-tools' .claude/skills/critique/SKILL.md` → ≥1
