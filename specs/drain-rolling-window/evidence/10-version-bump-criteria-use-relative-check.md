# Verification: 10-version-bump-criteria-use-relative-check

Verdict: FAIL (task file not updated — see "Process/contract" finding below;
content criteria themselves pass)

## Criterion 1: `grep -ci "base commit" .claude/skills/breakdown/SKILL.md` → ≥ 1, in vicinity of acceptance-criteria authoring guidance

Command: `grep -ci "base commit" .claude/skills/breakdown/SKILL.md`
Output: `1`

Location check: `grep -n -i "base commit" .claude/skills/breakdown/SKILL.md`
→ line 76, inside the new paragraph at SKILL.md:75-78, which sits directly
under Procedure step 3 ("Write specs/<slug>/tasks/NN-<slug>.md ..."),
immediately after the existing antigravity-mirror acceptance-check note and
immediately before step 4 ("Order tasks so each leaves the build green...").
This is squarely within the task-authoring / acceptance-criteria guidance
block, not an unrelated section.

Result: ✓ PASS

## Criterion 2: new guidance is additive-only, does not remove/contradict existing acceptance-authoring rules

Command: `git diff ef95a04d81bc912f9911d7f4347f0dd21188999b -- .claude/skills/breakdown/SKILL.md`

Output (full diff, all lines are additions):
```
+A version-bump acceptance criterion must check "changed from the value at
+the task's own base commit" (e.g. `git show <base-commit>:<path> | grep
+version` compared against the current value), never a hard-coded exact
+pre-task literal — a sibling task landing first can bump the same file, so
+a pinned literal false-fails once the on-disk value has already moved past it.
+
```
6 lines inserted, 0 removed. `grep -n -i "version" .claude/skills/breakdown/SKILL.md`
shows this is the *only* version-bump-related guidance in the file, so there
is no pre-existing rule it could contradict.

Result: ✓ PASS

## Gate: append-only task-file contract

Command: `git diff ef95a04d81bc912f9911d7f4347f0dd21188999b -- specs/drain-rolling-window/tasks/`
Output: (empty — 0 lines changed)

The task file `specs/drain-rolling-window/tasks/10-version-bump-criteria-use-relative-check.md`
is byte-identical to the base commit: `Status:` still reads `in-progress`,
both acceptance checkboxes are still unticked (`- [ ]`), and there is no
evidence-citation or plan-comment-block update recording that the work was
done. `git status` confirms the only modified file in the working tree is
`.claude/skills/breakdown/SKILL.md`; the task file has zero uncommitted
changes either.

Finding: the implementation (the SKILL.md edit) is present and correct, but
the task's own bookkeeping was never updated — Status was not flipped to
done/review, and neither acceptance checkbox was ticked. Per the task-file
contract (Status/checkbox/evidence updates are exactly the class of edit a
worker is expected and permitted to make), this task is incomplete as
submitted: the deliverable exists but the task record does not reflect it,
so there is nothing to distinguish "not started" from "done but
unrecorded" by inspecting the task file alone.

## Scope-creep check

Only file touched: `.claude/skills/breakdown/SKILL.md`, which matches the
task's `Touch:` header exactly. No other files modified. No version bump,
no antigravity mirror edit, no plugin.json bump — none of which this task's
`Touch:` list authorized anyway. No scope creep found.

## Overall

- Criterion 1: PASS
- Criterion 2: PASS
- Append-only task-file contract: the task file itself was left unmodified
  (Status still `in-progress`, checkboxes unticked) despite the guidance
  edit being present — this is a process gap, not a content gap.

Verdict: INCOMPLETE-as-submitted for the task record (content changes pass
both acceptance criteria, but the task file was never updated to reflect
completion, so per-task Status/checkbox state does not match the actual
state of the work).
