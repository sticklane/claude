# Task 05: the tracker bridge — run issues, actuals, provenance

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: blocked
Unblock: run: grep -q '^Status: done' specs/agentic-core-redesign/tasks/04-write-path-lock-sync.md || echo "core task 04 (write path, lock, sync) not done"
Depends on: 03
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (statement 7; DW7; RW-D)
Touch: agentic/runtracker.py, tests/test_agentic_run_tracker.py

## Goal

Every run files a tracker issue at start (script hash, pool) through
the core write path (lock + sync, primary checkout), checkpoints
actuals per phase, writes final actuals at completion, and files kept
findings as issues linked `discovered-from` the run issue. The
journal stays the hot-path meter; the tracker holds the durable
summary that rides the committed JSONL export.

## Touch

Blocked on core task 04 because every tracker write here goes through
its lock and sync rules — no parallel write path. Nothing auto-flips
this task: re-run the Unblock check and flip Status once core 04 is
done.

## Steps

1. Write `tests/test_agentic_run_tracker.py` failing first: a fixture
   run files its run issue; final actuals land in metadata; a kept
   finding lands `discovered-from` the run issue; invoking
   `agentic run` from a git worktree exits with the typed refusal
   before any dispatch launches (statement 7's guard re-asserted at
   the bridge layer).
2. Implement runtracker.py over the core write path; checkpoint
   cadence is per phase, never per dispatch (write latency stays out
   of the hot path).

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_run_tracker.py -q` → passes (RW-D incl. the checkout-guard case)
- [ ] `bash scripts/check.sh` → green
