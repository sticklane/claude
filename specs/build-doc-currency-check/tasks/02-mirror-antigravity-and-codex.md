# Task 02: Mirror the doc-currency close-out edits into antigravity and codex

Status: done
Depends on: 01
Priority: P1
Budget: 6 turns
Spec: ../SPEC.md (requirement R6)
Touch: antigravity/.agents/workflows/build.md, antigravity/AGENTS.md, codex/.agents/skills/build/SKILL.md

## Goal

Per CLAUDE.md's mirroring convention, both of Task 01's edits land in
their antigravity and codex mirrors too, adapted to each runtime's own
conventions (antigravity has no `quality-discipline.md` file; codex has
neither that file nor a slash-command citation convention).

## Touch

Exactly the three files listed above. Do not touch `.claude/` (Task 01
owns it).

**BLOCKING PRECONDITION — cleared by human judgment call, 2026-07-15.**
`specs/narrow-autopilot` also edited `antigravity/.agents/workflows/build.md`
(folding in the classification gate and escalation triggers, Task 04) and
`codex/.agents/skills/build/SKILL.md` (folding in autopilot's content,
Task 05) — the same cross-spec collision this spec's Sequencing note
flagged for the `.claude` leg extended to both mirrors. All 6 of
narrow-autopilot's real tasks (01-06) are `Status: done` and merged, so
both fold-ins are fully landed. One unrelated stub,
`specs/narrow-autopilot/tasks/07-antigravity-build-md-char-cap.md`
(`Status: draft`), does concern `antigravity/.agents/workflows/build.md`,
but a `draft` task is never dispatchable — no active or queued edit
against that file exists, so there is no live collision risk. Once this
task starts, find each edit point by section content, not by line
number.

## Steps

1. The blocking precondition above is already confirmed cleared (human
   judgment call, 2026-07-15) — no re-check needed. Confirm Task 01 has
   landed (its citation wording is what this task's antigravity/codex
   edits parallel).
2. `antigravity/.agents/workflows/build.md` (mirrors `build/SKILL.md`,
   including its close-out review logic): add a citation reading "see
   AGENTS.md's Quality discipline section" (antigravity has no
   `quality-discipline.md` file to name) at the equivalent close-out
   bullet. Separately, since this mirror has no `/code-review` call (its
   close-out step falls back to a subagent reviewer instead), add a note
   at that sub-reviewer fallback bullet using the exact phrase "not by the
   sub-reviewer fallback".
3. `antigravity/AGENTS.md`'s "## Quality discipline" section (mirrors
   `quality-discipline.md`): add the same new "Documentation currency"
   content Task 01 added to the `.claude` leg.
4. `codex/.agents/skills/build/SKILL.md` (real content, not a symlink):
   inline the reminder directly at the close-out pre-commit-review bullet
   (codex has no `quality-discipline.md` to cite) — e.g. "before
   committing, check whether the diff invalidates AGENTS.md's
   Map/Commands/State or anything README.md documents for end users —
   update it in the same commit." Separately, at the `$code-review`
   invocation (codex's close-out step does invoke it), add a note using
   the exact phrase "not by $code-review itself" (codex's own invocation
   syntax) — distinct anchor from the inlined reminder above.

## Acceptance

- [x] `grep -c "Documentation currency" antigravity/AGENTS.md` → 1 or more.
      Verified → 1 (evidence/02-mirror-antigravity-and-codex.md).
- [x] `grep -c "Quality discipline section" antigravity/.agents/workflows/build.md`
      → 1 or more. Verified → 1 (evidence file).
- [x] `grep -c "not by the sub-reviewer fallback" antigravity/.agents/workflows/build.md`
      → 1 or more. Verified → 1 (evidence file).
- [x] `grep -cE "Documentation currency|AGENTS.md's Map" codex/.agents/skills/build/SKILL.md`
      → 1 or more (`-E`, not a `\|` BRE-alternation escape — not portable
      to a plain BSD `grep`). Verified → 1 (evidence file).
- [x] `grep -cF 'not by $code-review itself' codex/.agents/skills/build/SKILL.md`
      → 1 or more. Use `-F` (fixed-string), not a bare double-quoted
      pattern: `\$` collapses to a literal `$` before grep sees it, and a
      mid-pattern `$` in BRE mode is not guaranteed to match a literal
      dollar sign on every platform — the unescaped form false-reports 0
      even when the phrase is present. Verified → 1 (evidence file).
