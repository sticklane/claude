# Critique findings — READY WITH NITS (2026-07-19)

Spec-hash: sha256:26631c293a833af6e6d68b8d120c402cc8610d53014f1b873b83638645918211
Critic verdict: READY WITH NITS (round 3; wording nit applied).
`Breakdown-ready: true` written.

## 2026-07-19 — round 3 (settled)

1. NIT (conf 63, applied): "verified <date>" was labeled both
   "ladder-era" (binding trigger) and "pre-ladder" (exemption clause)
   within R5. Reworded to "the markers the ladder keys on" — the
   NOT-done vs done scoping already fully determined behavior.

## 2026-07-19 — round 2 (all applied)

1. HIGH: self-detecting binding over-bound done work carrying
   pre-ladder "verified" notes, contradicting Out-of-scope bullet 1 —
   done/archived exemption made unconditional.
2. MED: R6 committed-half criterion overclaimed ("hollow assert cannot
   pass") — relabeled honest L1 shape check; the paid run is the
   behavioral half.
3. NIT: "five spec: sweep commits" overcounted — corrected to four
   remediation commits plus the grandfathering-narrowing commit.

## 2026-07-19 — round 1 (all applied)

1. HIGH: sweep referenced as same-PR deliverable with no requirement,
   criterion, or bounded list — now points at the landed sweep commits
   with self-detecting binding scope.
2. MED: JUDGMENT placement unverifiable (gameable could be appended to
   the MECHANICAL bullet) — mandated verbatim sentence
   "gameable criteria are JUDGMENT-class, never MECHANICAL" + anchor.
3. NIT: classification half of R2/R3 unanchored — 'ladder level'
   anchors added (verified 0).
4. NIT: R6 assert hollow-stub risk — bash -n + failure-construct +
   content greps added (later relabeled L1 in round 2).
