# Task 04: SCHEMA + README docs for reprime and sessions

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: pending
Depends on: 02
Priority: P2
Budget: 4 turns
Spec: ../SPEC.md (requirement R5)
Touch: agentprof/SCHEMA.md, agentprof/README.md

## Goal

SCHEMA.md documents the `reprime` label (definition: main-loop,
non-first-call, cache_write above `--reprime-threshold`; subagent cold
starts never marked) and the two new summary sections, including the
main-loop-only choice for context percentiles. README gains one worked
example: finding your re-primes with
`go tool pprof -tagfocus reprime=true <profile>`.

## Touch

Docs only. Do NOT edit Go code; if the shipped field names differ from
this task's expectations, the docs follow the code (read
internal/costsummary tests for ground truth), never the reverse.

## Steps

1. Read task 01/02 shipped shapes from their tests.
2. Write the SCHEMA.md label + sections entries and the README example.

## Acceptance

- [ ] `grep -qi 'reprime' agentprof/SCHEMA.md && grep -qi 'reprime' agentprof/README.md` → both hit
- [ ] `grep -qi 'tagfocus reprime' agentprof/README.md` → example present
- [ ] `bash agentprof/scripts/check.sh` → green (no code changed)
