# Task 03: Antigravity autopilot stale parallel-workflow reference

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: pending
Depends on: none
Priority: P2
Budget: 4 turns
Spec: ../SPEC.md (F2)
Touch: antigravity/.agents/workflows/autopilot.md

## Goal

`antigravity/.agents/workflows/autopilot.md` no longer points at the
deleted parallel workflow; its worker-launch line references the build
workflow directly, matching the Claude-side autopilot wording.

## Steps

1. Find the line citing "the build prompt from the parallel workflow" in
   `antigravity/.agents/workflows/autopilot.md`.
2. Reword to reference the build workflow (`.agents/workflows/build.md`)
   directly.
3. Check the file for any other `parallel workflow` mentions and fix them
   the same way.

## Acceptance

- [ ] `! grep -qi 'parallel workflow' antigravity/.agents/workflows/autopilot.md` → exit 0
