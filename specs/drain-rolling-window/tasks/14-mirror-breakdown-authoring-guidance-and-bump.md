Status: draft
Discovered-from: specs/drain-rolling-window/tasks/10-version-bump-criteria-use-relative-check.md
Spec: ../SPEC.md
Blocking: no

# Breakdown skill edits from this batch (task 10, and eventual task 13) ship un-mirrored and without a plugin.json bump

Task 10 added version-bump acceptance-criteria authoring guidance to `.claude/skills/breakdown/SKILL.md`, and draft task 13 (once promoted) will reword that same file's Hand off section — but task 10's `Touch:` named only the `.claude/` file, with no mirror path (`antigravity/.agents/skills/breakdown/breakdown.md`, `antigravity/.agents/workflows/breakdown.md`) and no `.claude-plugin/plugin.json` version bump. Task 05, which owned the mirror+bump work for this spec, is already merged and can't carry this. Per CLAUDE.md's mirroring convention, this is exactly the "unlisted mirror silently ships un-mirrored" gap: a closing task should port both breakdown edits (task 10's guidance, and task 13's wording once promoted and landed) to the antigravity mirror and bump the plugin version.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
