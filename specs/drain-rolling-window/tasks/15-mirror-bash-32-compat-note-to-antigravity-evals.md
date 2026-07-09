# Task 15: Mirror the bash-3.2 compat note into the antigravity evals workflow

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: pending
Depends on: none
Priority: P3
Budget: 2 turns
Spec: ../SPEC.md
Discovered-from: 11-evals-runner-bash-32-compat-note.md
Touch: antigravity/.agents/workflows/evals.md

## Goal

`antigravity/.agents/workflows/evals.md` (which documents authoring
`setup.sh`/`assert.sh` scenario scripts) carries the same one-line
compat warning task 11 added to `.claude/skills/evals/reference.md` and
`evals/run.sh`: macOS system bash is 3.2 — no `declare -A`. No plugin
bump: antigravity-only change; the plugin manifest ships
`.claude/skills/`.

## Steps

1. Port the one-line note into the scenario-authoring passage of
   `antigravity/.agents/workflows/evals.md`.

## Acceptance

- [ ] `grep -q '3\.2' antigravity/.agents/workflows/evals.md` → match
- [ ] `grep -q 'declare -A' antigravity/.agents/workflows/evals.md` → match
- [ ] `grep -Eqi 'macos|system bash' antigravity/.agents/workflows/evals.md` → match
