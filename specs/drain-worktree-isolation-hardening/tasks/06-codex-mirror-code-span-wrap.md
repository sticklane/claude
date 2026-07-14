Status: draft
Intake-refused: gate — assessor-authored ACs are unsatisfiable/backwards (criterion 1 can never reach 0 since the fix keeps "worktree remove" in the file; criterion 2 passes today unfixed and breaks after the correct fix) and miss a second genuinely-wrapped span (`git branch -D <branch>`, lines 251-252) the Goal/Touch don't cover (2026-07-14)
Discovered-from: 05-mirrors-plugin-bump-trim.md
Spec: ../SPEC.md
Blocking: no

# Cosmetic inline code span wraps mid-span in codex drain mirror

`codex/.agents/skills/drain/SKILL.md` has an inline code span that wraps
mid-span (e.g. a `git worktree remove` command split across a line break)
in the R1-R4 mirror content task 05 added — renders awkwardly but doesn't
affect the machine-parsed procedure.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
