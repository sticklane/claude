Status: draft
Intake-refused: gate — assessor's OBSOLETE verdict cited only that task 19's undeclared manifest edit merged harmlessly under this run's W=1 (no Touch enforcement at W=1), not that task 15's own Touch defect is closed; task 15 is still blocked and would hit real R4 Touch enforcement on a future W>1 re-dispatch/merge (2026-07-13)
Discovered-from: specs/mirror-procedure-discipline/tasks/15-normalize-next-stage-lines.md
Spec: ../SPEC.md
Blocking: no

# Task 15's Touch omits the manifest data file its own acceptance criteria requires editing

Task 15's `Touch:` names `tests/test_mirror_procedure_coverage.sh` but its
acceptance criterion 4 ("≥3 new manifest lines") requires editing
`tests/mirror-procedure-manifest.txt` (the data the script reads, not the
script itself) — a strict merge-time Touch whitelist would reject that
edit. Once task 15 unblocks and is re-dispatched, its Touch (or the
merge-time whitelist) should include `tests/mirror-procedure-manifest.txt`.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
