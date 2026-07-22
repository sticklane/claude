# Task 09: unify the drain loop onto agentic run (draft)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 08
Priority: P3
Budget: 24 turns
Spec: ../SPEC.md (statement 8's "any unification comes later" — this is the later)
Touch: agentic/loop.py, scripts/workflows/drain.sh, tests/

## Goal

The seam the design deliberately left open, recorded so it is owned
rather than forgotten: reimplement `agentic loop` (core task 08's
bespoke loop) as a saved workflow under `scripts/workflows/drain.sh`
executed by `agentic run`, so the queue drainer gains journaling,
prefix-replay resume, `runs`/`stop` control, and the watch view for
free, and the toolkit has exactly one execution substrate. Promote
this draft only after both the core loop and `agentic run` have real
mileage — unifying two working things beats unifying one working
thing with one hope.

## Steps

1. Port loop.py's iteration onto run + dispatch; keep the loop verb
   as a thin alias so nothing calling `agentic loop` breaks.
2. All core loop tests pass unchanged against the workflow-backed
   implementation; the R-C race tests re-run green.
3. Delete the bespoke iteration code once parity holds.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_loop.py -q` → passes unchanged against the workflow-backed loop
- [ ] `bash tests/test_agentic_generic.sh && bash tests/test_agentic_write_lock.sh && bash tests/test_agentic_clone_race.sh` → all green post-unification
- [ ] `agentic runs` → shows a completed drain run for the fixture queue (the loop is now observable like any run)
- [ ] `bash scripts/check.sh` → green
