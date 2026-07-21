# Task 03: Trajectory assertion — the drain eval proves the scanner ran

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. -->

Status: in-progress
Depends on: none
Priority: P2
Budget: 6 turns
Spec: ../SPEC.md (requirement R4)
Touch: evals/drain/01-rolling-window/assert.sh

## Goal

The drain evalset's assert greps `$EVAL_TRANSCRIPT` for a
`drain_frontier.py` invocation (the EVAL_TRANSCRIPT mechanism per
specs/trajectory-evals), guarding first that the variable is non-empty
and failing loudly when the transcript is unavailable — never silently
passing. Existing artifact assertions in the file are untouched.

## Steps

1. Read `evals/drain/01-rolling-window/assert.sh` and the
   trajectory-assertion pattern in
   `evals/breakdown/02-scout-delegation/assert.sh`.
2. Append the guarded transcript grep; do not modify existing checks.

## Acceptance

- [ ] `grep -rl 'drain_frontier' evals/drain/ | grep -q assert.sh` →
      exit 0, and `bash -n evals/drain/01-rolling-window/assert.sh` →
      exit 0 (committed half)
- [ ] `./evals/run.sh drain` passes — manual-pending (paid headless
      run, human-launched, per
      docs/memory/unattended-worker-tool-limits.md); this run is R4's
      behavioral half.
