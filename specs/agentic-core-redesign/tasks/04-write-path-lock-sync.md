# Task 04: claim, verdict, write lock, git sync rules

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 02
Priority: P0
Budget: 30 turns
Spec: ../SPEC.md (statements 4, 5; D8, D9; R-C; D7 verdict schema)
Touch: agentic/claim.py, agentic/verdict.py, agentic/lock.py, agentic/sync.py, agentic/schema/verdict.json, tests/test_agentic_verdict.py, tests/test_agentic_write_lock.sh, tests/test_agentic_clone_race.sh

## Goal

The write path exists and is safe under the concurrency the design
actually has. `agentic claim <id>` claims atomically via bd.
`agentic verdict <id> --file <path>` validates a worker's JSON against
`agentic/schema/verdict.json` (JSON Schema: DONE/BLOCKED/DEFERRED, typed
Unblock, Discovered list), updates the task, and files discovered work
with `discovered-from` edges. Every write command takes the D8
repo-level lock (with stale-lock timeout-and-takeover) and follows the
D9 sync rules: pull → import changed JSONL → apply → export → commit →
push, re-applying once on push rejection; the generated JSONL is never
hand-merged.

## Touch

This task proves the spec's riskiest assumption. It does not build the
loop (task 08) or compose (task 07). Batching granularity (one
export-commit per loop iteration) is exposed as a flag the loop will
use; the default for single commands is one commit per command.

## Steps

1. Write failing tests first: `tests/test_agentic_verdict.py` (schema
   acceptance and rejection cases; discovered filing with edge type;
   BLOCKED requires typed Unblock), then the two race scripts.
2. Implement lock.py (flock file + stale takeover), sync.py (the D9
   sequence against a bare fixture remote), claim.py, verdict.py.
3. `tests/test_agentic_write_lock.sh`: run two `agentic verdict`
   commands concurrently in one checkout; assert both recorded in bd AND
   the final committed JSONL contains both (no lost export). Then plant
   a STALE lock (dead PID, old mtime) and assert a write command takes
   it over after the timeout — D8's stale-lock recovery is a tested
   behavior, not a promise.
4. `tests/test_agentic_clone_race.sh`: two clones of one bare remote
   write near-simultaneously; assert both operations land after retries,
   or the loser exits nonzero with "already claimed" — and the remote's
   committed JSONL contains every surviving operation.

## Acceptance

- [x] `python3 -m pytest tests/test_agentic_verdict.py -q` → passes
- [x] `bash tests/test_agentic_write_lock.sh` → prints `LOCK OK` (both verdicts recorded, zero lost exports) and `STALE TAKEOVER OK` (planted dead-PID lock taken over after timeout) (R-C a, D8)
- [x] `bash tests/test_agentic_clone_race.sh` → prints `RACE OK` (both land or clean semantic failure; remote JSONL complete) (R-C b)
- [x] `bash scripts/check.sh` → green

<!-- Evidence (this run):
  - pytest tests/test_agentic_verdict.py -q -> 14 passed (schema accept/reject,
    typed-Unblock-required-for-BLOCKED, discovered-from filing, DONE closes,
    committed-JSONL reflects close, idempotent re-file on D9 re-apply).
  - tests/test_agentic_write_lock.sh -> LOCK OK + STALE TAKEOVER OK.
  - tests/test_agentic_clone_race.sh -> RACE OK (distinct tasks both land after
    push retry; same-task contention leaves exactly one winner, loser exits
    nonzero with bd's "already claimed"; remote JSONL complete). Stable x3.
  - scripts/check.sh -> green (only quarantined test_skill_chain_determinism.sh
    FAILs, owned by another spec).
  Integration note: wiring the claim/verdict verbs required replacing task 02's
  stubs in agentic/cli.py and adding bd wrappers (bd_claim/bd_set_status/
  bd_metadata/bd_set_metadata/bd_create, bd_import --allow-stale) to
  agentic/bd.py — neither file is in this task's Touch header, but the stubs
  exit 2 so the acceptance commands cannot pass without the wiring, and
  SPEC S2/D3 requires all bd shell-outs stay inside agentic.bd. Sequential
  dispatch (sole writer) makes the out-of-Touch edits collision-free. -->

