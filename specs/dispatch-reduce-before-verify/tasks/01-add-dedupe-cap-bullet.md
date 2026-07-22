# Task 01: Add the reduce/dedupe/cap-before-verify bullet to token-discipline.md

Status: pending
Depends on: none
Priority: P2
Budget: 6 turns
Spec: ../SPEC.md (requirement R1)
Touch: .claude/rules/token-discipline.md

## Goal

`.claude/rules/token-discipline.md`'s "Dispatch authoring" section gains one
new bullet, placed immediately after the existing "Bound evaluator-optimizer
loops to 2–4 cycles..." bullet, stating that any fan-out whose per-item
outputs feed a subsequent per-item verify or judge stage must reduce/
dedupe/cap the fan-out's results into one bounded set before that verify
stage runs — so verify-tier spend scales with the capped set, not the raw
fan-out width. State the generic shape (merge into a keyed map or list,
dedupe, sort by whatever ranking the task uses, cap at a stated number)
without prescribing an exact cap value.

## Touch

Only `.claude/rules/token-discipline.md`, and only inside the
"## Dispatch authoring" section. Do not reorder or reword any existing
bullet in that section — insert one new bullet in the stated position and
leave everything else byte-identical.

**Depth ceiling:** this is a doctrine/prose-file edit, not executable code —
every acceptance criterion below is L0 (text-presence, phrase-anchored),
which is the deepest feasible level for a rule bullet's own wording.
Behavioral complement: a future workflow-authoring session either follows
the new bullet or doesn't — that's a manual-pending human/critic read on
the next authored script that fans out into a per-item verify stage, not
something this task's acceptance gate can exercise itself.

## Steps

1. Read `.claude/rules/token-discipline.md`'s "## Dispatch authoring"
   section in full (it runs from the `## Dispatch authoring` heading to the
   next `## ` heading).
2. Locate the existing bullet beginning "Bound evaluator-optimizer loops to
   2–4 cycles...". Insert one new bullet immediately after it (before the
   "Default to a single-call rubric judge..." bullet that currently follows),
   in the file's existing terse bulleted style, stating the reduce/dedupe/
   cap-before-verify requirement from the Goal above. Explicitly state the
   ordering (dedupe/cap happens *before* the verify/judge stage runs), not
   just that deduping exists.
3. Run every acceptance command below and confirm all pass.

## Acceptance

- [ ] `awk '/^## Dispatch authoring/{f=1;next} /^## /{f=0} f' .claude/rules/token-discipline.md | grep -qi 'dedupe'` → matches (the word is present in the Dispatch authoring section)
- [ ] `awk '/^## Dispatch authoring/{f=1;next} /^## /{f=0} f' .claude/rules/token-discipline.md | tr '\n' ' ' | grep -qiE 'before[^.]*(verify|judge)'` → matches (the ordering claim — dedupe/cap *before* verify/judge — is stated, not just the bare word "dedupe")
- [ ] MANUAL: the new bullet sits between the existing "Bound evaluator-optimizer loops" bullet and the "Default to a single-call rubric judge" bullet that follows it, with no other bullet in the section reordered or reworded
