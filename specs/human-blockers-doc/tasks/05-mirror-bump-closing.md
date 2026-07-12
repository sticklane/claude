# Task 05: closing — drain/build port lines + plugin bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: 02, 03
Priority: P2
Budget: 3 turns
Spec: ../SPEC.md (requirement R6)
Touch: antigravity/.agents/workflows/drain.md, antigravity/.agents/workflows/build.md, codex/.agents/skills/drain/SKILL.md, codex/.agents/skills/build/SKILL.md, .claude-plugin/plugin.json

## Goal

Content-equivalent Agent-filed-blockers lines land in the antigravity
drain/build ports (paraphrased; anchor literal) and the codex
drain/build wrappers where their text embeds the affected steps (else
note in commit message). Plugin version bumped RELATIVE to this task's
base in THIS task's own commit, covering tasks 02 and 03's skill
changes; validate + ultra-gate green.

## Acceptance

- [ ] `grep -qi 'Agent-filed blockers' antigravity/.agents/workflows/drain.md` → hit (0 today, verified)
- [ ] `claude plugin validate .` → passes AND `bash evals/lint-ultra-gate.sh` → OK
- [ ] `git show HEAD -- .claude-plugin/plugin.json | grep -q '^+.*"version"'` right after this task's commit → hit
