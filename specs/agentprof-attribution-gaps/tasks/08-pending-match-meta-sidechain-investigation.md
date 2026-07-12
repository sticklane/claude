# Task 08: fix pending-volume from meta/sidechain tool_result skip

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Promotion-ready: true
Promoted-by-run: attended-2026-07-11-sjaconette
Discovered-from: specs/agentprof-attribution-gaps/tasks/03-pending-consolidation.md
Depends on: 07
Priority: P3
Budget: 6 turns
Spec: ../SPEC.md
Touch: agentprof/internal/claude/, agentprof/testdata/, agentprof/cmd_claude_test.go, specs/agentprof-attribution-gaps/evidence/

## Goal

The result-matching skip at claude.go:~673 (tool_result blocks on
IsMeta/IsSidechain user lines dropped BEFORE populating toolResultIDs) is
reproduced with a HERMETIC testdata fixture — a transcript where a
tool_use's result arrives on a meta or sidechain line — proving those
calls currently land as pending; the matching is fixed so such results
match, with the fixture asserting the pending count drops accordingly.
No home-directory access needed: the fixture encodes the hypothesized
shape, so the task is fully runnable in an isolated worktree. The
real-window before/after measurement stays a MANUAL-PENDING evidence
line (command recorded, run by the orchestrator or a human post-merge —
the manual-pending escape, docs/memory/unattended-worker-tool-limits.md).

## Original report

> claude.go:673 result-matching skips tool_result blocks on
> IsMeta/IsSidechain user lines before populating toolResultIDs —
> suspected mechanical source of the ~8,854 pending-sample volume
> (Agent-tool / TaskOutput result shapes). Confirm against real ~/.claude
> transcripts (needs $HOME data, outside an isolated worktree) and fix
> the matching if confirmed; record before/after counts in evidence/.

## Acceptance

- [x] `cd agentprof && go test ./internal/claude/` → pass, including a NEW
  fixture where a tool_result on a meta/sidechain line matches its
  tool_use (pending count asserted lower after the fix; pre-fix behavior
  demonstrated by the test's construction)
  — PASS: new `meta_sidechain_match_test.go` (`TestToolResultOnMetaOrSidechainLineMatchesToolUse`,
  isMeta+isSidechain subtests) asserts `Stats.Pending==0` and zero pending
  samples; verifier confirmed RED→GREEN by swapping in base claude.go (both
  subtests fail Pending=1 pre-fix). See evidence/08-pending-match.md.
- [x] evidence/08-pending-match.md records the fix + the exact real-window
  measurement command as MANUAL-PENDING (or its result if run attended)
  — PASS: evidence/08-pending-match.md documents the matching-order fix and the
  `go run . claude --claude-dir "$HOME/.claude"` before/after command (MANUAL-PENDING,
  needs real ~/.claude data absent from the worktree).
- [x] `cd agentprof && go test ./...` → pass; `bash agentprof/scripts/check.sh` → green
  — PASS: all 14 packages `ok`; check.sh → format-check ok, lint ok, tests ok.
