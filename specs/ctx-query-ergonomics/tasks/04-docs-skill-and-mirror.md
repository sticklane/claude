# Task 04: docs — skill command table + reading ladder (skill + antigravity mirror)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Unblock) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Status is blocked: this task edits the same SKILL.md that two sibling specs (ctx-skill-token-doctrine, ctx-static-analysis-augmentation) also edit, and it depends on prose those specs create (the reading ladder + rung-2 ast-grep) that is not present yet. The Unblock: run: line is the mechanical readiness check; nothing auto-flips it. -->

Status: blocked
Unblock: run: grep -q 'ast-grep' .claude/skills/ctx/SKILL.md && grep -qi 'rung' .claude/skills/ctx/SKILL.md && echo READY
Depends on: 01, 02, 03
Priority: P3
Budget: 12 turns
Spec: ../SPEC.md (requirement R4)
Touch: .claude/skills/ctx/SKILL.md, antigravity/.agents/skills/ctx/SKILL.md

## Goal

The `ctx` skill command table (both `.claude/skills/ctx/SKILL.md` and the
antigravity mirror) gains rows for `ctx show` and the selector / filter forms.
The reading ladder (created by specs/ctx-skill-token-doctrine R2) is updated so
rung 3 becomes `ctx show <symbol>` (read a located symbol's body) and rung 4
folds in sliced `Read` (`offset`/`limit`) for context exceeding one symbol's
span, whole-file only when about to edit. Rungs 1 and 2 are NOT touched — rung
2's ast-grep enrichment (from ctx-static-analysis-augmentation R1) is preserved
exactly.

## Touch

Only the two `SKILL.md` files. The antigravity file is a paraphrased port, NOT a
byte-identical mirror — port the concepts, do not diff for equality
(docs/memory/workboard-mirror-verbatim.md: only workboard's `.py` files are
byte-identical across trees; prose skill mirrors are paraphrased).

## Blocked — why, and how to unblock

This task is `Status: blocked` because the reading ladder it edits does not yet
exist in SKILL.md: the four-rung ladder is created by
specs/ctx-skill-token-doctrine R2, and rung 2's ast-grep enrichment by
specs/ctx-static-analysis-augmentation R1. Both sibling specs edit this same
SKILL.md and its mirror and have no `tasks/` breakdown yet, so this is a
cross-spec file collision as well as a content dependency. Landing order (per
SPEC R4): after ctx-skill-token-doctrine R2 and after any
ctx-static-analysis-augmentation SKILL.md edits, serialized, editing skill +
mirror in the same commit.

Nothing auto-flips this. `/drain` does NOT re-run `Unblock: run:` on a
pre-existing blocked task. Once the ladder + rung-2 ast-grep have landed (the
`Unblock: run:` grep prints `READY`), a human or a later session re-checks and
flips `Status:` to `pending`.

## Steps (once unblocked)

1. Add command-table rows in BOTH files for: `ctx show <symbol> [--head N]`, the
   `<path>:<name>` / `--in` selector form, and the `--in`/`--not-in` filters.
2. Rewrite ONLY rungs 3 and 4, verbatim as SPEC R4 gives them:
   - rung 3 → `ctx show <symbol>` when a located symbol's body must be read;
   - rung 4 → `Read` — sliced (`offset`/`limit`) when needed context exceeds one
     symbol's span, whole-file only when about to edit.
   Leave rungs 1 and 2 exactly as landed.
3. In the antigravity mirror, port the same content (paraphrase-compatible).

## Acceptance

<!-- Depth ceiling: L1 (docs prose). Deeper verification is infeasible for a doc
edit; the behavioral complement is a human read of the ladder prose confirming
rungs 3-4 read as SPEC R4 specifies and rungs 1-2 are unchanged. -->

- [ ] `grep -c 'ctx show' .claude/skills/ctx/SKILL.md` → ≥1 (new command-table / ladder row)
- [ ] `grep -ci 'ctx show' antigravity/.agents/skills/ctx/SKILL.md` → ≥1 (mirror ported)
- [ ] `grep -q 'ast-grep' .claude/skills/ctx/SKILL.md` → exit 0 (rung 2 augmentation R1 grep preserved)
