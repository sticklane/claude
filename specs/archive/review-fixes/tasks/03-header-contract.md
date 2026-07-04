# Task 03: Task-file header contract — Touch header line, drain inventory, plan-block placement

Status: done
Depends on: 02
Budget: 30 turns
Spec: ../SPEC.md (cluster 03)

## Goal

Drain's inventory reads "only the header fields" but `Touch` currently
lives in a `## Touch` body section, and `Budget` isn't in the inventory
list at all. Fix the contract end to end: breakdown's template moves Touch
to a `Touch:` single-line header (comma-separated paths) above the first
`##`, keeping an optional `## Touch` body section for prose boundaries;
drain's inventory reads all five headers (`Status`, `Depends on`,
`Priority`, `Budget`, `Touch`); build's plan-comment blocks are pinned below the
header lines so header parsing survives them. (Depends on task 02: both
edit the drain files — apply on top of its wording.)

## Touch

- `.claude/skills/breakdown/SKILL.md` (task template + one sentence)
- `.claude/skills/drain/SKILL.md` (inventory paragraph, ~lines 26-28)
- `.claude/skills/build/SKILL.md` (step 1 plan instruction, close-out)
- `antigravity/.agents/skills/breakdown/SKILL.md`,
  `antigravity/.agents/workflows/drain.md`,
  `antigravity/.agents/workflows/build.md` (mirrors)

## Steps

1. In breakdown's task template, add a `Touch: <comma-separated paths>`
   header line in the header block (above the first `##`); keep
   `## Touch` as an optional body section for prose boundary notes, and
   say the header line is what dispatchers parse.
2. In drain's inventory paragraph, change the header list to
   (`Status`, `Depends on`, `Priority`, `Budget`, `Touch`) — Budget is
   currently unlisted even though the over-budget stop and headless
   `--max-turns` consume it, and `Priority` is consumed by the
   tie-break the task-priority spec adds (listing it here keeps the
   inventory contract stable whichever lands first; it is optional in
   task files, absent = P2).
3. In build step 1, amend the plan-as-comment-block instruction: the plan
   block must sit BELOW the header lines (never between them); in build's
   close-out, add that the plan block is deleted.
4. Mirror 1-3 into the antigravity breakdown skill and drain/build
   workflows.

## Acceptance

- [x] `grep -q "^Touch:" .claude/skills/breakdown/SKILL.md` → exit 0 (template header line) — verified, see ../evidence/03-header-contract.md
- [x] `grep -q "## Touch" .claude/skills/breakdown/SKILL.md` → exit 0 (optional body section retained) — verified, see ../evidence/03-header-contract.md
- [x] `grep -q "Budget" .claude/skills/drain/SKILL.md && grep -qE '\(.?Status.?, .?Depends on.?, .?Priority.?, .?Budget.?, .?Touch.?\)' .claude/skills/drain/SKILL.md` → exit 0 (inventory lists all five headers) — verified, see ../evidence/03-header-contract.md
- [x] `grep -qi "below the header lines" .claude/skills/build/SKILL.md` → exit 0 (plan-block placement pinned) — verified, see ../evidence/03-header-contract.md
- [x] `grep -qi "delete" .claude/skills/build/SKILL.md` → exit 0 (close-out deletes the plan block; confirm the sentence is in close-out, not elsewhere) — verified in ## 4. Close out only, see ../evidence/03-header-contract.md
- [x] `grep -q "^Touch:" antigravity/.agents/skills/breakdown/SKILL.md && grep -q "Budget" antigravity/.agents/workflows/drain.md && grep -qi "below the header lines" antigravity/.agents/workflows/build.md` → exit 0 (mirrors) — verified, see ../evidence/03-header-contract.md
