Status: draft
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
