# Task 01: human-blockers.md — Blocks: clause, plain-language rule, mandatory bullet

Status: pending
Depends on: none
Priority: P1
Budget: 16 turns
Spec: ../SPEC.md (requirements R1, R2, R6)
Touch: .claude/rules/human-blockers.md

## Goal

`.claude/rules/human-blockers.md`'s entry grammar carries a `Blocks:`
clause, the doc states the plain-language authoring rule for the action
clause explicitly, and the "Rules" list gets a new bullet making `Blocks:`
mandatory (with the `Blocks: unclear — <reason>` fallback) on every entry
filed after this change.

## Touch

Only `.claude/rules/human-blockers.md`. Do not touch
`.claude/skills/drain/reference.md` (task 02), `HUMAN.md` (task 03), or
`antigravity/.agents/workflows/drain.md` (task 04) — all Touch-disjoint,
no shared design decision (this spec pins the exact grammar and wording).

## Steps

1. Read `.claude/rules/human-blockers.md`'s current "Entry grammar" and
   "Rules" sections.
2. Extend the grammar line per SPEC.md's Requirements R1: `- [ ] <ISO date>
· <source path> · <ask|run|provision|decide> — <plain-language action>
— Blocks: <impact>`.
3. Add the plain-language rule (R2): state explicitly, near the grammar
   line, that the action clause must be readable and actionable without
   opening the source file — expand jargon/task-ID shorthand into what it
   actually means.
4. Add one new bullet to the "Rules" list (R6): the `Blocks:` clause is
   mandatory on every new entry; a filer that cannot determine impact
   writes `Blocks: unclear — <one-line reason>` rather than omitting the
   clause.

## Acceptance

- [ ] `grep -c 'Blocks: <impact>' .claude/rules/human-blockers.md` → 1
- [ ] `grep -n 'readable and actionable' .claude/rules/human-blockers.md` →
      at least one match
- [ ] `grep -c 'Blocks: unclear' .claude/rules/human-blockers.md` → ≥ 1
- [ ] End-to-end (R2's readability bar): as the implementing/verifying
      agent, with no other context beyond this file, read only
      `.claude/rules/human-blockers.md`'s updated grammar + Rules sections
      and write one sentence stating what a `Blocks:` clause on a
      hypothetical filed entry would mean — record that sentence as
      evidence; it must name both the ask and its impact.
