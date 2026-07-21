# Task 03: idea evalset (happy path + adversarial gameable-criterion)

<!-- Machine-read fields; body sections never parsed by orchestrators. -->
<!-- Append-only for workers: flip own Status:, tick checkboxes, add evidence lines, maintain plan block. -->

Status: in-progress
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R4a)
Touch: evals/idea/

## Goal

`evals/idea/` holds two scenarios: `01-*` happy-path (a pitch produces
specs/<slug>/SPEC.md with the template sections and runnable criteria)
and `02-adv-*` adversarial — a pitch whose OBVIOUS criterion is a
doctrine-word grep; assert.sh fails if the written SPEC.md contains an
unanchored grep criterion (no "verified <date>" note) or a
self-referential doctrine-word grep with no depth-ceiling annotation.
This is the behavioral complement criterion-depth-ladder's task 02
names.

## Steps

1. Read `evals/breakdown/01-small-spec/` for the contract; /idea is
   interactive — prompt.txt must pre-answer the interview inline.
2. setup.sh builds a minimal target repo; assert.sh parses the produced
   SPEC.md's Acceptance section (structure, not exact wording — assert
   the anchoring/ceiling markers, never incidental prose).

## Acceptance

- [ ] `ls -d evals/idea/0* | wc -l` → 2, one matching
      `evals/idea/02-adv-*` (dir absent today, verified 2026-07-19)
- [ ] `for f in evals/idea/*/assert.sh; do bash -n "$f" || exit 1;
  done` → exit 0
- [ ] `./evals/run.sh idea` passes — manual-pending (paid headless run,
      human-launched, per docs/memory/unattended-worker-tool-limits.md)
