# Task 04: agent_id label on subagent samples

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: 03
Priority: P2
Budget: 4 turns
Spec: ../SPEC.md (requirement R5)
Touch: agentprof/internal/claude/, agentprof/testdata/, agentprof/SCHEMA.md

## Goal

Every sample parsed from an agent sidecar transcript carries label
`agent_id=<sidecar id>` (the id already known at parse time and currently
discarded). Existing labels unchanged. SCHEMA.md documents the label and
its use (`-tagfocus agent_id=…`, fan-out width, true per-instance
parallelism).

## Touch

Same file as tasks 01–03 — runs after them (serial chain tail). SCHEMA.md
is shared with task 06's README-adjacent docs — keep to the agent_id
entry.

## Steps

1. Failing test first: two same-typed agents in one turn get distinct
   `agent_id` labels; main-loop samples carry none.
2. Implement in the subagent emission block (claude.go:~329-342).
3. Document in SCHEMA.md.

## Acceptance

- [ ] `cd agentprof && go test ./internal/claude/` → pass including the
  distinct-ids fixture
- [ ] `grep -qi 'agent_id' agentprof/SCHEMA.md` → hits
- [ ] `bash agentprof/scripts/check.sh` → green
