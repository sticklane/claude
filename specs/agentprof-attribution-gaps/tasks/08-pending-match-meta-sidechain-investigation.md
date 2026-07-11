Status: draft
Discovered-from: specs/agentprof-attribution-gaps/tasks/03-pending-consolidation.md
Spec: ../SPEC.md
Blocking: no

# Task 08: investigate pending-volume from meta/sidechain tool_result skip

claude.go:673 result-matching skips tool_result blocks on IsMeta/IsSidechain
user lines before populating toolResultIDs — suspected mechanical source of
the ~8,854 pending-sample volume (Agent-tool / TaskOutput result shapes).
Confirm against real ~/.claude transcripts (needs $HOME data, outside an
isolated worktree) and fix the matching if confirmed; record before/after
counts in evidence/.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
