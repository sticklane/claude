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
