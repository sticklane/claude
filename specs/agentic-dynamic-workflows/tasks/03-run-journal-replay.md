# Task 03: agentic run — durable execution and prefix replay

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 02
Priority: P1
Budget: 30 turns
Spec: ../SPEC.md (statements 2, 3, 7 guard; DW1, DW3, DW6; RW-J)
Touch: agentic/run.py, tests/test_agentic_run_replay.sh, tests/fixtures/workflows/

## Goal

`agentic run <script>` assigns a run ID, executes the host-language
script with the journal active, and on re-run replays the unchanged
PREFIX of dispatches from cache — only the first changed call and
everything after it runs live (the observed ultracode semantics,
DW3). Invoked from a non-primary checkout (a git worktree), it exits
with the typed refusal before any dispatch launches. The run dir
carries journal.jsonl + progress.jsonl (gitignored derived state).
run.py ships its extension points as part of THIS task, so tasks
04/05/06 wire in from their own modules without ever editing run.py:
a per-dispatch ledger charge hook, run-start/checkpoint/finish
callbacks, and a stop-signal check between dispatches — each a no-op
until its consumer task registers it.

## Touch

Fixture workflows are stub-worker bash scripts committed under
tests/fixtures/workflows/. The determinism note (no timestamps or
randomness in prompts, or replay is forfeited) goes in run.py's
--help text and the example workflow's header comment, not in a rules
file.

## Steps

1. Write `tests/test_agentic_run_replay.sh` failing first: run a
   5-dispatch fixture; re-run unchanged → journal shows 5 cached, 0
   live; edit dispatch 3's prompt in the fixture; re-run → exactly 2
   cached, 3 live. Also: run from a `git worktree add` checkout →
   typed refusal, no dispatch launched, exit nonzero.
2. Implement run.py: run-id assignment, journal ownership, prefix
   validity (a changed content-hash invalidates all later positions),
   primary-checkout guard, and the three extension points (ledger
   hook, tracker callbacks, stop-signal check) with stub-callback
   tests proving each fires at the right moment.
3. Progress events for run start/end phases validate against task
   01's schema.

## Acceptance

- [ ] `bash tests/test_agentic_run_replay.sh` → prints `REPLAY OK` (5/0, then 2/3 — prefix semantics) and `GUARD OK` (worktree refusal) (RW-J + statement 7 guard)
- [ ] `python3 -m pytest tests/ -q -k run_hooks` → passes (stub callbacks prove the ledger hook fires per dispatch, tracker callbacks at start/checkpoint/finish, and the stop check between dispatches)
- [ ] `bash scripts/check.sh` → green
