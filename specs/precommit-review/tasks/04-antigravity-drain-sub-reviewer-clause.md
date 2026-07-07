Status: in-progress
Priority: P1
Discovered-from: specs/precommit-review/tasks/03-workflow-mirror-and-bump.md
Spec: ../SPEC.md
Blocking: no

# antigravity drain.md missing sub-reviewer clause cited by build.md mirror

`antigravity/.agents/workflows/drain.md` has no "sub-reviewer" clause that build.md's mirrored review step cites ("the drain workflow's sub-reviewer clause") — the citation points at prose that doesn't exist in the antigravity drain mirror yet (only in `.claude/skills/drain/reference.md`); worth a follow-up task if drain.md is ever mirrored with that section.

Decision (2026-07-06): confirmed gap — `antigravity/.agents/workflows/drain.md` has zero "sub-reviewer" mentions while `antigravity/.agents/workflows/build.md` (line ~78) cites "the drain workflow's sub-reviewer clause". Mirror the sub-reviewer clause from `.claude/skills/drain/reference.md` into the antigravity drain.md so the citation resolves. (Task has no Touch list; the file to edit is `antigravity/.agents/workflows/drain.md`.)

## Acceptance

- [ ] `grep -q 'sub-reviewer' antigravity/.agents/workflows/drain.md` → exits 0 (clause mirrored; currently 0 mentions)
