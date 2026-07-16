Status: draft
Discovered-from: specs/trajectory-evals/tasks/04-closing-antigravity-and-version.md
Spec: ../SPEC.md
Blocking: no

# closing-task version-diff acceptance criteria should not anchor on a bare HEAD~1

A closing task's acceptance criterion checking a plugin.json version bump
via `git show HEAD~1:...` silently degrades to a false negative if any
commit lands after the version-bump commit. /breakdown's authoring
convention for closing tasks should anchor version-diff criteria to the
bump commit explicitly (or require the bump to be the branch's last
commit) instead of a bare `HEAD~1`.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
