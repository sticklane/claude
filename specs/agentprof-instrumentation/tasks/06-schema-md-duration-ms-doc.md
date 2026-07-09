# Task 06: Document duration_ms in agentprof/SCHEMA.md's well-known metrics table

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Depends on: none
Priority: P3
Budget: 2 turns
Spec: ../SPEC.md
Discovered-from: 01-tool-and-model-durations.md
Touch: agentprof/SCHEMA.md, agentprof/README.md

## Goal

`agentprof/SCHEMA.md`'s "Well-known metrics" table documents
`duration_ms` → milliseconds (mirroring the `wall_ms` row), matching what
`unitFor` already maps in `agentprof/internal/pprofenc/pprofenc.go:21`;
`agentprof/README.md`'s unit list gets the same row (it has the same
omission).

## Steps

1. Add the `duration_ms` → milliseconds row to SCHEMA.md's table.
2. Update README.md's unit documentation to match.

## Acceptance

- [x] `grep -n 'duration_ms' agentprof/SCHEMA.md | grep -q 'millisecond'` → match (verifier PASS; evidence/06-schema-md-duration-ms-doc.md)
- [x] `grep -n 'duration_ms' agentprof/README.md | grep -q 'millisecond'` → match (verifier PASS; evidence/06-schema-md-duration-ms-doc.md)
- [x] `cd agentprof && bash scripts/check.sh` → exit 0 (format-check/lint/tests ok; evidence/06-schema-md-duration-ms-doc.md)
