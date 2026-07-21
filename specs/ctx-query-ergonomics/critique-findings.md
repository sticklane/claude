# Critique findings — READY WITH NITS (2026-07-20, post-authoring critique, round 2)

SPEC.md sha256: 6a307e2fe256b018f19f70aabed066b0da8d2a8c62d44e83d86626c1ba815791
Critic verdict: READY WITH NITS (round 2), after round-1 READY WITH NITS.

Round 1 nits (applied in commit 8fd11b6): R2 staleness acceptance now
requires a span-shifting edit (sweep-before-resolve pinned); R4 states
the final four-rung ladder; landing-order serialization added.

Round 2 findings, applied same day after the recheck:
1. (conf 70) R4's "verbatim whole-ladder" mandate collided with
   augmentation R1's rung-2 ast-grep enrichment (R4 is the last writer;
   nothing re-checked R1's grep at R4's landing). Fixed: R4 scoped to
   rungs 3-4 + command table only, and its acceptance re-runs
   augmentation R1's ast-grep grep.
2. (conf 40) Supersession wording — now "rung 3 becomes ctx show;
   sliced Read folds into rung 4".
3. (conf 45) R5 had no runnable acceptance — now annotated as a
   design-review constraint, not a testable requirement.

(Hash reflects post-fix bytes; the round-2 fixes have not had a further
critic pass — critic agent unavailable at close. Sibling verdicts:
ctx-skill-token-doctrine READY, ctx-static-analysis-augmentation READY
with fork-gate on R2/R3 only.)
