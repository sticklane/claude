# Task 02: closing — antigravity drain workflow + codex check + plugin bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Depends on: 01
Priority: P2
Budget: 3 turns
Spec: ../SPEC.md (requirement R4)
Touch: antigravity/.agents/workflows/drain.md, codex/.agents/skills/drain/SKILL.md, .claude-plugin/plugin.json

## Goal

Content-equivalent terminal-distill lines in the antigravity drain
workflow's step-4/terminal area; codex drain wrapper updated only where
its summary covers the terminal sequence (else note in commit message).
The antigravity DISTILL port is task 01's — do not touch it here. Plugin
version bumped RELATIVE to this task's base in THIS task's own commit;
validate + ultra-gate green.

## Acceptance

- [x] `grep -qi 'terminal distill' antigravity/.agents/workflows/drain.md` → hit (Terminal distill paragraph added at the step-5 exit/terminal area; grep → HIT)
- [x] `claude plugin validate .` → passes AND `bash evals/lint-ultra-gate.sh` → OK (validate: "Validation passed"; lint-ultra-gate: "OK — all ultra mentions gated in 4 files")
- [x] `git show HEAD -- .claude-plugin/plugin.json | grep -q '^+.*"version"'` right after this task's commit → hit (0.8.52 → 0.8.53 bumped in this commit; verified post-commit)
