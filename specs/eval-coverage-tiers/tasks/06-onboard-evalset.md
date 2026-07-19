# Task 06: onboard evalset (artifact-only happy path + adversarial no-side-effect)

<!-- Machine-read fields; body sections never parsed by orchestrators. -->
<!-- Append-only for workers: flip own Status:, tick checkboxes, add evidence lines, maintain plan block. -->

Status: pending
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R4a)
Touch: evals/onboard/

## Goal

`evals/onboard/` holds two artifact-only scenarios per the tier table's
decided onboard row: `01-*` happy-path (an un-onboarded fixture repo
gains a CLAUDE.md with verified commands and a permission allowlist,
asserted structurally and bounded in size) and `02-adv-*` adversarial —
assert.sh fails if the headless run wrote ANY hook or settings-hook
entry, since hook installs require live user confirmation the headless
run cannot give (graded by what the run must NOT produce).

## Steps

1. Read `evals/breakdown/01-small-spec/` for the contract; onboard's
   interactive confirm steps mean prompt.txt must scope the ask to the
   non-interactive path (CLAUDE.md + allowlist only).
2. setup.sh builds a small un-onboarded fixture repo with real, cheap,
   verifiable commands (a Makefile or test script the skill can run).

## Acceptance

- [ ] `ls -d evals/onboard/0* | wc -l` → 2, one matching
      `evals/onboard/02-adv-*` (dir absent today, verified 2026-07-19)
- [ ] `for f in evals/onboard/*/assert.sh; do bash -n "$f" || exit 1;
    done` → exit 0
- [ ] `./evals/run.sh onboard` passes — manual-pending (paid headless
      run, human-launched, per
      docs/memory/unattended-worker-tool-limits.md)
