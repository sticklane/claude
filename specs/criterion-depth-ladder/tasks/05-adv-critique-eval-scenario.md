# Task 05: Adversarial critique eval scenario (seeded gameable criterion)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. -->

Status: in-progress
Depends on: none
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirement R6)
Touch: evals/critique/02-adv-gameable-criterion/

## Goal

A committed scenario `evals/critique/02-adv-gameable-criterion/` whose
fixture spec carries one grep criterion that is anchored (phrase absent
from the fixture) yet trivially satisfiable by its own requirement's
literal. Its assert.sh asserts both halves: the critique run does NOT
set `Breakdown-ready: true`, AND the persisted `critique-findings.md`
identifies the seeded criterion. The `NN-adv-*` name is load-bearing —
specs/eval-coverage-tiers' lint keys on it; do not rename.

## Steps

1. Read `evals/critique/01-clean-spec/` for the scenario contract
   (setup.sh fixture build, prompt.txt, assert.sh, allowed-tools.txt —
   critique dispatches the critic agent, so the scenario needs the
   Agent/Task tool allowed per that evalset's convention).
2. Write setup.sh building a minimal fixture repo whose SPEC.md has one
   anchored-but-gameable criterion (a doctrine-word grep its own
   requirement would type).
3. Write assert.sh red-first in spirit: it must fail loudly on a
   `Breakdown-ready: true` header, on missing critique-findings.md, or
   on findings that never name the seeded criterion.
4. Do NOT edit any existing scenario; `./evals/run.sh critique` is
   paid/human-launched — mark that half manual-pending, never attempt it.

## Acceptance

- [ ] `bash -n evals/critique/02-adv-gameable-criterion/assert.sh &&
  grep -q 'Breakdown-ready'
  evals/critique/02-adv-gameable-criterion/assert.sh && grep -q
  'critique-findings'
  evals/critique/02-adv-gameable-criterion/assert.sh && grep -Eq
  'exit 1|fail' evals/critique/02-adv-gameable-criterion/assert.sh`
      → exit 0 — committed-scenario SHAPE check, honestly L1 per the
      spec.
- [ ] `test -f evals/critique/02-adv-gameable-criterion/setup.sh &&
  test -f evals/critique/02-adv-gameable-criterion/prompt.txt` →
      exit 0
- [ ] `./evals/run.sh critique` passes — manual-pending (paid headless
      run, human-launched; a drained worker cannot launch it, per
      docs/memory/unattended-worker-tool-limits.md). This run is R6's
      behavioral half.
