# Task 03: closing gate — plugin bump + validate, no antigravity drift

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: pending
Depends on: 01, 02
Priority: P2
Budget: 3 turns
Spec: ../SPEC.md (requirement R3)
Touch: .claude-plugin/plugin.json

## Goal

The plugin version is bumped (this task owns the bump — task 02's skill
edit is plugin-distributed; task 01's workflow edit is not),
`claude plugin validate .` passes, and the spec shipped ZERO
antigravity/ additions or changes (workflow-author is explicitly not
ported — antigravity/README.md:40 — and .claude/workflows/*.js has no
antigravity analog; creating ports would be a defect).

## Steps

1. Bump `.claude-plugin/plugin.json` version.
2. Run `claude plugin validate .`.
3. Verify no antigravity/ paths changed across this spec's commits.

## Acceptance

- [ ] `claude plugin validate .` → passes
- [ ] plugin.json version differs from the value at this task's base
  commit: `git show $(git merge-base HEAD origin/main 2>/dev/null || git rev-parse HEAD~3):.claude-plugin/plugin.json | grep '"version"'` vs current → changed
- [ ] `git log --oneline --name-only -20 | grep -c '^antigravity/'` over
  this spec's commits → 0 antigravity paths touched
