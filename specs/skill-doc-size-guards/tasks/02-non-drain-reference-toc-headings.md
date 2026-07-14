# Task 02: Add TOC headings to the 7 non-drain over-100-line reference.md files

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: none
Priority: P2
Budget: 35 turns
Spec: ../SPEC.md (requirement R5, non-drain portion)
Touch: .claude/skills/factcheck/reference.md, .claude/skills/evals/reference.md, .claude/skills/prose-review/reference.md, .claude/skills/gate/reference.md, .claude/skills/workflow-author/reference.md, .claude/skills/fleet/reference.md, .claude/skills/autopilot/reference.md, antigravity/.agents/skills/prose-review/reference.md, antigravity/.agents/skills/gate/reference.md, antigravity/.agents/skills/factcheck/reference.md

## Goal

Each of these 7 reference.md files (all currently over 100 lines with no
qualifying heading) gains a `## Table of contents` heading within its
first 20 lines, listing its `## `-level sections: `factcheck`, `evals`,
`prose-review`, `gate`, `workflow-author`, `fleet`, `autopilot`. For the 3
of these that have an existing antigravity mirror
(`prose-review`, `gate`, `factcheck` — verified: `evals`, `workflow-author`,
`fleet`, and `autopilot` have none), the matching TOC heading is added to
the antigravity mirror too, per CLAUDE.md's standing "mirror the change
into antigravity/ in the same commit" convention. Do not touch drain's
files — that remediation is a separate, coupled task elsewhere in this
spec.

## Touch

Do not edit `.claude/skills/drain/reference.md`,
`.claude/skills/drain/SKILL.md`, `codex/.agents/skills/drain/SKILL.md`,
`antigravity/.agents/workflows/drain.md`, or `.claude-plugin/plugin.json`
— those belong to the drain-remediation task.

## Steps

1. For each of the 7 `.claude/skills/<name>/reference.md` files, find each
   `## `-level heading in the file (in order) and add a
   `## Table of contents` heading near the top (within the first 20 lines
   — right after the title and any existing "Contents:" prose line is
   fine) listing those headings, e.g. as a bullet list or
   middle-dot-separated line. Where a prose "Contents:" line already
   exists (some files may not have one), you may supplement it with the
   heading rather than delete useful prose, but the `## Table of contents`
   (or `## Contents`) heading itself must be present and matched by
   requirement 3's regex within the first 20 lines.
2. For `prose-review`, `gate`, and `factcheck` specifically, repeat the
   same TOC-heading addition in the antigravity mirror
   (`antigravity/.agents/skills/<name>/reference.md`), matching that
   mirror's own section list (it may differ slightly in wording from the
   `.claude/` source — list the mirror's own `## ` headings, not the
   source's).
3. Run `evals/lint-skill-size-gate.sh` if task 01 has already landed
   (informational only — this task's acceptance below does not depend on
   task 01's script existing).

## Acceptance

- [ ] `for f in factcheck evals prose-review gate workflow-author fleet autopilot; do grep -qiE '^## (Table of [Cc]ontents|Contents)\b' <(head -20 .claude/skills/$f/reference.md) || echo "MISSING:$f"; done`
      → empty output.
- [ ] `for f in prose-review gate factcheck; do grep -qiE '^## (Table of [Cc]ontents|Contents)\b' <(head -20 antigravity/.agents/skills/$f/reference.md) || echo "MISSING-MIRROR:$f"; done`
      → empty output.
- [ ] `wc -l .claude/skills/factcheck/reference.md .claude/skills/evals/reference.md .claude/skills/prose-review/reference.md .claude/skills/gate/reference.md .claude/skills/workflow-author/reference.md .claude/skills/fleet/reference.md .claude/skills/autopilot/reference.md`
      → each file's content (minus the added TOC) is otherwise unchanged —
      spot-check with `git diff --stat` that only these 10 files (7
      source + 3 mirrors) changed.
