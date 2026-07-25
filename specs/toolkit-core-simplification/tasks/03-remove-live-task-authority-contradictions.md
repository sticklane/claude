# Task 03: remove live task-authority contradictions

<!-- Task state is canonical in bd. The Status line is frozen display and is not edited by workers. -->

Status: pending
Depends on: 02
Priority: P0
Budget: 36 turns
Spec: ../SPEC.md (requirement R3)
Touch: AGENTS.md, CLAUDE.md, .claude/rules/quality-discipline.md, .claude/skills/_shared/headers.py, .claude/skills/build/SKILL.md, .claude/skills/drain/SKILL.md, .claude/skills/example-corpus/SKILL.md, .claude/skills/handoff/SKILL.md, .claude/skills/onboard/SKILL.md, .claude/skills/workboard/SKILL.md, .claude/skills/workboard/reference.md, .claude/skills/workboard/workboard.py, .claude/skills/workboard/test_workboard.py, .claude/skills/workflow-author/SKILL.md, .claude/skills/workflow-author/reference.md, tests/test_bd_authority_contract.sh, tests/inventory/03-bd-authority.json, specs/toolkit-core-simplification/surface-inventory/03-bd-authority.json

## Goal

Every live procedure must read and write task status, dependencies, claims,
handoffs, and closure through bd. Markdown task headers remain readable
historical/display data but no worker, dashboard, build, drain, or authoring
procedure advances them.

## Touch

Preserve task-file goals, acceptance criteria, evidence, and prose as durable
data. Do not touch dead workflows or runtime-profile currency; Task 04 owns
those.

## Steps

1. Add a behavioral authority test that exercises build/drain/workboard
   fixtures with bd state disagreeing with frozen markdown.
2. Remove header-writing and header-authority paths from the listed live
   skills, dashboard code, rules, and orientation files; route state changes
   to bd.
3. Keep task-file content updates only where they are evidence or authored
   task definitions, never status transitions.

## Acceptance

- [ ] `bash tests/test_bd_authority_contract.sh` → bd wins every disagreement fixture and no live procedure writes a task Status header (L3).
- [ ] `python3 -m pytest .claude/skills/workboard/test_workboard.py -q` → workboard status/dependency rendering is derived from bd fixtures (L2).
- [ ] `bash scripts/check.sh` → the authority sweep preserves all inventoried behavior (L3).
