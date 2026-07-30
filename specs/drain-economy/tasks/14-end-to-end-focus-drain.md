# Task 14: the end-to-end focus-drain scenario

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->

Status: pending
Depends on: 05, 06, 09, 10, 11, 12, 13
Priority: P2
Budget: 25 turns
Spec: ../SPEC.md (acceptance criterion A22)
Touch: evals/drain/07-focus-e2e/setup.sh, evals/drain/07-focus-e2e/prompt.txt, evals/drain/07-focus-e2e/assert.sh, evals/drain/07-focus-e2e/allowed-tools.txt, evals/drain/07-focus-e2e/skill-deps.txt, evals/drain/07-focus-e2e/timeout-seconds.txt, tests/inventory/drain-economy-14.json

## Goal

One scenario exercises the whole mechanism as a user would. On a fixture repo
with `NOW.md = [feat-a, feat-b]` — feat-a holding 4 issues (one with a
cross-spec blocking dep homed in feat-b, one `ask:`-blocked), 2 adjacent
discoveries seeded, and 1 chore bead — a bare `/drain` finishes with triage
holding 2, the imported dep worked and attributed to its donor, one
spillover-and-return recorded, the chore reported in its own section, feat-a's
ceremony executed with acceptance moving 0/2 → 2/2, and `bin/spec-status`
showing feat-b untouched for burnup.

## Touch

Fixture and assertions only. This task adds no mechanism: if a fixture cannot
be satisfied, the defect belongs to the task that owns that mechanism and is
filed as blocking work against it, never patched here.

Every dependency listed above must have landed — this scenario is the spec's
one expensive end-to-end criterion, and running it against a partial
implementation produces a failure that says nothing useful.

## Steps

1. Build the fixture repo in `setup.sh`: the two-slug NOW.md, feat-a's four
   issues with the cross-spec dep and the `ask:` blocker, feat-b's donor issue,
   two seeded adjacent discoveries, one `chore` bead, and acceptance blocks on
   both specs so `bin/spec-gate` can score them.
2. Write `assert.sh` against observable end state, one assertion per clause of
   the goal above, each naming what it checks so a failure identifies its
   mechanism: triage count, imported-dep attribution, spillover-and-return
   record, chore section placement, ceremony completion, acceptance 0/2 → 2/2,
   and feat-b's untouched burnup.
3. Set a timeout that fits a multi-issue run rather than a single-issue one,
   and keep `allowed-tools.txt` to what the scenario genuinely needs.
4. Register the scenario in the test inventory and confirm
   `evals/lint-eval-coverage.sh` passes.

## Acceptance

- [ ] `ls evals/drain/07-focus-e2e/ | wc -l` → 6. **L1**
- [ ] `grep -c 'assert' evals/drain/07-focus-e2e/assert.sh` → ≥ 7, one per
      clause of the goal. **L1**
- [ ] `bash evals/lint-eval-coverage.sh` → passes with the scenario
      registered. **L2**
- [ ] `bash evals/run.sh drain` → the end-to-end scenario passes with all seven
      assertions green. **L3** — `manual-pending`: this is the spec's
      `expensive` end-to-end criterion, a paid headless session an unattended
      worker must not launch (`docs/memory/unattended-worker-tool-limits.md`).
      A human runs it and records the result on this task.
- [ ] `bash scripts/check.sh` → `check.sh: green`. **L2**
