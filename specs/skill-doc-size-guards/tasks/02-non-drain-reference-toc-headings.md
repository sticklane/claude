# Task 02: Add TOC headings to the 7 non-drain over-100-line reference.md files

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
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

- [x] `for f in factcheck evals prose-review gate workflow-author fleet autopilot; do grep -qiE '^## (Table of [Cc]ontents|Contents)\b' <(head -20 .claude/skills/$f/reference.md) || echo "MISSING:$f"; done`
      → empty output. Evidence: re-run from the main checkout post-merge,
      empty output confirmed.
- [x] `for f in prose-review gate factcheck; do grep -qiE '^## (Table of [Cc]ontents|Contents)\b' <(head -20 antigravity/.agents/skills/$f/reference.md) || echo "MISSING-MIRROR:$f"; done`
      → empty output. Evidence: re-run from the main checkout post-merge,
      empty output confirmed.
- [x] `wc -l .claude/skills/factcheck/reference.md .claude/skills/evals/reference.md .claude/skills/prose-review/reference.md .claude/skills/gate/reference.md .claude/skills/workflow-author/reference.md .claude/skills/fleet/reference.md .claude/skills/autopilot/reference.md`
      → each file's content (minus the added TOC) is otherwise unchanged —
      spot-check with `git diff --stat` that only these 10 files (7
      source + 3 mirrors) changed. Evidence: `git diff --stat` against this
      task's pre-merge base shows exactly these 10 files, 31
      insertions(+)/9 deletions(-); `evals/lint-skill-size-gate.sh` (wired
      by task 04) now reports `OK`.

## Decisions

- [2026-07-14 /drain] The worker's DONE verdict was self-consistent
  (all 3 criteria verified with command+result evidence) but its
  branch never carried the Status:done / ticked-box bookkeeping this
  task file normally gets as part of the worker's own commit — only
  the 10 target reference.md files were committed. Rather than
  treating this as a failed DONE candidate (the content deliverable
  itself was independently re-verified from the main checkout
  post-merge, per the headless-fallback precedent in
  `.claude/skills/drain/reference.md`'s "Headless fallback"), drain
  re-ran all 3 acceptance commands itself post-merge, confirmed they
  pass, and wrote this bookkeeping directly. Reversible: revert this
  bookkeeping commit and re-flip to blocked/in-progress if a review
  disagrees with treating the omission as non-blocking.
- [2026-07-14 /drain] Worker-reported: the repo's PostToolUse
  `post-tool-format.sh` hook ran prettier on Edit-tool writes to these
  reference.md files and introduced out-of-scope reformatting (JS
  reflow, emphasis-marker swaps, table realignment, one markdown
  de-indent bug in workflow-author's code block). The worker reverted
  via `git checkout HEAD` and re-applied only the TOC heading via a
  raw `perl` edit through Bash (which does not retrigger the Edit
  hook), to keep the diff scoped to acceptance criterion 3's
  "content otherwise unchanged" requirement. Justified: no
  `scripts/check.sh`, no pre-commit hook, and no prettier config
  enforce formatting at commit/check time in this repo, and the
  files were already non-prettier-conformant before this task.
  Reversible: running prettier over the 10 touched files would
  reintroduce the reformatting.

## Discovered

- [2026-07-14 /drain] The repo's PostToolUse prettier-format hook
  reformats `.md` files on any Edit-tool write (embedded-JS reflow,
  `*x*`→`_x_` emphasis swaps, table realignment) and in this task's
  run introduced a real markdown-list de-indent bug inside
  workflow-author/reference.md's embedded code block before the
  worker reverted it. Latent churn/corruption risk for any future
  Edit-tool edit to these files unless the hook's scope is narrowed
  or its output is verified. Report only — no task file created (a
  human should assess whether to scope the hook away from
  `.claude/skills/**/reference.md`).
