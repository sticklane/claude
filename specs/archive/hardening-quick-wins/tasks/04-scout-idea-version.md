# Task 04: Scout early-stop, /idea deterministic gate, version bump

Status: done
Depends on: none
Budget: 30 turns
Spec: ../SPEC.md (requirements R5, R6, R9, R8 scout + idea parts)

## Goal

The scout agent stops as soon as findings converge (with a ~15 tool-call
ceiling and best-so-far reporting), /idea's right-size paragraph sends
mechanical transforms to "a script, not a spec", both antigravity skill
mirrors carry the same phrases, and the plugin version is bumped to
0.3.0 (this task owns the bump for the whole four-spec batch).

## Touch

- `.claude/agents/scout.md`
- `.claude/skills/idea/SKILL.md` (right-size paragraph only)
- `antigravity/.agents/skills/scout/SKILL.md`
- `antigravity/.agents/skills/idea/SKILL.md` (the skill, not the
  workflow stub)
- `.claude-plugin/plugin.json` (version only)

## Steps

1. Add the early-stop rule to `.claude/agents/scout.md` containing the
   phrase "stop as soon as findings converge", the ~15 tool-call
   ceiling, and best-so-far + unresolved reporting.
2. Extend /idea's right-size paragraph with the deterministic-first gate
   containing the phrase "a script, not a spec".
3. Mirror both into the antigravity scout and idea skills.
4. Set `"version": "0.3.0"` in `.claude-plugin/plugin.json`.

## Acceptance

- [x] `grep -q "stop as soon as findings converge" .claude/agents/scout.md` → pass
      (verifier: exit 0; rule includes the ~15 tool-call ceiling and
      best-so-far plus unresolved reporting)
- [x] `grep -q "a script, not a spec" .claude/skills/idea/SKILL.md` → pass
      (verifier: exit 0; gate added inside the "Right-size first."
      paragraph, not elsewhere)
- [x] `grep -q "stop as soon as findings converge" antigravity/.agents/skills/scout/SKILL.md && grep -q "a script, not a spec" antigravity/.agents/skills/idea/SKILL.md` → pass
      (verifier: exit 0; both mirrors carry the same wording; idea change
      is in the skill file, not the workflow stub)
- [x] `python3 -c "import json; assert json.load(open('.claude-plugin/plugin.json'))['version']=='0.3.0'"` → pass
      (verifier: exit 0; single-line version change, valid JSON, no other
      fields touched)
      Note: pin superseded by the review-fixes batch bump (task
      review-fixes/99; current version 0.7.0). Passed as written when this
      task landed; do not count as a regression in later sweeps.
