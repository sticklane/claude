Status: draft
Discovered-from: specs/absorb-agent-tools/tasks/08-mirror-priority-re-to-antigravity.md
Spec: ../SPEC.md
Blocking: no

# Global auto-format-on-edit hook silently rewrites entire non-ruff-conformant Python files, not just the two files task 07 covers

A global (user-level, not repo) auto-format-on-edit hook runs `ruff format` on Python edits in this repo (task 07's worker confirmed the active hook is ruff, not black — `.claude/hooks/post-tool-format.sh`; a prior report calling it "black-style" was a misidentification, and `agent-console/agent-console.py` itself turned out already ruff-conformant, needing no flush). On any Python file that isn't already ruff-conformant — task 07 flushed the drift on `.claude/skills/workboard/workboard.py`, but the task 08 worker hit the same behavior on `antigravity/.agents/skills/workboard/workboard.py`, a third file outside task 07's Touch — a single-line Edit triggers a full-file reformat (500+ lines), ballooning a scoped change into a diff dominated by cosmetic noise. The worker had to detect this and re-apply via a non-Edit path to avoid shipping the wholesale reformat. Since the antigravity mirror tree carries multiple such files, task 07's one-shot fix won't prevent recurrence elsewhere. Worth either ruff-conforming the repo's Python files intentionally (broader than task 07's scope) or scoping the format hook to touched hunks rather than whole files.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
