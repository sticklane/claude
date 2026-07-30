# Task 07: the machine-readable acceptance-block grammar

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->

Status: pending
Depends on: none
Priority: P0
Budget: 25 turns
Spec: ../SPEC.md (requirements EP11, decision D2)
Touch: docs/memory/acceptance-block-grammar.md, .claude/skills/idea/SKILL.md, tests/test_acceptance_block_grammar.sh, tests/inventory/drain-economy-07.json, specs/toolkit-core-simplification/surface-inventory/drain-economy-07.json

## Goal

A spec's `## Acceptance criteria` block becomes machine-runnable. Each
criterion carries a stable id and follows one grammar:
`- [ ] A<k> (<cheap|expensive>): \`<command>\` — <expected>`. The grammar is
documented as a sibling of `docs/memory/anchored-acceptance-criteria.md`, and
`/idea`'s SPEC.md template emits it. Backfill is lazy by design: nothing
rewrites existing specs, and a non-conforming block is a filing event for
whoever focus-drains that spec, not a migration.

## Touch

This task writes the grammar and the template only — it does not write a parser
(task 08's `bin/spec-gate`) and does not change `/critique`'s READY bar (task
13). It must NOT retrofit existing `specs/*/SPEC.md` acceptance blocks; the
spec makes backfill lazy on purpose, and a sweep here would collide with every
in-flight spec in the repo.

`docs/memory/anchored-acceptance-criteria.md` owns the L0–L3 depth ladder and
is not restated here — the new file cites it and covers only the block's
syntax, ids, and tier marking.

## Steps

1. Write the failing test first: `tests/test_acceptance_block_grammar.sh`
   asserting the grammar against fixture blocks — a conforming block parses
   with ids and tiers recovered, a missing id fails, an unknown tier fails, a
   criterion with no backticked command fails, and duplicate ids within one
   block fail. The test owns a small reference parser or a documented regex so
   the grammar has one executable definition before any consumer exists.
2. Write `docs/memory/acceptance-block-grammar.md`: the line grammar, id
   stability rules (ids never renumber once published; a removed criterion's id
   is retired, not reused), and a pointer to the depth ladder in
   `docs/memory/anchored-acceptance-criteria.md` for how deep a criterion
   should reach.
3. State the two rules the tiers actually encode, per the spec's D11/D12 and
   EP11: `cheap` is what an unattended worker may execute under the command
   policy, `expensive` is a paid or gated run only a human launches and whose
   result a human records in `acceptance-status.json`; and every criterion of
   either tier is read-only or idempotent, building any state it needs in a
   fixture rather than in the live tracker or working tree.
4. Update `.claude/skills/idea/SKILL.md`'s SPEC.md template so generated
   acceptance criteria carry ids and tiers, keeping the existing
   end-with-an-end-to-end-check instruction.
5. State the lazy-backfill rule in the grammar doc: a focus spec whose block
   does not parse gets one blocking child, "conform acceptance block to
   grammar", filed by the drain that hit it — never a guess at what the
   criterion meant.
6. Register the new doc and test in the surface and test inventories.

## Acceptance

- [ ] `bash tests/test_acceptance_block_grammar.sh` → exits 0, reports 0
      failures, and its conforming-block case recovers every id and tier. **L2**
- [ ] The malformed fixtures each fail: missing id, unknown tier, no command,
      duplicate ids — asserted inside the test above, one case each. **L2**
- [ ] `grep -c 'read-only' docs/memory/acceptance-block-grammar.md` → ≥ 1 and
      `grep -c 'expensive' docs/memory/acceptance-block-grammar.md` → ≥ 1, with
      the human-launched and human-recorded rule stated on the expensive tier
      (both verified 0 in the repo's docs today, 2026-07-30). **L0** — Depth
      ceiling: the rules bind authors and `/critique`'s READY bar (task 13);
      their behavioral complement is task 13's NOT-READY eval fixture.
- [ ] `grep -c 'acceptance-block grammar' docs/memory/acceptance-block-grammar.md`
      → ≥ 1 and `grep -c 'anchored-acceptance-criteria' docs/memory/acceptance-block-grammar.md`
      → ≥ 1 (the phrase verified 0 across the repo's docs today,
      2026-07-30). **L0** — Depth ceiling: a grammar document has no runtime;
      its behavioral complement is the parser test above and `bin/spec-gate`'s
      suite in task 08.
- [ ] `awk '/^## Acceptance criteria/{f=1;next} f&&/^## /{f=0} f' .claude/skills/idea/SKILL.md | grep -cE '^- \[ \] A[0-9]+ \((cheap|expensive)\):'`
      → ≥ 1, proving the template emits the grammar rather than describing
      it. **L1**
- [ ] `git diff --name-only | grep -c '^specs/.*/SPEC.md$'` → 0, proving no
      existing spec was retrofitted. **L1**
- [ ] `bash tests/test_doc_links.sh` → passes, proving the new doc's links
      resolve. **L2**
- [ ] `bash scripts/check.sh` → `check.sh: green`. **L2**
