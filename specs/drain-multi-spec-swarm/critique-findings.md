# Critique findings — NOT READY (2026-07-18, round 3, resumed via /resume-handoff)

SPEC.md-hash: b05100e8a8c30756c5faea4906aa1d53c11281482da302e423ea944c8811a06d

Critic verdict: NOT READY. Ranked findings (most damaging first):

1. **R2 widens only the Touch-disjointness clause, but the admission
   predicate also AND's a co-admissibility (`Group:`) clause that no
   cross-spec pair can ever satisfy; implemented literally, the spec is a
   no-op** (confidence 85). The existing admission rule
   (`reference.md:1644-1652`, mirrored `SKILL.md:151-155`) admits a task
   only when ALL hold: `Status: pending` + deps done, Touch-disjoint from
   the claim set, AND co-admissible — "two tasks may run together iff one
   `Group:` line in the owning spec's Parallelization section names both.
   A task on no `Group:` line ... runs only alone (admitted only when the
   window is empty)." R2 (`SPEC.md:102-108`) and Solution bullet 2
   (`SPEC.md:62-67`) only widen the Touch-disjointness comparison set from
   "this spec's in-progress tasks" to "every claimed spec's in-progress
   tasks" — they never touch co-admissibility. But a `Group:` line lives in
   one spec's Parallelization section and can never name a task in a
   different spec, so every cross-spec pair fails co-admissibility and is
   treated as "runs only alone." Result: with the ≤10 window, at most ONE
   task total runs at a time across all claimed specs — the raised cap and
   the entire swarm are dead on arrival. Smallest fix: R2 must state the
   `Group:`/co-admissibility constraint is spec-scoped, and cross-spec task
   pairs are co-admissible whenever their `Touch:` sets are disjoint. Add an
   acceptance criterion asserting two Touch-disjoint tasks in _different_
   specs co-admit — the current simulation fixture only tests spec-level
   footprint admission (R1/R5), not the task-window co-admission R2 governs.

2. **Nit (confidence 60)** — R4's "byte-identical dispatch behavior" is
   unfalsifiable by its mapped check. The acceptance criterion only asserts
   the admission algorithm returns exactly 1 claim for a 1-spec fixture; it
   cannot prove _dispatch_ behavior is byte-identical to today's path (needs
   a live `/drain` run, which unattended workers can't do). Acceptable as
   the best available proxy; consider softening R4's wording to "produces a
   single claim identical to the single-spec path."

Verified as holding (round-1/round-2 fixes landed correctly): anchors
accurate against current file state (`"At most one dispatch lease is held
at a time"` at `SKILL.md:33`; SKILL.md is 505 lines; `swarm`/`already-green`/
`single global` all grep to 0 today); `docs/memory/drain-dispatch-lessons.md`
line refs (`:64-80`, `:134-151`) resolve exactly and R7/R2 adopt them without
contradiction (round-1 concern cleared); "priority-then-path tie-break" R4
genuinely exists for spec selection; R6 negative-constraint check and R4's
degenerate 1-spec fixture (round-2 fixes) are present; mirror files exist and
`codex/.agents/skills/drain/SKILL.md` correctly required as real content per
R10; plugin.json at 0.9.19 (bump criterion satisfiable).

Next step: resolve finding 1 (a design decision on cross-spec
co-admissibility semantics, not mechanical — surfaced to the user rather
than auto-applied) plus optionally finding 2's wording softening, then
re-run `/critique` (round 4, still within the 2-4 cycle bound).

## Round 4 (2026-07-18, resumed via /resume-handoff) — still NOT READY

SPEC.md-hash: d766c6584ee3e83cdfcb8aa041b13d448d83c807f4d9434b5a10d4f6a83e3b63

Round-3's fix (Group-line co-admissibility scoped to same-spec; cross-spec
pairs co-admit on Touch-disjointness alone) verified internally consistent
against the actual rule at `reference.md:1638-1654`. But it fixed only one
half of the same clause and left its enforcement sibling untouched, plus
surfaced further composition gaps:

