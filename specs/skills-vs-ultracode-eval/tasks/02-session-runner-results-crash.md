# Task 02: Stub session runner — results row, cost summing, crash-as-fail, toy fixtures

Status: done
Depends on: 01
Priority: P1
Budget: 28 turns
Rigor: prototype
Spec: ../SPEC.md (design statements 6, 9; controls; acceptance criteria 3, 6, 7)
Touch: evals/headtohead/run.sh, evals/headtohead/tasks/fixture/, evals/headtohead/tasks/crashfixture/, evals/headtohead/lib/

## Goal

`run.sh --task <t> --arm <A> --seeds <n>` runs a session against a bundled
STUB-driven fixture (no real paid CLI session — mirror the existing
`evals/stub-cli.sh` pattern) and emits one results row per run that validates
against `result.schema.json`. Cost and tokens are summed across the root session
AND every spawned child session, so a fixture whose stub work spawns a child
yields a `tokens` total that EXCEEDS the root transcript's own total. A crashed
or capped run records a schema-valid row with `pass: false` and non-null partial
`usd`/`tokens` — crashed runs are recorded, never dropped. Two toy tasks are
authored: `fixture` (stub work that spawns a child session) and `crashfixture`
(stub session dies mid-run / hits the cap).

## Touch

Owns the session-run path in `run.sh`, plus the `fixture` and `crashfixture`
task directories (toy setup + brief + stub transcript generator + a trivial
`assert.sh`/reference so the row can be scored). Do NOT touch the dry-run/config
core (task 01 owns its structure), the judge path (task 03), or the three real
fixtures (04-06). Use a stub CLI so the run needs no API key and no network.

## Steps

1. Add the stub CLI harness (reuse/extend `evals/stub-cli.sh` conventions) that
   emits deterministic fake root + child transcripts with token/usd/turn counts.
2. Author `tasks/fixture/`: a toy snapshot + ≤6-sentence brief + stub work that
   spawns ONE child session; a trivial `assert.sh` + reference so `pass` resolves.
3. Author `tasks/crashfixture/`: stub session that exits mid-run / trips the cap,
   still emitting partial usd/tokens before dying.
4. Implement the run path: for each seed, run the stub session, sum cost/tokens
   across root + children, count spawns, measure wall-clock and turns, run the
   out-of-mount `assert.sh` to set `pass`, and append the row (schema-validated).
5. Implement crash handling: a non-zero/capped session still writes a row with
   `pass: false` and the partial cost captured.
6. Mechanical acceptance run (prototype rigor) — confirm the commands below.

## Acceptance

- [x] `bash evals/headtohead/run.sh --task fixture --arm S --seeds 1` → emits one results row that validates against `evals/headtohead/result.schema.json` (validation asserted by the run or a bundled validator invoked in the same command); exits 0
- [x] `bash evals/headtohead/run.sh --task fixture --arm S --seeds 1` then inspecting the emitted row → `usd`, `tokens`, `turns`, `wall_s` are all non-null AND `tokens` exceeds the root transcript's own total (child-session cost is summed)
- [x] `bash evals/headtohead/run.sh --task crashfixture --arm U --seeds 1` → emits a schema-valid row with `pass: false` and non-null partial `usd` and `tokens`
