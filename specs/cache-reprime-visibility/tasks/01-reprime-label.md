# Task 01: reprime=true label on main-loop cache-write spikes

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: none
Priority: P0
Budget: 8 turns
Spec: ../SPEC.md (requirement R1)
Touch: agentprof/internal/claude/, agentprof/cmd_claude.go, agentprof/testdata/

## Goal

`agentprof claude` attaches label `reprime=true` to main-loop model-call
samples (stack has no `agent:` frame) that are not the main loop's first
model call in their transcript and whose `cache_write_tokens` exceeds the
threshold (default 50,000; flag `--reprime-threshold`, 0 disables).
Subagent samples and the main loop's first call are never marked.

## Touch

Parser and flag only. Do NOT touch `internal/costsummary/` (task 02),
`agent-console/` (task 03), or SCHEMA.md/README.md (task 04). Emission
order caveat from SPEC.md applies: main-loop samples emit first in
transcript order, then per-subagent blocks (claude.go:311-342) — track
"first main-loop model call" per transcript, never per session label.

## Steps

1. Write the failing test first: fixture transcript where (a) the main
   loop's first model call writes >50k cache tokens → no label; (b) a
   later main-loop call writes >50k → `reprime=true`; (c) a subagent's
   first call writes >50k under the same session label → no label;
   (d) a later main-loop call writes <50k → no label.
2. Implement the label in the main-loop emission path in
   `internal/claude/claude.go`.
3. Add `--reprime-threshold` to `cmd_claude.go` (default 50000; 0
   disables), plumbed to the parser.
4. Verify pprof label filtering works end-to-end on the fixture
   (labels already become pprof string labels via internal/pprofenc).

## Acceptance

- [ ] `cd agentprof && go test ./internal/claude/` → pass, including the
  four-case fixture above (mid-session main-loop >50k gets `reprime=true`;
  main-loop first call, subagent first call, and sub-threshold calls do
  not)
- [ ] `cd agentprof && go run . claude --help 2>&1 | grep -q reprime-threshold` → flag documented
- [ ] `bash agentprof/scripts/check.sh` → green
