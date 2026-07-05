# Task 04: concurrent-sessions rule + docs pointer + onboard bullet

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirement R8)
Touch: .claude/rules/concurrent-sessions.md, docs/memory/concurrent-session-collision.md, .claude/skills/onboard/SKILL.md

## Goal

`.claude/rules/concurrent-sessions.md` exists (≤40 lines): the always-on
pre-flight promoted from docs/memory/concurrent-session-collision.md —
before multi-file edits in a shared checkout, check for other live
sessions (`claude agents --json` / recent foreign mtimes /
`git worktree list`); on detected collision STOP and surface to the
user, never revert the other session's work. The docs/memory file keeps
its incident narrative but replaces its procedure section with a pointer
to the rule (no duplication). /onboard's CLAUDE.md template gains ONE
optional bullet pointing installing repos at the same pre-flight pattern.

## Touch

Only the three listed files. Do NOT touch drain/build/autopilot files
(tasks 02–03), antigravity, or plugin.json (task 05 mirrors onboard's
edit and bumps). Rules are always-loaded context: stay terse (≤40 lines,
imperative), consistent with the sibling rules' style
(token-discipline.md, untrusted-data.md).

## Steps

1. Write the rule file (distill the docs/memory procedure; keep the
   STOP-don't-revert clause verbatim in spirit).
2. Replace the docs/memory procedure section with a pointer line to the
   rule; keep the incident record.
3. Add the single optional bullet to onboard's template section.
4. Acceptance checks; full test sweep; commit.

## Acceptance

- [ ] `test -f .claude/rules/concurrent-sessions.md && [ $(wc -l < .claude/rules/concurrent-sessions.md) -le 40 ]` → exit 0
- [ ] `grep -c "concurrent-sessions" docs/memory/concurrent-session-collision.md` → ≥ 1 (pointer present)
- [ ] `grep -ci "never revert" .claude/rules/concurrent-sessions.md` → ≥ 1
- [ ] `grep -c "concurrent-sessions" .claude/skills/onboard/SKILL.md` → ≥ 1 (one optional template bullet)
- [ ] `for t in tests/test_*.sh; do bash "$t" || exit 1; done && claude plugin validate .` → exit 0