1. **The round-3 fix left the "runs only alone / window empty" enforcement
   sentence unaddressed — it still forces solo (ungrouped) tasks to wait for
   a globally empty window** (confidence 68). `reference.md:1650-1654`, right
   after the Group-line sentence round-3 scoped, says: "A task on no
   `Group:` line ... runs only alone (admitted only when the window is
   empty)... 'Window empty' means zero live in-flight workers." R2's fix
   scoped the _Group-line_ sentence to same-spec but never reconciles this
   _next_ sentence. For an ungrouped/solo task — exactly the motivating
   example (`commit-message-doctrine` et al. are small specs whose
   dispatchable tasks are very plausibly ungrouped) — the shipped prose now
   says both "cross-spec Touch-disjoint pairs co-admit" AND "an ungrouped
   task runs only alone until the window is globally empty," which
   contradict. Drain is model-executed from this prose, so the
   "run-alone/global-empty" reading can re-defeat cross-spec concurrency for
   precisely the tasks the feature targets. Compounding it: the only
   _behavioral_ acceptance check is a standalone reimplementation of the
   algorithm, not the shipped `reference.md` prose drain actually executes
   — so this contradiction has zero acceptance coverage today. Smallest fix:
   add a clause requiring the "runs only alone (window empty)" statement and
   its "window empty" definition be re-scoped to _the task's own spec's_
   in-flight set (or explicitly overridden for cross-spec pairs).

2. **"Rules bind only when W > 1" vs. the W=1 default that no-argument
   /drain runs** (confidence 65). `reference.md:1640-1642`'s section
   preamble — the section this spec extends — says the rules "bind only
   when W > 1 (the default W=1 admits one task alone and merges it before
   the next)." R4/Solution require no-argument `/drain` (default W=1) to
   swarm-claim by default. The spec never states whether spec-level lease
   claiming (R1) is exempt from the W>1 gate; an implementer can faithfully
   tuck R1 under the "bind only when W>1" preamble, so default /drain never
   swarms — contradicting R4. Smallest fix: state R1 fires independently of
   the per-spec W>1 gate, at default W=1.

3. **Per-spec W (≤5) vs. global ≤10 / 3-spec cap composition is
   unspecified** (confidence 60). With 3 claimed specs each capable of W up
   to 5, requested workers (15) exceed the global ≤10. The spec never says
   how the budget is allocated (shared global window? per-spec W still ≤5
   with a global ceiling? first-come?). Dormant at default W=1 so lower
   cost, but unresolved for any elevated-W path. Smallest fix: one sentence
   on how ≤10 composes with per-spec W.

4. **Nit (confidence 60)** — R7's only acceptance check greps for
   "already-green," which a worker can satisfy by inserting the token
   without implementing any of R7's real structure (naming attributable
   lines, citing the sibling's `evidence/spec-review.md` by path,
   instructing exclusion). Consider anchoring on a phrase requiring
   co-occurrence with the citation behavior.

Next step: this round surfaced two more genuine design-composition gaps
(findings 1-2) beyond a straightforward mechanical fix, on top of round 3's
already-JUDGMENT finding — surfaced to the user rather than auto-applied,
per token-discipline's 2-4 cycle evaluator-optimizer bound (this is cycle 4,
the top of that bound).

## Rounds 5-9 (2026-07-18/19, resumed via /resume-handoff) — settled READY WITH NITS

SPEC.md-hash: 9898f4591de80b7ff54d535d47a7083eba5a5ae15e444c86715c64fa714d57df

User answered round 4's three design questions (window-empty scoped
same-spec; R1 fires independent of the W>1 gate; one shared global ≤10
window replacing independent per-spec summing, not the per-spec `W≤5`
ceiling itself). Rounds 5-6 were pure acceptance-criterion-anchoring
corrections (two vacuous greps matching unrelated pre-existing substrings,
one line-wrapped phrase never matching) — all mechanical, applied
unconditionally per the MECHANICAL-finding rule. Round 7 found one missing
acceptance branch (R12's reference.md-relocation case uncovered) — mechanical,
fixed. Round 8 found R2 and R12 used identical "per-spec ≤5" language to
imply contradictory models — clarified as a two-level cap (per-spec `W≤5`
unchanged; only independent cross-spec summing is dropped, replaced by a
shared ≤10 pool) and added a criterion guarding the per-spec ceiling's
survival. Round 9 (final): **READY WITH NITS**, two minor findings —

1. (confidence 62, applied) The two-level cap's central throttle behavior
   had no runnable simulation fixture, only prose greps. Fixed: added
   fixture case (e) — 3 specs × 5 disjoint tasks each (15 candidates)
   asserts exactly 10 admitted, none exceeding its own spec's `W`.
2. (confidence 55, left as-is — below the critic's own report threshold)
   R2/Solution's phrasing "a single claimed spec's own `W`" reads as
   per-spec-configurable when `W` is actually set once per drain run. Noted
   as a future wording clarity improvement, not applied — harmless since
   the only load-bearing value (≤5) is identical across specs regardless
   of phrasing, and re-triggering a 10th critique round for pure wording
   polish was judged not worth the token cost after 9 rounds.

`Breakdown-ready: true` written; this spec self-chains into `/breakdown`
next per the idea skill's own conventions (not a gated stage, no additional
user authorization needed for this specific step).
