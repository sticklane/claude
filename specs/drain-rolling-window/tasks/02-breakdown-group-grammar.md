# Task 02: /breakdown emits the machine-readable `Group:` grammar

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P1
Budget: 10 turns
Spec: ../SPEC.md (requirement R5)
Touch: .claude/skills/breakdown/SKILL.md

## Goal

`.claude/skills/breakdown/SKILL.md` step 5 (the Parallelization-section
instruction) tells the model to emit one `- Group: NN, NN[, NN...]` line
per concurrent-safe group, instead of free-form prose, so drain can parse
group membership mechanically per R1's co-admissibility predicate. The
decision-coupling test (disjoint Touch AND no shared undecided design)
still gates which tasks may share a line — this task changes the output
format, not the judgment call.

## Touch

In scope: step 5 of the Procedure section and the task-file template's
Parallelization guidance in `.claude/skills/breakdown/SKILL.md` only.

Out of scope: the antigravity mirror
(`antigravity/.agents/skills/breakdown/SKILL.md`) — deferred to task 05
per CLAUDE.md's spec exception (mirror bundled into one closing task so
it isn't missed across a multi-task drain); do not edit it here. Also out
of scope: `.claude/skills/drain/SKILL.md` (task 01 owns the consuming
side of the same grammar).

## Steps

1. Read `.claude/skills/breakdown/SKILL.md` step 5 and the task-file
   template's Parallelization section as they exist now.
2. Use the exact grammar pinned in
   `specs/drain-rolling-window/SPEC.md`'s own `## Parallelization`
   section (written by this spec's breakdown pass, so it's ground truth,
   not this task's invention): one `Group:` line per group, format
   `- Group: NN, NN[, NN...]`, comma-and-space-separated two-digit task
   numbers matching each task file's `NN-` prefix; a task named on no
   `Group:` line runs solo. Cite that pinned paragraph from the new
   prose rather than re-deriving the format.
3. Rewrite step 5 to instruct: after applying the decision-coupling test,
   emit each surviving group as its own `- Group:` line under the
   Parallelization section (plain prose explanation may still precede
   the lines, but the lines themselves are the parseable contract).
4. Add a short worked example (2–3 lines) showing the grammar in use —
   e.g. `- Group: 02, 03` — so the instruction is unambiguous to a
   fresh session with no other context.
5. Confirm the existing decision-coupling paragraph (disjoint Touch AND
   free of shared undecided design) is preserved, not replaced — this
   task adds output-format instructions, it does not relax the judgment
   test.

## Acceptance

- [ ] `grep -c '^- Group:' .claude/skills/breakdown/SKILL.md` → ≥ 1
- [ ] `grep -c 'decision.coupling\|decision-coupling' .claude/skills/breakdown/SKILL.md`
      → ≥ 1 (the judgment test survives)
- [ ] The worked example's task numbers are two-digit and comma-space
      separated: `grep -n '^- Group: [0-9][0-9], [0-9][0-9]' .claude/skills/breakdown/SKILL.md`
      → at least one match
