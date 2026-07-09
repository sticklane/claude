# Task 14: Mirror breakdown's version-bump authoring guidance to antigravity + bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Depends on: none
Priority: P3
Budget: 4 turns
Spec: ../SPEC.md
Discovered-from: specs/drain-rolling-window/tasks/10-version-bump-criteria-use-relative-check.md
Touch: antigravity/.agents/skills/breakdown/SKILL.md, .claude-plugin/plugin.json

## Goal

Task 10's version-bump acceptance-criteria authoring guidance (bump
checks compare against the task's own base commit, never a hard-coded
pre-task literal) is ported into `antigravity/.agents/skills/breakdown/
SKILL.md` — a paraphrased content port, not a byte mirror
(docs/memory/workboard-mirror-verbatim.md) — and plugin.json is bumped.
Scope note (narrowed at promotion, 2026-07-09): task 13's Hand-off
rewording is ALREADY mirrored (task 09 landed it), and
`antigravity/.agents/workflows/breakdown.md` is a 5-line launcher with
nothing to port — only task 10's guidance remains. The original stub
named a nonexistent path (`.agents/skills/breakdown/breakdown.md`); the
real mirror is the SKILL.md above.

## Steps

1. Read `.claude/skills/breakdown/SKILL.md`'s version-bump guidance
   paragraph (near "A version-bump acceptance criterion").
2. Port the concept into the antigravity breakdown SKILL.md's matching
   section.
3. Bump plugin.json one patch level from the value at this task's own
   base commit.

## Acceptance

- [x] `grep -qi 'base commit' antigravity/.agents/skills/breakdown/SKILL.md && grep -qi 'version' antigravity/.agents/skills/breakdown/SKILL.md` → both match (verifier PASS; evidence/14-\*.md)
- [x] `grep -Eqi 'never a hard-coded|pinned literal' antigravity/.agents/skills/breakdown/SKILL.md` → match (the false-fail rationale landed; verifier PASS)
- [x] plugin.json version differs from `git show <this task's base commit>:.claude-plugin/plugin.json` (base f5648489 = 0.8.26 → worktree 0.8.27; verifier PASS)
