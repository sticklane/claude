# First-pass success rate from agentprof role markers

Status: open
Priority: P3

## Problem

"The New SDLC With Vibe Coding" (adopted-practice record in
docs/external-playbooks.md) names first-pass success rate as the primary
OpEx driver of agentic work: retries and salvage attempts, not the first
attempt, are where token spend compounds. The toolkit is about to have
the raw material and still no rate: `specs/agentprof-instrumentation/
SPEC.md` lands `role:` frames distinguishing drain's `worker-attempt1`
from `worker-relaunch` and `worker-tournament-t1..t3` dispatches, and
`specs/workboard-weekly-cost-view/SPEC.md` builds a 7-day rolling cache
of profile samples — but neither computes verdict outcomes or any success
rate, and nothing surfaces one.

This spec depends on both of those landing first; it is a small delta on
top of them, not a parallel mechanism.

## Solution

Compute first-pass success rate from the `role:` frames already in the
cost view's cached samples, in the same code path that aggregates the
weekly cost panel:

- Denominator: distinct attempt-1 dispatches in the window (distinct
  dispatch identities carrying a `role:worker-attempt1` frame).
- Numerator: those with no relaunch or tournament sibling for the same
  task in the window (presence of `role:worker-relaunch` /
  `role:worker-tournament-*` for the task marks the first pass as
  failed).
- Surface: a rate (numerator/denominator, with the absolute counts) in
  workboard's cost view, per week and per skill/project alongside the
  existing spend dimensions. Windows with a zero denominator display
  "n/a", never 100%.

The task identity used to pair attempt-1 with its retries is whatever the
role-marker samples make available (the dispatch's task-file path if
present in the stack, else the spawn identity); pinning it exactly is the
first implementation task's job and must be recorded in the spec's
evidence.

## Requirements

- R1: The rate is computed from cached samples only — no new transcript
  parsing pass and no LLM call (the cheap-profile constraint carried over
  from agentprof-instrumentation).
- R2: Definition exactly as in Solution: attempt-1 dispatches without
  retry siblings ÷ all attempt-1 dispatches; zero-denominator windows
  render "n/a".
- R3: Surfaced in the workboard cost view next to spend, per week and per
  skill/project.
- R4: Absolute counts shown with the rate (a 1/1 week must not read like
  a 40/40 week).
- R5: Any skill-text or mirror changes ride the same-commit mirroring +
  plugin.json bump convention via the tasks' `Touch:` lines (expected to
  be code-only; the requirement exists so a drift into skill text isn't
  silently un-mirrored).

## Out of scope

- Role markers for skills other than drain (the instrumentation spec's
  own scope).
- Verdict-quality weighting (a merged-but-later-reverted task still
  counts as first-pass success) — rate of retry, not rate of truth.
- Historical backfill beyond the cost view's rolling window.

## Acceptance criteria

- [ ] Depends-first check: `specs/agentprof-instrumentation` and
      `specs/workboard-weekly-cost-view` tasks are `done` before this
      spec's tasks leave `pending`.
- [ ] Unit test: a fixture sample set with 3 attempt-1 dispatches, one of
      which has a relaunch sibling, yields 2/3 (R1, R2).
- [ ] Unit test: an empty-window fixture renders "n/a", not a division
      error or 100% (R2).
- [ ] The workboard cost view renders the rate with counts per week
      (screenshot or DOM-grep evidence) (R3, R4).

## Open questions

- Which stack frame pins task identity for the attempt-1/retry pairing —
  resolved by the first implementation task against the landed
  instrumentation format, recorded in evidence.
