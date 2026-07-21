# Task 07: Adversarial backfill scenarios for the existing evalsets

<!-- Machine-read fields; body sections never parsed by orchestrators. -->
<!-- Append-only for workers: flip own Status:, tick checkboxes, add evidence lines, maintain plan block. -->

Status: in-progress
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

- [ ] `for s in breakdown build drain evals critique; do ls -d
  evals/$s/*-adv-* >/dev/null 2>&1 || { echo "missing: $s"; exit
  1; }; done` → exit 0 (no `*-adv-*` dir exists anywhere under
      evals/ today, verified 2026-07-19)
- [ ] `for f in evals/*/*-adv-*/assert.sh; do bash -n "$f" || exit 1;
  done` → exit 0
- [ ] `git diff --stat <base>..HEAD -- evals/ | grep -v 'adv-'` shows
      no modified pre-existing scenario files (evidence-record the
      command output)
- [ ] `./evals/run.sh breakdown build drain evals critique` passes —
      manual-pending (paid headless runs, human-launched, per
      docs/memory/unattended-worker-tool-limits.md)
