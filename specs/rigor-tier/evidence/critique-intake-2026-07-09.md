# Critique intake verdict: NOT READY (2026-07-09, single-pass)

Ranked findings (from the critic's report):

1. (82) drain/reference.md is an unnamed edit locus — the tournament
   per-candidate verifier runs R4 targets live there, but no requirement,
   Touch entry, or acceptance check reaches it. Add it to R4's loci and a
   task's Touch (as R8 does for mirrors).
2. (80) R4's acceptance greps only check the literal "Rigor:" string, not
   gate-scaling behavior — add a criterion asserting the prototype branch
   in the tournament//build procedure text.
3. (70) "substitute acceptance-command runs ... and rank on them" is
   undefined against the real tournament (triple-vote >=2 PASS filter,
   findings-count rank): state prototype tournaments filter on a single
   acceptance pass/fail per candidate and rank by (pass-count, angle index).
4. (65) The headless-fallback worker template independently instructs
   test-first — condition that clause on Rigor: production or prototype
   tasks run there still do TDD.
5. (62) Say whether prototype skips /build's close-out /code-review and
   /simplify — kept or skipped, one clause.
Note: sequence rigor-tier's build after draft-auto-promotion (both edit
drain/SKILL.md + reference.md).

Route: NOT READY → human checklist. Next: amend per findings, re-run /critique.
