# Task 04: the budget ledger and structural caps

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 03
Priority: P1
Budget: 24 turns
Spec: ../SPEC.md (statement 4; DW4, DW5, DW8, DW11; RW-B, RW-C, RW-N)
Touch: agentic/ledger.py, tests/test_agentic_run_budget.py, tests/test_agentic_run_caps.sh, tests/test_agentic_dispatch_silent.sh

## Goal

One hierarchical ledger: every dispatch charges the run's pool (hard
typed refusal at the cap) and, when task-scoped, that task's
budget_tokens. Structural caps enforced from the profile: dispatch
depth (AGENTIC_RUN_DEPTH, max 2), per-run concurrency (default 10,
queueing above it), per-run agent lifetime (default 200). ctx queries
leave the meter unchanged. Dispatch's tracker-silence — the
load-bearing concurrency invariant — is proven on the store, and the
write lock exposes an attempt counter so the proof is not vacuous.

## Steps

1. Write failing tests first: `tests/test_agentic_run_budget.py`
   (pool sized for 2 of 3 → third refused typed; task-scoped refusal
   on exhausted budget_tokens; an `agentic ctx` query between
   dispatches leaves the meter reading unchanged);
   `tests/test_agentic_run_caps.sh` (depth-3 refused; with
   controlled-sleep stub workers, above-cap dispatches show journal
   queuedAt strictly before startedAt; agent-cap crossing refuses);
   `tests/test_agentic_dispatch_silent.sh` (export tracker, 8
   concurrent dispatches, re-export → empty diff AND lock attempt
   counter reads zero).
2. Implement ledger.py and the cap enforcement in dispatch/run;
   expose the lock attempt counter.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_run_budget.py -q` → passes (RW-B incl. ctx-unmetered)
- [ ] `bash tests/test_agentic_run_caps.sh` → prints `CAPS OK` (RW-C, queuedAt/startedAt mechanism)
- [ ] `bash tests/test_agentic_dispatch_silent.sh` → prints `SILENT OK` (empty export diff, zero lock attempts) (RW-N)
- [ ] `bash scripts/check.sh` → green
