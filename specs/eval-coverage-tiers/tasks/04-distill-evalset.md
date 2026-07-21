# Task 04: distill evalset (happy path + adversarial noise-rejection)

<!-- Machine-read fields; body sections never parsed by orchestrators. -->
<!-- Append-only for workers: flip own Status:, tick checkboxes, add evidence lines, maintain plan block. -->

Status: in-progress
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R4a)
Touch: evals/distill/

## Goal

`evals/distill/` holds two scenarios: `01-*` happy-path (a session
transcript containing a genuine correction lands as a durable
CLAUDE.md/rules entry) and `02-adv-*` adversarial — the transcript
contains one instruction that belongs in a rule AND one-off noise that
must NOT be captured; assert.sh fails if the noise phrase appears in
any written doctrine file.

## Steps

1. Read `evals/breakdown/01-small-spec/` for the contract; distill
   reads session context, so setup.sh must plant the transcript
   fixture where the scenario's prompt directs the skill to read it
   (an explicit fixture file the prompt names — not a real harness
   transcript).
2. assert.sh checks capture of the durable item (structure-level grep)
   and absence of the seeded noise phrase in every touched doctrine
   file.

## Acceptance

- [ ] `ls -d evals/distill/0* | wc -l` → 2, one matching
      `evals/distill/02-adv-*` (dir absent today, verified 2026-07-19)
- [ ] `for f in evals/distill/*/assert.sh; do bash -n "$f" || exit 1;
    done` → exit 0
- [ ] `./evals/run.sh distill` passes — manual-pending (paid headless
      run, human-launched, per
      docs/memory/unattended-worker-tool-limits.md)
