# Maintainability rubric (single-call judge)

Score the MAINTAINABILITY of a code change on a 1–5 scale in a single pass. You
are given only two things: the canonical task brief and the diff produced for
it. You do NOT see whether the change is correct, whether its tests pass, how
much it cost, how long it took, or anything about how or by what configuration
it was produced. Score maintainability alone, independent of correctness.

## Inputs

- **Canonical task brief** — the neutral statement of what the task asked,
  identical for every diff you score.
- **Diff under review** — the change to score.

Nothing else is provided, and nothing else may influence the score.

## Scale

- **5 — exemplary.** Clear structure, well-named, appropriately factored,
  minimal and focused; a maintainer could extend it with confidence.
- **4 — solid.** Readable and reasonably factored; minor nits only.
- **3 — workable.** Gets the shape right but carries rough edges — some
  duplication, unclear names, or thin structure.
- **2 — strained.** Hard to follow, poorly factored, or noticeably sprawling
  relative to what the task asked.
- **1 — poor.** Tangled, opaque, or so sprawling that a maintainer would
  struggle to change it safely.

## Scoring rules

- Judge only what the diff shows against what the brief asked. Do not reward or
  penalize correctness, test pass/fail, cost, or speed — those are measured
  elsewhere and are deliberately withheld here.
- A minimal, focused change that meets the brief scores high even when it is
  small; size is not quality.
- Sprawl, dead code, or churn unrelated to the brief lowers the score.

## Output

Emit exactly one line, `score: <N>`, where `<N>` is an integer from 1 to 5,
then one sentence of justification on the following line.
