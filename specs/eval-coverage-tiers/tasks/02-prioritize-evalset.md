# Task 02: prioritize evalset (happy path + adversarial)

<!-- Machine-read fields; body sections never parsed by orchestrators. -->
<!-- Append-only for workers: flip own Status:, tick checkboxes, add evidence lines, maintain plan block. -->

Status: done
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R4a)
Touch: evals/prioritize/

## Goal

`evals/prioritize/` holds two scenarios: `01-*` happy-path (a queue
whose Priority headers the run must rewrite per an interview reply) and
`02-adv-*` adversarial — a queue where the correct output changes NO
Priority header, asserted by diffing headers before/after.

## Steps

1. Read `evals/breakdown/01-small-spec/` for the scenario contract and
   `evals/run.sh` for required files; prioritize is interactive
   (AskUserQuestion) — the prompt.txt must carry the reply inline so
   the headless run needs no interview round-trip.
2. Build fixtures in setup.sh; write assert.sh red-first in spirit
   (fails loudly on wrong/absent header changes).

## Acceptance

- [x] `ls -d evals/prioritize/0* | wc -l` → 2, one matching
      `evals/prioritize/02-adv-*` (dir absent today, verified
      2026-07-19)
      <!-- evidence: count=2; 01-reorder-priorities + 02-adv-out-of-scope -->
- [x] `for f in evals/prioritize/*/assert.sh; do bash -n "$f" || exit
1; done` → exit 0
      <!-- evidence: both assert.sh parse (rc=0) -->
- [x] `./evals/run.sh prioritize` passes — human-launched paid headless
      run, 2026-07-20 via `bin/human-followups`: `PASS
    prioritize/01-reorder-priorities`, `PASS
    prioritize/02-adv-out-of-scope`, exit 0.
      <!-- runnability pre-verified: setup.sh provisions the scanner's
              _shared/workboard/runtimes deps (run.sh copies only the skill under
              test), scanner rc=0 on both fixtures; graders red-first (01 fails on
              untouched, passes on P0/P3+commit; 02-adv passes on no-op, fails on a
              P5 edit). -->

## Discovered

- `evals/run.sh` provisions only the single skill dir under test, so any
  evalset whose skill runs a script importing `_shared`/`workboard`/
  `runtimes/` must self-provision those in its `setup.sh` (as this task
  does). A general fix — run.sh provisioning shared deps for all
  scenarios — would remove the per-scenario boilerplate. Stub
  `10-run-sh-shared-dep-provisioning.md`.
- `bash evals/lint-eval-coverage.sh` FAILs with 15 violations across 8
  sibling Tier A skills (breakdown: no adversarial; build/distill/drain/
  evals/gate/idea/onboard: under-bar and/or no adversarial) — the exact
  remaining scope of tasks 03–07 toward task 08's lint-green criterion
  (no stub; dedupes against tasks 03–08).
