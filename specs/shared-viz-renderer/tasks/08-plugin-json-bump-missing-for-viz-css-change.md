Status: obsolete
Closed: 2026-07-09 — the bump landed with the viz-css resync (commit 2f15b0d, 0.8.23→0.8.24; now 0.8.25), satisfying CLAUDE.md's convention; nothing remains.
Discovered-from: specs/shared-viz-renderer/tasks/06-viz-axis-muted-tint.md
Spec: ../SPEC.md
Blocking: no

# plugin.json version was not bumped for the viz-axis-muted-tint skill-behavior change

`plugin.json` version was not bumped for task 06's change (emitted VIZ_CSS changed, a skill-behavior change per CLAUDE.md's bump convention). CLAUDE.md places the shared-viz spec's mirror + `plugin.json` bump in a task's `Touch:` (a closing task), but task 06 has no `Touch:` line and no closing task follows it in `specs/shared-viz-renderer/tasks/`, so the spec-wide bump may be missing.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
