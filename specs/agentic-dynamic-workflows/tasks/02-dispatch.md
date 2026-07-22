# Task 02: agentic dispatch — the single-agent primitive

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: blocked
Unblock: run: grep -q '^Status: done' specs/agentic-core-redesign/tasks/07-composer.md || echo "core task 07 (composer, meter, screen) not done"
Depends on: 01
Priority: P0
Budget: 30 turns
Spec: ../SPEC.md (statements 1, 5; DW2, DW8, DW9, DW11; RW-P, RW-T)
Touch: agentic/dispatch.py, tests/test_agentic_dispatch.py

## Goal

`agentic dispatch` works end to end: prompt (or compose envelope) +
result JSON Schema + `--tier` + optional `--worktree` in; a validated
JSON result file out. Invalid returns re-prompt ≤2 times then fail
typed, journaled. Tier aliases resolve through the runtime profile
(unknown tier or bare profile → session default with a warning). Every
dispatch charges the meter (core task 07's module), passes
tracker-sourced text through the screen, emits progress events
conforming to task 01's schema — and never touches the tracker.

## Touch

Blocked on core task 07 because dispatch reuses the composer's meter
and screen modules rather than growing rivals. Nothing auto-flips this
task: a human or later session re-runs the Unblock check and flips
Status once core 07 is done.

## Steps

1. Write `tests/test_agentic_dispatch.py` failing first: schema pass;
   schema fail → 2 re-prompts → typed failure recorded in the
   journal; tier resolution per fixture profile incl. unknown-tier
   warning; emitted events validate against
   `agentic/schema/progress-event.json`; screen refusal on a
   screen-stub fixture string.
2. Implement dispatch.py over the meter/screen modules and a
   `--worker <command>` abstraction (stub workers in tests).
3. Wire the journal write path (started/result events, versioned
   content-hash keys) as a shared module task 03 will reuse.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_dispatch.py -q` → passes (RW-P, RW-T; covers screen refusal and event-schema conformance)
- [ ] `bash scripts/check.sh` → green
