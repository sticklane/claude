# Task 02: Tier-dispatch doctrine block in token-discipline.md

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: pending
Depends on: none
Priority: P2
Budget: 6 turns
Spec: ../SPEC.md (requirement R2)
Touch: .claude/rules/token-discipline.md

## Goal

`.claude/rules/token-discipline.md` carries a short block making the
freehand fan-out default explicit: mechanical fan-out work dispatched
outside a skill uses the typed pinned agents
(scout/verifier/implementation-worker) or passes an explicit cheap-tier
`model` override to general-purpose; bare general-purpose at session model
is reserved for judgment work. The block cites the measured $/call
inversion (general-purpose $0.067 vs opus-pinned implementation-worker
$0.057, from the 2026-07 agentprof week).

## Touch

Only the rules file. The natural home is inside "Model and effort
matching" or "Dispatch authoring" — extend, don't duplicate: those
sections already teach tier-by-stage for SKILL-authored dispatch; this
block covers freehand dispatch specifically. CLAUDE.md gets no edit
(cite-don't-restate). Note: the drain-wake-cost spec's task 02 also edits
this file — if a drain-wake-cost drain is live, serialize (check
DRAIN-OWNER.md / coordinate via the human) rather than racing.

## Steps

1. Read ../SPEC.md R2 and the current token-discipline.md tier sections.
2. Add the block (3–6 lines), citing the $/call figures and pointing at
   ../../drain-wake-cost/EVIDENCE.md for provenance.
3. Confirm the block does not contradict the existing "Model and effort
   matching" rungs — it applies them to freehand dispatch, nothing more.

## Acceptance

- [ ] `grep -q '0\.067' /Users/sjaconette/claude/.claude/rules/token-discipline.md` → exit 0
- [ ] MANUAL: the block names the pinned agents as the default for mechanical fan-outs and reserves session-model general-purpose for judgment work (quote it as evidence)
