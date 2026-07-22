# Name the reduce/dedupe/cap barrier between fan-out and verify

Status: open
Priority: P2
Breakdown-ready: true

## Problem

`.claude/rules/token-discipline.md`'s "Dispatch authoring" section already
names two ends of a common orchestration shape: fan-out ("parallel gather
over independent task files... hard cap and effort tiers written into the
dispatch prompt") and per-item adversarial verify (bounded
evaluator-optimizer loops, single-call rubric judges). It says nothing
about the step in between. Today's Workflow-tool (ultracode) runs on this
machine gave a concrete instance of that missing middle step done right:
an N-lens parallel fan-out merged its per-lens findings into one deduped,
severity-capped set before any per-finding verify stage ran — bounding
verify-tier spend to the capped set's size regardless of how wide the
fan-out was. Nothing in this repo's doctrine currently requires that
ordering. A future multi-lens fan-out — in a skill, or a workflow authored
by `workflow-author` — can wire an N-way fan-out straight into an N-way
per-item verify with no cap in between, and nothing here would flag it.

## Solution

Add one bullet to `.claude/rules/token-discipline.md`'s "Dispatch
authoring" section, placed after the existing "Bound evaluator-optimizer
loops..." bullet: any fan-out whose per-item outputs feed a subsequent
per-item verify or judge stage must reduce/dedupe/cap the fan-out's
results into one bounded set before that verify stage runs, so verify-tier
spend scales with the capped set, not the raw fan-out width. State the
generic shape (merge into a keyed map or list, dedupe, sort by whatever
ranking the task uses, cap at a stated number) without prescribing an
exact cap value — the cap is the task's to choose, the requirement is that
one exists and runs before verify.

## Requirements

- R1: `.claude/rules/token-discipline.md`'s "Dispatch authoring" section
  gains one new bullet, placed immediately after the existing "Bound
  evaluator-optimizer loops to 2–4 cycles..." bullet, stating the
  reduce/dedupe/cap-before-verify requirement above in the file's existing
  terse bulleted style (matching surrounding bullets' length and citation
  conventions — no new external source needed, this is an internal
  ordering rule, not a research claim).

## Out of scope

- Prescribing a specific cap number, dedupe key shape, or ranking function
  — left to each task, matching how the existing "Cap subagent returns at
  1–2k tokens" bullet states a number while this one deliberately doesn't
  (fan-out width and finding shape vary too much across tasks for one
  fixed cap to fit).
- Retrofitting this into `workflow-author`'s templates or reference.md —
  a natural follow-up once the rule exists, not required for this rule to
  land.

## Acceptance criteria

- [ ] `awk '/^## Dispatch authoring/{f=1;next} /^## /{f=0} f' .claude/rules/token-discipline.md | grep -qi 'dedupe'` — the word is present in the right section
- [ ] `awk '/^## Dispatch authoring/{f=1;next} /^## /{f=0} f' .claude/rules/token-discipline.md | tr '\n' ' ' | grep -qiE 'before[^.]*(verify|judge)'` — the ordering claim itself (not just the word "dedupe") is stated: a bullet that names deduping without tying it to running *before* verify/judge does not satisfy this. Flattened to one line first so the check doesn't depend on where the file's ~72-column wrap happens to fall, and `[^.]*` keeps the match inside one sentence so an unrelated "verify" two bullets away can't spuriously satisfy it.
- [ ] MANUAL: the new bullet sits between the existing "Bound
  evaluator-optimizer loops" bullet and the bullet that follows it in the
  file's current order (confirm no reordering of unrelated bullets)

## Parallelization

Single requirement, single file, single task — no parallelization needed.
