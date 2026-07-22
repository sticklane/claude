# Critique findings — READY (2026-07-21, /critique, three rounds settled)

SPEC.md sha256: e38738b1cafa530b06586aacce97c2d6a39fd9c4d5d854487bc831a604c11a72

Critic verdict: READY (round-3 verdict READY WITH NITS; both nits were
mechanical and applied in the same pass — the settled state has no
open findings). Breakdown-ready: true written per the /critique
marker step.

Resolution history:

- Round 1 (NOT READY): 4 blockers (judge-brief blinding leak;
  spawned-session cost parity; missing hidden-script calibration
  criterion; missing crash-as-fail criterion), 3 majors, 2 minors.
  All mechanical findings applied; verified closed by round 2.
- Round 2 (NOT READY): confirmed mechanical fixes closed; two
  judgment findings gated — arm-S scope framing and the n=3
  verdict/tie/aggregate rule; one new nit (reference solutions held
  out of both arms' mounts) applied.
- Maintainer resolutions (2026-07-21 live session): scope stated up
  front — arm S is the always-on tier, launch-gated stages out of
  frame, follow-up arm S′ (agentic loop under caps, per
  specs/agentic-core-redesign D1/step 6) named and excluded from this
  spec's runs; verdict rule pre-registered — task winner at
  pass-count gap ≥2, gap 1 indistinguishable, gap-0 cost band ≥25%,
  overall winner only at ≥2 wins with no losses, else "mixed" is the
  finding.
- Round 3 (READY WITH NITS): both resolutions verified closed and
  internally consistent; nits applied in-pass — both-arms-fail
  labeled indistinguishable; two formatter-stripped continuation
  indents restored.
