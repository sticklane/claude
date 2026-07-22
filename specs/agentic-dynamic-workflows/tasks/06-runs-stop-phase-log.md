# Task 06: operator control — runs, stop, phase, log

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 03
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (statements 6, 11; RW-O)
Touch: agentic/runsctl.py, tests/test_agentic_run_stop.sh

## Goal

`agentic runs` lists running and recent runs (id, script, state,
spend, started). `agentic stop <run-id>` signals a running run to
halt after in-flight dispatches settle — the journal ends clean
(every started event has a result), the stopped state is visible in
`runs`, and a later re-run resumes by prefix replay losing nothing
journaled. `agentic phase <title>` and `agentic log <msg>` append
schema-valid progress events for host scripts to narrate with.

## Touch

Wires in exclusively through task 03's extension points (ledger
hook / tracker callbacks / stop-signal check); this task never edits
run.py or dispatch.py — that is what keeps Group: 04, 05, 06
Touch-disjoint and safe to run concurrently.

## Steps

1. Write `tests/test_agentic_run_stop.sh` failing first: start a
   fixture run with slow stub workers; stop it mid-run; assert
   in-flight dispatches settle, the journal has no dangling started
   events, `agentic runs` shows `stopped`, and a resume replays the
   completed prefix (cached count equals settled dispatches).
2. Implement runsctl.py (run registry from the run dirs; stop via a
   signal file the run loop checks between dispatches) and the
   phase/log event appenders (events validate against task 01's
   schema).

## Acceptance

- [ ] `bash tests/test_agentic_run_stop.sh` → prints `STOP OK` and `RESUME OK` (RW-O)
- [ ] `bash scripts/check.sh` → green
