# Task 04: closing — antigravity mirror, plugin bump, zero-target entries

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: 01, 03
Priority: P2
Budget: 4 turns
Spec: ../SPEC.md (requirements R10 + R9 zero-target repos)
Touch: antigravity/.agents/skills/prose-review/, .claude-plugin/plugin.json, specs/prose-review/evidence/zero-target.md

## Goal

`antigravity/.agents/skills/prose-review/` created with content-equivalent
doctrine (plain review/authoring skill; content-coverage check, not
byte-diff). Plugin version bumped RELATIVE to this task's base in THIS
task's own commit; `claude plugin validate .` passes. R9 zero-target
evidence: one entry each for ~/automation and ~/dev-agents (std repos
with no README/AGENTS/docs targets — skipped, no docs authored). No codex
wrapper (not one of the four explicit-invocation stages — reaches Codex
via the antigravity symlink overlay).

## Acceptance

- [ ] `grep -qi 'Diátaxis' antigravity/.agents/skills/prose-review/reference.md` (or SKILL.md) → hit
- [ ] `claude plugin validate .` → passes
- [ ] `git show HEAD -- .claude-plugin/plugin.json | grep -q '^+.*"version"'` run right after this task's commit → hit
- [ ] `grep -c 'automation\|dev-agents' specs/prose-review/evidence/zero-target.md` ≥ 2
