# Task 02: prioritize evalset (happy path + adversarial)

<!-- Machine-read fields; body sections never parsed by orchestrators. -->
<!-- Append-only for workers: flip own Status:, tick checkboxes, add evidence lines, maintain plan block. -->

Status: in-progress
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

- [ ] `ls -d evals/prioritize/0* | wc -l` → 2, one matching
      `evals/prioritize/02-adv-*` (dir absent today, verified
      2026-07-19)
- [ ] `for f in evals/prioritize/*/assert.sh; do bash -n "$f" || exit
  1; done` → exit 0
- [ ] `./evals/run.sh prioritize` passes — manual-pending (paid
      headless run, human-launched, per
      docs/memory/unattended-worker-tool-limits.md)
