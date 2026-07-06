Status: draft
Discovered-from: specs/absorb-agent-tools/tasks/08-mirror-priority-re-to-antigravity.md
Spec: ../SPEC.md
Blocking: no

# Global auto-format-on-edit hook silently rewrites entire non-black-conformant Python files, not just the two files task 07 covers

A global (user-level, not repo) auto-format-on-edit hook runs a black-style formatter on Python edits in this repo. On any Python file that isn't already black-conformant — task 07 names two (`agent-console/agent-console.py`, `.claude/skills/workboard/workboard.py`), but the task 08 worker hit the same behavior on `antigravity/.agents/skills/workboard/workboard.py`, a third file outside task 07's Touch — a single-line Edit triggers a full-file reformat (500+ lines), ballooning a scoped change into a diff dominated by cosmetic noise. The worker had to detect this and re-apply via a non-Edit path to avoid shipping the wholesale reformat. Since the antigravity mirror tree carries multiple such files, task 07's one-shot fix for its two named files won't prevent recurrence elsewhere. Worth either black-conforming the repo's Python files intentionally (broader than task 07's scope) or scoping the format hook to touched hunks rather than whole files.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
