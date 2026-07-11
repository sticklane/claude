# Task 03: workboard cost panel re-prime line

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: 02
Priority: P2
Budget: 6 turns
Spec: ../SPEC.md (requirement R4)
Touch: agent-console/

## Goal

The agent-console workboard cost panel shows one re-prime line (count +
cost for the window) sourced from the `reprime` section of the summary
JSON it already reads via the refresh path specs/workboard-weekly-cost-view
shipped. When the summary carries no `reprime` section (older cache), the
panel renders exactly as today — no error, no placeholder.

## Touch

agent-console only (`_read_cost_summary` / `render_workboard` path,
agent-console.py). No new endpoint. Do NOT touch agentprof/ — task 02
fixed the field names this task consumes; read them from the shipped
summary JSON shape.

## Steps

1. Failing test first: unit/render test with a summary fixture carrying
   `reprime` → line present with count and $; fixture without → absent.
2. Implement in the cost panel renderer.
3. Run the console's check script.

## Acceptance

- [ ] `bash agent-console/scripts/check.sh` → green (py_compile, render
  smoke test, unit tests) including the new fixture pair (reprime section
  present → line rendered; absent → gracefully omitted)
