Status: draft
Discovered-from: specs/agentprof-attribution-gaps/tasks/03-pending-consolidation.md
Spec: ../SPEC.md
Blocking: no

# Task 07: wire --keep-pending CLI flag + parse-stat in cmd_claude.go

Task 03 implemented library-level `Options.KeepPending` + `Stats.Pending` but
could not wire the `--keep-pending` CLI flag or the stderr parse-stat line
("N unmatched tool call(s) consolidated…") because cmd_claude.go is outside
task 03's Touch. Add the ~4-line `fs.Bool("keep-pending")` wiring in cmdClaude
and surface the pending parse-stat on real CLI runs.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
