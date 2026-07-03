# Task 03: Budget line in task template, over-budget stop in /drain

Status: in-progress
Depends on: 01
Budget: 30 turns
Spec: ../SPEC.md (requirements R4, R8 breakdown + drain budget parts)

## Goal

/breakdown's task template includes a `Budget:` line with one sentence
of sizing guidance; both /drain worker prompts tell workers to stop with
verdict BLOCKED "over budget" when remaining work clearly exceeds the
budget; the headless fallback maps the budget to `--max-turns`. Mirrors:
antigravity breakdown template and drain workflow prompt. (Depends on
task 01 because both edit the same drain prompts and antigravity drain
workflow — apply on top of its wording.)

## Touch

- `.claude/skills/breakdown/SKILL.md` (template block + one sentence)
- `.claude/skills/drain/reference.md` (both worker prompts, headless
  `--max-turns` line)
- `antigravity/.agents/skills/breakdown/SKILL.md` (template block)
- `antigravity/.agents/workflows/drain.md` (worker prompt)

## Steps

1. Add `Budget: <rough ceiling, e.g. "40 turns">` to the task template
   in `.claude/skills/breakdown/SKILL.md`, plus one sizing sentence
   (2× the honest estimate; workers stop rather than grind).
2. Add the "over budget" stop instruction to both worker prompts in
   `.claude/skills/drain/reference.md`; in the headless fallback, derive
   `--max-turns` from the task's Budget when present.
3. Mirror: template line into `antigravity/.agents/skills/breakdown/SKILL.md`,
   the "over budget" stop into `antigravity/.agents/workflows/drain.md`.

## Acceptance

- [ ] `grep -q "^Budget:" .claude/skills/breakdown/SKILL.md` → pass
- [ ] `test "$(grep -c 'over budget' .claude/skills/drain/reference.md)" -ge 2` → pass
- [ ] `grep -q "^Budget:" antigravity/.agents/skills/breakdown/SKILL.md && grep -q "over budget" antigravity/.agents/workflows/drain.md` → pass
