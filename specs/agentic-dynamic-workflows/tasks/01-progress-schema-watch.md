# Task 01: progress-event schema and the watch renderer

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P1
Budget: 24 turns
Spec: ../SPEC.md (statement 6; DW10; RW-V)
Touch: agentic/watch.py, agentic/schema/progress-event.json, tests/test_agentic_watch.sh, tests/fixtures/progress/

## Goal

The canonical progress-event schema exists (`agentic/schema/
progress-event.json`, JSON Schema for the two event types — phase and
agent — with the field set recorded in EVIDENCE.md: label, phase
index/title, tier, state, queuedAt/startedAt, attempt, last event,
tokens, durationMs, result preview), and `agentic watch <stream-file>`
renders a stream of those events as the terminal tree: phase boxes,
one row per agent. Later emitter tasks (02, 03) validate their events
against this schema — the renderer is authored first precisely so the
schema is fixed by its consumer, not improvised by each emitter.

## Touch

No dependency on any other agentic verb: watch reads a file. The
fixture stream is committed with frozen timestamps and a pinned
stream-end clock; elapsed is always computed against the stream-end
clock, never the wall clock.

## Steps

1. Write `tests/test_agentic_watch.sh` failing first: render the
   committed fixture stream under `COLUMNS=100 NO_COLOR=1`; diff
   against the committed golden output; assert empty. Include a
   malformed-event fixture → typed warning line, exit 0 (rendering
   is best-effort, never crashes the run it observes).
2. Author `agentic/schema/progress-event.json` from the spec's field
   set; validate the fixture stream against it in the test.
3. Implement watch.py: one-shot render mode (used by the test) and
   follow mode (tail + re-render).

## Acceptance

- [ ] `python3 -m pytest tests/ -q -k progress_schema 2>/dev/null || python3 -c "import json,jsonschema" 2>/dev/null; bash -c 'for f in tests/fixtures/progress/*.jsonl; do python3 -m agentic.validate_events "$f" || exit 1; done; echo EVENTS VALID'` → `EVENTS VALID` (fixture streams conform to the committed schema)
- [ ] `bash tests/test_agentic_watch.sh` → prints `WATCH GOLDEN OK` (COLUMNS=100, NO_COLOR=1, frozen fixture, empty diff) (RW-V)
- [ ] `bash scripts/check.sh` → green
