Status: obsolete
Closed: 2026-07-09 — `ruff format --check .claude/skills/_shared/viz.py antigravity/.agents/skills/_shared/viz.py` reports "2 files already formatted"; the drift no longer exists at HEAD.
Discovered-from: specs/shared-viz-renderer/tasks/06-viz-axis-muted-tint.md
Spec: ../SPEC.md
Blocking: no

# .claude/skills/\_shared/viz.py (and its antigravity mirror) are not ruff-format-clean

HEAD's `.claude/skills/_shared/viz.py` and its antigravity mirror are not `ruff format`-clean, the repo's own declared canonical Python formatter (`.claude/hooks/post-tool-format.sh`, SPEC R11) would reflow them. Pre-existing drift, not introduced by task 06 — its worker discarded the hook's spurious whole-file reflow to keep task 06's commit minimal, but the underlying drift remains unfixed.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
