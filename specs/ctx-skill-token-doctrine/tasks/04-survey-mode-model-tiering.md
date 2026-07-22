# Task 04: Codebase survey section + model tiering (R4)

Status: pending
Depends on: 03, 02
Priority: P3
Budget: 10 turns
Spec: ../SPEC.md (requirement R4)
Touch: .claude/skills/ctx/SKILL.md, antigravity/.agents/skills/ctx/SKILL.md

## Goal

The ctx skill body has a "Codebase survey" section with the survey recipe and
a model-tiering rule. Recipe for whole-repo understanding requests:
`map --limit N` + `tree` per top-level module + `deps` on entry points.
Tiering rule: up to ~4 targeted queries run inline; a batched survey or
open-ended multi-question exploration is delegated to a cheap-tier scout whose
prompt embeds the ctx command table and returns a distilled structure report
— the main model never reads raw query dumps for surveys. The section
includes an explicit dispatch-prompt template for the scout containing the ctx
command table. Mirror the section into the antigravity ctx SKILL.md.

## Touch

Body of `.claude/skills/ctx/SKILL.md` and its antigravity mirror. Serializes
after task 03 (same file). Also depends on task 02 (R5): R4's delegation is
only functional once scout has the `Bash(ctx *)` grant, so this task's text
must not ship ahead of R5 — hence the acceptance re-runs R5's grant check.

## Steps

1. Read the current ctx SKILL.md body (with tasks 01/03 already landed).
2. Write the "Codebase survey" section: the `map --limit N` + per-module
   `tree` + entry-point `deps` recipe, and the ~4-query inline vs.
   delegate-to-cheap-scout tiering rule (deterministic CLI calls; tier only
   governs whose context absorbs output).
3. Include an explicit scout dispatch-prompt template that embeds the ctx
   command table and asks for a distilled structure report.
4. Port the section into `antigravity/.agents/skills/ctx/SKILL.md`.
5. Run the acceptance commands (including the R5 grant re-check).

## Acceptance

- [ ] `grep -qi 'Codebase survey' .claude/skills/ctx/SKILL.md` → exit 0
- [ ] `grep -q 'map --limit' .claude/skills/ctx/SKILL.md && grep -qi 'deps' .claude/skills/ctx/SKILL.md` → exit 0 (recipe present)
- [ ] `grep -qi 'scout' .claude/skills/ctx/SKILL.md && grep -qi 'inline' .claude/skills/ctx/SKILL.md` → exit 0 (tiering rule + dispatch template)
- [ ] `grep -q 'Bash(ctx' .claude/agents/scout.md` → exit 0 (R5 grant landed — R4 text must not ship ahead of it)
- [ ] `grep -qi 'survey' antigravity/.agents/skills/ctx/SKILL.md` → exit 0 (mirror coverage)
