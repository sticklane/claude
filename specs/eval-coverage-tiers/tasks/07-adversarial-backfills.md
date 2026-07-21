# Task 07: Adversarial backfill scenarios for the existing evalsets

<!-- Machine-read fields; body sections never parsed by orchestrators. -->
<!-- Append-only for workers: flip own Status:, tick checkboxes, add evidence lines, maintain plan block. -->

Status: done
Depends on: none
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (requirement R4b)
Touch: evals/breakdown/, evals/build/, evals/drain/, evals/evals/, evals/critique/

## Goal

Each existing Tier A evalset meets the ≥2-scenarios-with-adversarial
bar: new `NN-adv-*` scenario dirs in evals/breakdown, evals/build,
evals/drain, and evals/evals (each a scenario whose correct outcome is
to refuse, flag, or not act — e.g. breakdown refusing a spec with
unresolved Open questions; build stopping on a task whose acceptance
command is red and unfixable in budget; drain skipping a queue whose
only task is blocked; evals refusing to scaffold over an existing
evalset). For evals/critique: create
`evals/critique/02-adv-gameable-criterion/` per criterion-depth-ladder
R6's content contract IFF the directory does not already exist at
execution time; if it exists, verify it matches `NN-adv-*` and record
that as evidence.

## Touch

NEW `NN-adv-*` scenario dirs only — never modify any existing scenario
file (including evals/drain/01-rolling-window/assert.sh, which
specs/drain-frontier-scanner task 03 owns). Run the critique
conditional LAST to minimize the cross-spec race window.

## Steps

1. Read each evalset's existing scenario for its fixture conventions.
2. Author each adversarial scenario red-first in spirit: assert.sh
   fails loudly when the skill DOES act on input it must refuse.
3. Critique conditional last, per the Goal's existence check.

## Acceptance

- [x] `for s in breakdown build drain evals critique; do ls -d
evals/$s/*-adv-* >/dev/null 2>&1 || { echo "missing: $s"; exit
1; }; done` → exit 0 (no `*-adv-*` dir exists anywhere under
      evals/ today, verified 2026-07-19)
  - Evidence: ran the loop → exit 0. New dirs: breakdown/03-adv-open-questions,
    build/02-adv-red-acceptance, drain/02-adv-blocked-queue,
    evals/02-adv-existing-evalset; critique/02-adv-gameable-criterion
    pre-existed and matches `NN-adv-*` (verify-only per Goal).
- [x] `for f in evals/*/*-adv-*/assert.sh; do bash -n "$f" || exit 1;
done` → exit 0
  - Evidence: ran the loop over all `*-adv-*/assert.sh` → exit 0 (all valid bash).
- [x] `git diff --stat <base>..HEAD -- evals/ | grep -v 'adv-'` shows
      no modified pre-existing scenario files (evidence-record the
      command output)
  - Evidence: base=2fd603c; `git diff --stat 2fd603c..HEAD -- evals/ | grep -v 'adv-'`
    output = only the summary line ` 16 files changed, 353 insertions(+)`; every
    changed path contains `adv-`, so no pre-existing scenario file was modified.
- [ ] `./evals/run.sh breakdown build drain evals critique` passes —
      manual-pending (paid headless runs, human-launched, per
      docs/memory/unattended-worker-tool-limits.md)
  - Manual-pending: unattended worker cannot launch paid headless model
    sessions. Graders were instead validated non-vacuous offline (each
    `assert.sh` green on the correct refused state, red on every wrong-action
    mutation); a human runs `./evals/run.sh` post-merge to close this.
