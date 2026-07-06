Status: in-progress
Depends on: none
Priority: P3
Budget: 6 turns
Discovered-from: specs/drain-rolling-window/tasks/05-ship-gates-and-mirrors.md
Spec: ../SPEC.md
Touch: .claude/skills/breakdown/SKILL.md
Blocking: no

# Version-bump acceptance criteria that pin an exact pre-task value can go stale

Task 05's own acceptance criterion hard-coded the pre-task `plugin.json` version as `0.8.14`, but by the time the task actually ran, a sibling task (03's own bump, or an earlier merge) had already advanced it to `0.8.15` — the criterion's own fallback wording ("or simply confirm the checked-in version string is not 0.8.14") absorbed the drift this time, but a future task authored the same way, without that fallback, would false-fail once a sibling task bumps the same file first. Worth a note in `/breakdown`'s authoring guidance: version-bump acceptance criteria should check "changed from the value at the task's own base commit" (or equivalent relative check) rather than hard-coding an exact pre-task literal.

## Steps

1. In `.claude/skills/breakdown/SKILL.md`'s task-authoring guidance (wherever it documents how to write acceptance criteria), add a note: version-bump acceptance criteria should check "changed from the value at the task's own base commit" (e.g. `git show <base-commit>:<path> | grep version` compared against the current value) rather than hard-coding an exact pre-task literal, since a sibling task landing first can bump the same file and cause a hard-coded literal to false-fail.

## Acceptance

- [ ] `grep -ci "base commit" .claude/skills/breakdown/SKILL.md` → ≥ 1, in the vicinity of acceptance-criteria authoring guidance
- [ ] The new guidance text does not remove or contradict any existing acceptance-authoring rule
