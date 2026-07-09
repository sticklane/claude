# Task 01: Stub-intake contract in drain SKILL.md + human-gates weave

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions / ## Decisions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P1
Budget: 16 turns
Spec: ../SPEC.md (requirements R1 SKILL-side, R4, R5, R7 SKILL-side)
Touch: .claude/skills/drain/SKILL.md, docs/human-gates.md

## Goal

`drain/SKILL.md` carries the stub-intake contract (trigger: same
exhaustion check as critique intake, evaluated after critique intake and
before 3b's loop-back; once per stub per run across generations via the
`Stub-intake-failed:` baton line; the assess → gate → act pipeline itself
lives in reference.md — SKILL.md carries the contract and pointer). The
exit checklist gains the "promoted this run" section and its pinned
"six-section" count text becomes seven. Every SKILL.md manual-promotion
statement is revised per the spec's R7 enumeration (the inventory-step
"only a human promotes" statement, the discoveries-paragraph "only a
human edits" variant, and the critique-intake "explicitly not intake"
passage — which becomes a pointer to stub intake), and SKILL.md's two
draft-gate "reason 1" citations are corrected to reason 4.
`docs/human-gates.md` reason 4 is revised by WEAVING — its
disable-model-invocation launch rationale is preserved in substance, with
the draft-gate relocation (human-only → hard screen + re-authored Goal +
adversarial review; human audits via the exit checklist and may demote
with a `Demoted:` line) woven in alongside.

## Touch

Only the two files in the header. Do NOT touch `drain/reference.md` or
the screen script (task 02 owns them — cite the spec-pinned names:
`Stub-intake-failed:`, `.claude/skills/drain/screen-stub.sh`), nor
`antigravity/` / `.claude-plugin/plugin.json` (task 03).

## Steps

1. Read `../SPEC.md` Solution + R1/R4/R5/R7 (SKILL-side clauses).
2. Add the stub-intake contract next to the critique-intake branch
   (after it in evaluation order, before 3b's loop-back).
3. Exit checklist: add "promoted this run" (stub, verdict, criteria
   source) and bump the count text six → seven.
4. Revise the three R7 SKILL.md statements; correct both "reason 1"
   citations to reason 4.
5. Weave docs/human-gates.md reason 4 per the Goal — preserve the
   disable-model-invocation rationale verbatim in substance.
6. `bash evals/lint-ultra-gate.sh` green (drain is ultra-path).

## Acceptance

- [ ] `grep -qi "stub intake" .claude/skills/drain/SKILL.md` → match (absent today)
- [ ] `grep -qi "promoted this run" .claude/skills/drain/SKILL.md` → match, and the exit-checklist count text says seven (cite the line)
- [ ] `rg -Uqi "only a human (promotes|edits)|only a human \(or|Promotion is manual|promoted manually|only a human\s+(promotes|edits)" .claude/skills/drain/SKILL.md` → exit 1, no matches
- [ ] `grep -n "reason 1" .claude/skills/drain/SKILL.md` → no draft-gate citation remains (cite what's left, if anything)
- [ ] `grep -qi "adversarial" docs/human-gates.md` → match, and reason 4 still carries the disable-model-invocation launch rationale (cite the surviving sentence)
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0
