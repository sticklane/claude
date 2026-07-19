# Task 01: Add the depth ladder and trivially-satisfiable pattern to the anchoring doctrine

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. -->

Status: in-progress
Depends on: none
Priority: P1
Budget: 8 turns
Spec: ../SPEC.md (requirement R1)
Touch: docs/memory/anchored-acceptance-criteria.md

## Goal

`docs/memory/anchored-acceptance-criteria.md` carries (a) a fourth failure
pattern — the trivially satisfiable criterion, anchored per the existing
doctrine yet green-checkable by typing the searched literal — with the
spec's surveyed examples, and (b) the named criterion depth ladder
L0 text-presence / L1 artifact-structure / L2 behavior / L3 end-to-end,
the deepest-feasible rule, and the `Depth ceiling:` annotation grammar
(why deeper is infeasible + the named behavioral complement). Every other
task in this spec cites this text rather than restating it.

## Steps

1. Read the current memory doc in full (it is short) and the spec's R1.
2. Append the fourth failure pattern with the surveyed examples from the
   spec's Problem section (critique-findings-loop-closure/01,
   rigor-tier/01, the mirror-procedure-discipline grep-manifest shape).
3. Add the ladder section: level definitions, the deepest-feasible rule,
   the depth-ceiling annotation grammar, and the binding/grandfathering
   scope exactly as R5's decided text states it (cite the spec).
4. Keep the doc's existing structure and tone; this is the doctrine home
   the skills cite — no skill-procedure text belongs here.

## Acceptance

- [ ] `grep -ci 'depth ladder' docs/memory/anchored-acceptance-criteria.md`
      → ≥ 1 (0 today, verified 2026-07-19)
- [ ] `grep -ci 'trivially satisfiable'
  docs/memory/anchored-acceptance-criteria.md` → ≥ 1 (0 today,
      verified 2026-07-19). Depth ceiling: doctrine prose — behavioral
      complement is task 05's eval scenario plus tasks 02–04's
      procedure edits, which operationalize this text.
