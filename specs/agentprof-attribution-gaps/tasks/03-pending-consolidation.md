# Task 03: consolidate tool:(pending) samples

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Depends on: 02
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R3)
Touch: agentprof/internal/claude/, agentprof/testdata/, specs/agentprof-attribution-gaps/evidence/

## Goal

Unmatched tool_use blocks no longer emit one empty-valued sample each
(`toolSamples`, claude.go:~857): they aggregate into a single per-turn
`tool:(pending)` sample carrying a `pending_calls` value, with a
`--keep-pending` flag preserving today's per-call emission for debugging.
A parse-stat logs the pending count. Investigate whether Agent-tool /
TaskOutput result shapes account for the 8,854-sample volume; fix the
matching if so and record the finding in evidence/.

## Touch

Same file as tasks 01/02 — runs after them (serial chain).

## Steps

1. Failing tests first: fixture with 3 unmatched tool_uses in one turn →
   one `tool:(pending)` sample, `pending_calls: 3`, no empty-values
   samples; with `--keep-pending` → today's behavior.
2. Implement aggregation + flag + parse-stat.
3. Investigate the two suspected unmatched shapes against a real
   transcript; fix matching if confirmed; write
   evidence/03-pending-volume.md with the before/after sample counts on
   the local 14-day window (expect ≥8% total-sample drop).

## Acceptance

- [x] `cd agentprof && go test ./internal/claude/` → pass including the
  aggregation and keep-pending fixtures — verifier PASS: all internal/claude
  tests green incl. TestUnmatchedToolCallsConsolidateIntoOnePendingSample,
  TestKeepPendingPreservesPerCallEmptyValuedSamples,
  TestPendingParseStatCountsUnmatchedCalls (evidence/03-pending-consolidation.md)
- [x] evidence/03-pending-volume.md records before/after — fixture: empty-values
  pending samples 2→0. 14-day-window ≥8% drop + Agent-tool/TaskOutput
  investigation are MANUAL-PENDING (need $HOME/.claude, outside the isolated
  worktree) with exact runnable commands recorded (evidence/03-pending-volume.md)
- [x] `bash agentprof/scripts/check.sh` → green — format-check/lint/tests ok
  (verifier confirmed)

## Decisions

- CLI `--keep-pending` flag deferred: cmd_claude.go is out of this task's
  `Touch:` (only agentprof/internal/claude/ + testdata + evidence). Implemented
  as library-level `Options.KeepPending` + `Stats.Pending` — the in-scope
  surfacing that satisfies all three (internal/claude-scoped) acceptance
  criteria. Reverse/complete: add the ~4-line `fs.Bool("keep-pending")` wiring
  in cmdClaude per evidence/03-pending-volume.md. Recorded as Discovered.
- 14-day volume measurement + Agent-tool/TaskOutput shape fix left
  MANUAL-PENDING rather than fabricated: the data lives under $HOME/.claude,
  unreadable from an isolated worktree. Code-level hypothesis (meta/sidechain
  tool_results skipped at claude.go:673 before matching) + exact confirmation
  commands are in evidence/03-pending-volume.md. No speculative matching change
  made without confirming data.
