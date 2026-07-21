# Task 05: Real-concurrency test for admission.py's lease-claim CAS

Status: in-progress
Depends on: 04
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirement R16)
Touch: .claude/skills/drain/test_admission_concurrency.py

## Goal

This is the "real test" of the multi-spec swarm's lease-claim concurrency
safety, without requiring a live `/drain` run or a human present. Task 04's
`admission.py` implements the `DRAIN-OWNER.md` git-CAS lease-claim protocol
as callable Python; this task exercises it with **real OS-level concurrency**
— actual concurrent processes (Python's `multiprocessing`, not sequential
calls dressed up as fixture cases) racing against shared fixture git repos.
It proves the CAS protocol holds under genuine race conditions, which a
deterministic single-threaded fixture walk cannot: two racing processes can
interleave their git reads/writes in ways a hand-written sequential fixture
never exercises. The hazard this guards against is real, not hypothetical —
`docs/memory/concurrent-session-collision.md` documents exactly this class
of incident (two independent `/drain` invocations, or a hung session plus a
fresh relaunch, racing against the same queue state).

**Round-10 scope correction:** this task covers THREE lease-claim race
scenarios, not four. The global ≤10 worker cap is explicitly NOT tested
here — critique found that bound is single-orchestrator in-memory
bookkeeping with no persisted shared state to race against (Out of scope
forbids inventing one), so there is nothing for two processes to race over;
it stays covered by task 04's own deterministic fixture case (e). Racing it
here would either be vacuous or force `admission.py` to invent the
persisted counter this spec explicitly rejects.

No `/drain` invocation, no execution-stage skill, no human — this task is
fully orchestrator-resolvable per CLAUDE.md's authoring conventions on
unattended-worker tool limits.

## Touch

Only `.claude/skills/drain/test_admission_concurrency.py`. Do not touch
`.claude/skills/drain/admission.py` itself (task 04's scope, already
merged by the time this task starts) or `drain_frontier.py` (owned by
`specs/drain-frontier-scanner`).

## Steps

1. Read task 04's landed `admission.py` interface in full — this task
   exercises that real code, it does not re-derive the algorithm
   independently.
2. Set up shared fixture git repos (throwaway temp repos per test case,
   matching `tests/test_drain_owner_protocol.sh`'s existing convention of
   exercising CAS mechanics against real git repos rather than mocks) that
   multiple `multiprocessing.Process` workers will race against.
3. **Scenario (a) — same-spec lease contention.** Spawn two real concurrent
   processes both calling `admission.py`'s lease-claim function against the
   SAME fixture spec's `DRAIN-OWNER.md`. Assert exactly one process's claim
   is committed; the loser's own return value reports a CAS rejection
   (matching reference.md's "FRESH → refuse unless baton lineage" rule) —
   never both processes reporting success.
4. **Scenario (b) — cross-spec simultaneous claims.** Spawn processes racing
   to claim 3 mutually Touch-disjoint fixture specs plus a 4th overlapping
   one, all launched concurrently (not sequentially). Assert all 3 disjoint
   specs admit (R1/R4) and the colliding pair still serializes (R5) even
   though the claim attempts raced rather than running one after another.
5. **Scenario (c) — stale-lease reclaim race (round-10 respecification).**
   Spawn TWO processes SIMULTANEOUSLY racing to reclaim the SAME stale
   fixture lease (a fixture with an old `Started:` timestamp and no live
   worktree — both processes see it as reclaimable and race to commit the
   reclaim). This is a genuine race precisely because both sides are
   actively attempting the same write, unlike a passive pre-seeded holder
   that never re-validates and races against nothing. Assert exactly one
   reclaim commits (matching reference.md's "ALL STALE" reclaim rule); the
   loser detects the winner's committed reclaim via the same re-read-at-HEAD
   CAS check as scenario (a).
6. Make each scenario print a distinct marker line on success (e.g.
   `scenario: a passed`) so the runnable acceptance check can confirm all
   three ran and passed, not just that the script exited 0.
7. Confirm the script's own exit code is the runnable check (non-zero on
   any assertion failure, including a hung/deadlocked race — use a timeout
   per scenario so a broken CAS implementation fails fast rather than
   hanging the test).

## Acceptance

- [x] `test -f .claude/skills/drain/test_admission_concurrency.py` → file
      exists (absent today, verified 2026-07-19)
      Evidence: file created; `test -f` → OK.
- [x] `python3 .claude/skills/drain/test_admission_concurrency.py` → exits 0
      Evidence: exit 0 on 10/10 consecutive runs (flakiness loop, races stable).
- [x] `python3 .claude/skills/drain/test_admission_concurrency.py | grep -co '^scenario: [a-c] passed'`
      → 3 (the file does not exist today, so this cannot pass vacuously)
      Evidence: 3 markers (`scenario: a/b/c passed`) on 10/10 runs.
- [x] Each scenario spawns genuinely concurrent processes — a code-review
      check (not grep-anchorable): the implementation must use
      `multiprocessing.Process`/`Pool` (or equivalent real-OS-concurrency
      primitive) to launch the racing workers, not a `for` loop calling
      functions sequentially and asserting on the results as if they'd
      raced. A verifier reads the implementation to confirm this — grep
      for `import multiprocessing` as a necessary-but-not-sufficient signal
      (`grep -c "import multiprocessing" .claude/skills/drain/test_admission_concurrency.py`
      → ≥ 1), with the verifier's own read confirming it's actually used to
      launch concurrent racers in each of the three scenarios, not just
      imported and unused.
      Evidence: `import multiprocessing` grep → 1; all three scenarios route
      through `_run_race`, which builds `mp.Process` per racer and starts
      them, each worker `barrier.wait()`-synced (`mp.Barrier`) into the CAS
      window. Independent verifier confirmed genuine per-scenario concurrency
      (PASS, line-grounded).
- [x] Scenario (c)'s implementation specifically confirms via code review
      that BOTH racing processes actively attempt the reclaim write (not one
      passive pre-seeded holder plus one reclaimer) — the round-10
      respecification's whole point, otherwise this scenario silently
      regresses to the finding critique raised.
      Evidence: stale lease seeded in fixture SETUP (backdated seed commit,
      GIT_COMMITTER_DATE=2020); both spawned `_worker_reclaim` processes
      independently `read_owner`→`owner_liveness`(ALL_STALE)→`claim_decision`
      (reclaim) then `git_cas_claim`; assertion `all(r in {won,lost})` fails
      if either failed to attempt the write. Verifier confirmed PASS.
