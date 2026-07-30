# Critique findings — human-blocker-staleness

Spec-sha256: 6af4cad44489cb40520399091f80a236de0f54c3813f6986bd544a3f1aaed3bb
Verdict: READY WITH NITS

## 2026-07-29 — round 4 (final)

Rounds 1–3 returned NOT READY (11, 8, and 6 findings); all were applied in
`09ceed5d`, `1dfdf7be`, and `e0d31f3b`. The design changed twice rather than
being patched: a binary allowlist became a reviewed-probe-script model after
`git -c alias.p='!touch PWNED' p` was reproduced locally, and the exit contract
became three-valued after "cannot determine" was found collapsing into "stale".

Round 4 returned READY WITH NITS with three one-phrase findings, all applied:

1. (82) Criterion 10 was unsatisfiable under the new exit-3 rule — a
   cross-repo probe lands in `unknown` on a fresh clone, so the two named
   buckets could not list exactly the surviving entries. `unknown` added to
   the bucket list. The live `~/ynab-mcp-new` entry is the concrete case.
2. (76) R4's `unknown` and `violation` buckets overlapped on a nonexistent
   probe script, because the git-root edit in `e0d31f3b` displaced R2's
   "must exist as a regular executable file" clause. Restored to R2 and
   narrowed R4's wording to an `exec` failure.
3. (62) Nothing bound the *shipped* probes to R3's argv rule — the argv
   fixture exercises a fixture probe. Criterion 8 now requires each shipped
   probe to take no arguments or validate against a fixed set.

No findings remain open.
