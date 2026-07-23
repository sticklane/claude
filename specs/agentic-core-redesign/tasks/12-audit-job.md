# Task 12: the audit job — measure use, file regressions as tasks

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 09
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (statement 14; component "The audit job"; Migration step 7)
Touch: agentic/audit.py, tests/test_agentic_audit.py

## Goal

`agentic audit [--since <date>]` reads session transcripts (the
agentprof transcript locations) and tracker data, measures: structure
lookups that bypassed `agentic ctx` for grep, dispatches that bypassed
compose, verdict-schema failures, and spend vs caps — and files each
regression class as a tracker task with a `discovered-from` edge to a
standing audit anchor issue. Scheduling wiring (cron/Routine) is a
one-line doc note; the command itself is the deliverable, runnable by
hand or by any scheduler.

## Touch

Read-only over transcripts; writes only tracker tasks through the
standard write path (lock + sync). No new hook directories.

## Steps

1. Write `tests/test_agentic_audit.py` failing first: fixture transcript
   files exhibiting one grep-bypass and one compose-bypass → audit files
   exactly two tasks, correctly typed, linked discovered-from; a second
   run files nothing new (dedup against open audit tasks).
2. Implement audit.py on top of agentprof's transcript-reading helpers
   where importable, else a minimal reader.
3. Add the scheduling one-liner to README's agentic section.

## Acceptance

- [x] `python3 -m pytest tests/test_agentic_audit.py -q` → passes (covers dedup on re-run) — 8 passed (test_second_run_files_nothing_new covers dedup)
- [x] `agentic audit --since 2026-07-01 --dry-run | head -20` → runs against this machine's real transcripts and prints its measures without writing (record output as evidence) — grep-bypass: 14497, compose-bypass: 6509, verdict-schema-failure: 1, spend-over-cap: 0; no tasks filed
- [x] `bash scripts/check.sh` → green — 40 agentic pytest + all tests/test_*.sh green, exit 0
