Status: done
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

- [x] `grep -ci "base commit" .claude/skills/breakdown/SKILL.md` → ≥ 1, in the vicinity of acceptance-criteria authoring guidance — verifier PASS: count 1, match at SKILL.md:76 in the new paragraph under Procedure step 3, right after the antigravity-mirror acceptance-check note; evidence specs/drain-rolling-window/evidence/10-version-bump-criteria-use-relative-check.md
- [x] The new guidance text does not remove or contradict any existing acceptance-authoring rule — verifier PASS: `git diff` shows a purely additive 6-line hunk (0 deletions); it is the only version-bump guidance in the file, contradicting nothing existing; evidence specs/drain-rolling-window/evidence/10-version-bump-criteria-use-relative-check.md
