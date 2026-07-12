# Task 07: wire --keep-pending CLI flag + pending parse-stat line

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Promotion-ready: true
Promoted-by-run: attended-2026-07-11-sjaconette
Discovered-from: specs/agentprof-attribution-gaps/tasks/03-pending-consolidation.md
Depends on: none
Priority: P3
Budget: 4 turns
Spec: ../SPEC.md
Touch: agentprof/cmd_claude.go, agentprof/cmd_claude_test.go, agentprof/README.md

## Goal

`agentprof claude` exposes task 03's library-level `Options.KeepPending`
as a `--keep-pending` CLI flag (default false), and prints the pending
parse-stat to stderr on real runs ("N unmatched tool call(s)
consolidated" or the library's equivalent wording). README's Commands
table gains the flag. Root-level `cmd_claude_test.go` fixture-count
assertions may need updating if the flag changes output shape
(docs/memory/touch-root-fixture-tests.md — hence its place in Touch).

## Original report

> Task 03 implemented library-level `Options.KeepPending` + `Stats.Pending`
> but could not wire the `--keep-pending` CLI flag or the stderr parse-stat
> line because cmd_claude.go is outside task 03's Touch. Add the ~4-line
> `fs.Bool("keep-pending")` wiring in cmdClaude and surface the pending
> parse-stat on real CLI runs.

## Acceptance

- [ ] `cd agentprof && go run . claude --help 2>&1 | grep -q keep-pending` → hit
- [ ] `cd agentprof && go test ./...` → pass (incl. root cmd tests)
- [ ] `grep -qi 'keep-pending' agentprof/README.md` → hit
- [ ] `bash agentprof/scripts/check.sh` → green
