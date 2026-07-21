#!/usr/bin/env python3
"""Genuine multi-process race test of admission.py's lease-claim CAS protocol
(specs/drain-multi-spec-swarm R16, task 05).

test_admission.py's `support_git_cas_claim_loser_reports_false` exercises the
same CAS one writer at a time — a sequential simulation. This file instead
launches *real* concurrent OS processes (Python `multiprocessing.Process`,
synchronised on a `Barrier` so they hit the claim window together) racing
against shared fixture git repos, so the interleavings a hand-written
sequential fixture can never produce are actually produced. The hazard is
real, not hypothetical: two independent `/drain` invocations, or a hung
session plus a fresh relaunch, racing against the same `DRAIN-OWNER.md`
files (docs/memory/concurrent-session-collision.md).

Three scenarios, each printing a distinct `scenario: <x> passed` marker on
success so the runnable acceptance check confirms all three ran, not just
that the process exited 0:

  (a) same-spec lease contention — two processes race to claim the SAME
      spec's DRAIN-OWNER.md; exactly one wins, the loser's own return value
      reports the CAS rejection (never both winning).
  (b) cross-spec simultaneous claims — four processes race, one per spec,
      to claim 3 mutually Touch-disjoint specs plus a 4th whose Touch
      footprint overlaps one of them; all 3 disjoint specs admit (R1/R4) and
      the overlapping pair serialises (R5) even under the race.
  (c) stale-lease reclaim race — TWO processes SIMULTANEOUSLY reclaim the
      SAME stale lease (both actively decide "reclaim" and attempt the write,
      not one passive holder against one reclaimer); exactly one reclaim
      commits (reference.md's "ALL STALE" rule).

The shared <=10 global cap is deliberately NOT tested here (R16 round-10
scope: it is single-orchestrator in-memory bookkeeping with no persisted
shared state to race against; task 04's fixture case (e) covers it).

Each scenario has its own wall-clock timeout so a broken CAS that deadlocks
fails fast rather than hanging; the script's exit code is the runnable check
(non-zero on any assertion failure or timeout). Stdlib only.
"""

import multiprocessing as mp
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from queue import Empty

# Make the sibling admission.py importable even when spawned children re-import
# this module by file path from an arbitrary cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from admission import (  # noqa: E402
    claim_decision,
    claim_specs,
    format_owner,
    git_cas_claim,
    owner_liveness,
    parse_owner,
    read_owner,
)

# Retry budget for the shared-branch claim race in scenario (b): concurrent
# pushes to one branch serialise (one winner per push round), so a disjoint
# spec whose push lost to another spec's commit re-syncs and re-attempts. Three
# contenders converge in a few rounds; the ceiling only guards against a
# livelock, and the per-scenario timeout is the real hard stop.
_CLAIM_RETRIES = 40
_SCENARIO_TIMEOUT_S = 60


# --------------------------------------------------------------------------- #
# git fixture helpers — real throwaway repos, matching
# tests/test_drain_owner_protocol.sh's "CAS mechanics against real git repos,
# never mocks" convention.
# --------------------------------------------------------------------------- #
def _git(cwd, *args, env=None, check=True):
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=check,
        capture_output=True,
        text=True,
        env=env,
    )


def _configure_identity(clone):
    _git(clone, "config", "user.email", "racer@example.com")
    _git(clone, "config", "user.name", "Racer")


def _make_bare(root):
    bare = Path(root) / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    return bare


def _clone(bare, dest):
    subprocess.run(["git", "clone", "-q", str(bare), str(dest)], check=True)
    _configure_identity(dest)
    return Path(dest)


def _seed(bare, root, populate, commit_env=None):
    """Clone the bare origin, run `populate(seed_clone)` to lay down fixture
    files, commit them (optionally with `commit_env` to backdate the commit for
    a stale lease), and push so worker clones inherit the state."""
    seed = _clone(bare, Path(root) / "seed")
    populate(seed)
    _git(seed, "add", "-A")
    _git(seed, "commit", "-q", "-m", "seed fixture", env=commit_env)
    _git(seed, "push", "-q", "origin", "HEAD")
    return seed


def _worker_clones(bare, root, n):
    return [_clone(bare, Path(root) / f"w{i}") for i in range(n)]


def _write_task(spec_dir, touch):
    tasks = Path(spec_dir) / "tasks"
    tasks.mkdir(parents=True, exist_ok=True)
    tf = tasks / "01-x.md"
    tf.write_text(f"# 01-x\n\nStatus: pending\nTouch: {touch}\n", encoding="utf-8")
    return tf


# --------------------------------------------------------------------------- #
# process orchestration
# --------------------------------------------------------------------------- #
def _collect(result_q, expected, timeout):
    """Drain `expected` results off the queue within `timeout`. Draining before
    join avoids the classic Queue/join deadlock; payloads here are tiny."""
    results = []
    deadline = time.monotonic() + timeout
    while len(results) < expected:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            results.append(result_q.get(timeout=remaining))
        except Empty:
            break
    return results


def _run_race(target, arglist, timeout):
    """Spawn one process per entry in `arglist`, all handed a shared Barrier so
    they enter the claim window together. Returns (results, timed_out)."""
    result_q = mp.Queue()
    barrier = mp.Barrier(len(arglist))
    procs = [
        mp.Process(target=target, args=(barrier, result_q, *args)) for args in arglist
    ]
    for p in procs:
        p.start()
    results = _collect(result_q, len(arglist), timeout)
    deadline = time.monotonic() + 5
    for p in procs:
        p.join(max(deadline - time.monotonic(), 0))
    timed_out = any(p.is_alive() for p in procs)
    for p in procs:
        if p.is_alive():
            p.terminate()
    return results, timed_out


# --------------------------------------------------------------------------- #
# worker bodies (module-level so they pickle under the spawn start method)
# --------------------------------------------------------------------------- #
def _worker_same_spec(barrier, result_q, clone, slug, token):
    """Scenario (a)/(c) worker: actively race to write+commit+push a claim of
    one spec's DRAIN-OWNER.md via the real git_cas_claim CAS."""
    try:
        spec_dir = Path(clone) / "specs" / slug
        owner = format_owner(token, "host", "2026-07-20T00:00:00Z", 1, str(spec_dir))
        barrier.wait()
        won = git_cas_claim(str(spec_dir), owner, token)
        winner_token = parse_owner(read_owner(str(spec_dir))).get("run_token")
        result_q.put((slug, token, "won" if won else "lost", winner_token))
    except Exception as exc:  # surface, never hang the parent
        result_q.put((slug, token, "error", repr(exc)))


def _worker_reclaim(barrier, result_q, clone, slug, token):
    """Scenario (c) worker: BOTH racers independently re-validate the lease as
    stale (owner_liveness -> ALL_STALE -> claim_decision -> "reclaim") and then
    actively attempt the reclaim write — no passive pre-seeded holder."""
    try:
        spec_dir = Path(clone) / "specs" / slug
        present = read_owner(str(spec_dir)) is not None
        liveness = owner_liveness(str(spec_dir))
        decision = claim_decision(present=present, liveness=liveness)
        if decision != "reclaim":
            result_q.put((slug, token, "not-reclaim", decision))
            return
        owner = format_owner(token, "host", "2026-07-20T00:00:00Z", 2, str(spec_dir))
        barrier.wait()
        won = git_cas_claim(str(spec_dir), owner, token)
        winner_token = parse_owner(read_owner(str(spec_dir))).get("run_token")
        result_q.put((slug, token, "won" if won else "lost", winner_token))
    except Exception as exc:
        result_q.put((slug, token, "error", repr(exc)))


def _worker_cross_spec(barrier, result_q, clone, my_slug, token, cand_meta, cap):
    """Scenario (b) worker: one process per spec. Each independently runs the
    real claim_specs Touch-disjoint selector over the full candidate set to
    decide whether ITS spec is admissible (R5 serialisation), then races to
    claim its own lease on the shared branch, re-syncing and retrying when its
    push loses to another spec's concurrent commit."""
    try:
        candidates = [
            {
                "spec": str(Path(clone) / "specs" / slug),
                "task_files": [str(Path(clone) / "specs" / slug / "tasks" / "01-x.md")],
            }
            for slug, _touch in cand_meta
        ]
        claimed = {c["spec"] for c in claim_specs(candidates, cap=cap)}
        my_spec = str(Path(clone) / "specs" / my_slug)
        barrier.wait()
        if my_spec not in claimed:
            # R5: an overlapping higher-order spec occupies the footprint; this
            # spec is refused and never contends for a lease.
            result_q.put((my_slug, token, "refused", None))
            return
        owner = format_owner(token, "host", "2026-07-20T00:00:00Z", 1, my_spec)
        for _ in range(_CLAIM_RETRIES):
            if git_cas_claim(my_spec, owner, token):
                result_q.put((my_slug, token, "claimed", token))
                return
            # push lost to a peer's commit; git_cas_claim already reset us to the
            # winner's tip, so re-attempt on top of it.
        result_q.put((my_slug, token, "retry-exhausted", None))
    except Exception as exc:
        result_q.put((my_slug, token, "error", repr(exc)))


# --------------------------------------------------------------------------- #
# scenarios
# --------------------------------------------------------------------------- #
def scenario_a():
    """Two processes race to claim the SAME spec's lease; exactly one wins."""
    with tempfile.TemporaryDirectory() as root:
        bare = _make_bare(root)

        def populate(seed):
            spec_dir = Path(seed) / "specs" / "alpha"
            spec_dir.mkdir(parents=True)
            (spec_dir / "SPEC.md").write_text("# alpha\n", encoding="utf-8")

        _seed(bare, root, populate)
        c1, c2 = _worker_clones(bare, root, 2)
        arglist = [(str(c1), "alpha", "tok-a1"), (str(c2), "alpha", "tok-a2")]
        results, timed_out = _run_race(_worker_same_spec, arglist, _SCENARIO_TIMEOUT_S)
        assert not timed_out, "scenario (a) deadlocked / timed out"
        assert len(results) == 2, f"scenario (a): expected 2 results, got {results}"
        assert all(r[2] != "error" for r in results), f"worker error: {results}"
        wins = [r for r in results if r[2] == "won"]
        losses = [r for r in results if r[2] == "lost"]
        assert len(wins) == 1, f"scenario (a): not exactly one winner: {results}"
        assert len(losses) == 1, f"scenario (a): loser missing/extra: {results}"
        winner_token = wins[0][1]
        # The loser's own return reports the CAS rejection AND it sees the
        # winner's committed token, never its own (no double-win).
        assert losses[0][3] == winner_token, (
            f"scenario (a): loser did not observe the winner's committed claim: {results}"
        )
        # HEAD at the origin carries exactly the winner's token.
        head = _git(bare, "show", "HEAD:specs/alpha/DRAIN-OWNER.md").stdout
        assert parse_owner(head).get("run_token") == winner_token, head
    print("scenario: a passed")


def scenario_b():
    """Four processes race, one per spec: 3 disjoint specs admit, the 4th
    (Touch-overlapping) serialises out (R5), even under the concurrent race."""
    cand_meta = [
        ("alpha", "src/alpha/mod.py"),
        ("beta", "src/beta/"),
        ("gamma", "docs/gamma.md"),
        ("delta", "src/alpha/"),  # overlaps alpha's footprint -> R5 excludes it
    ]
    # cap=4 (> the 4 candidates) so delta's exclusion is caused by the Touch
    # overlap (R5), never by the spec-claim cap — the cap is out of scope here.
    cap = 4

    def populate(seed):
        for slug, touch in cand_meta:
            _write_task(Path(seed) / "specs" / slug, touch)

    with tempfile.TemporaryDirectory() as root:
        bare = _make_bare(root)
        _seed(bare, root, populate)
        clones = _worker_clones(bare, root, len(cand_meta))
        arglist = [
            (str(clones[i]), slug, f"tok-{slug}", cand_meta, cap)
            for i, (slug, _touch) in enumerate(cand_meta)
        ]
        results, timed_out = _run_race(_worker_cross_spec, arglist, _SCENARIO_TIMEOUT_S)
        assert not timed_out, "scenario (b) deadlocked / timed out"
        assert len(results) == 4, f"scenario (b): expected 4 results, got {results}"
        assert all(r[2] != "error" for r in results), f"worker error: {results}"
        outcome = {r[0]: r[2] for r in results}
        assert outcome.get("alpha") == "claimed", outcome
        assert outcome.get("beta") == "claimed", outcome
        assert outcome.get("gamma") == "claimed", outcome
        assert outcome.get("delta") == "refused", outcome
        # The committed end-state matches: the 3 disjoint leases present at
        # origin HEAD, the overlapping one absent (R5 held under the race).
        tree = _git(bare, "ls-tree", "-r", "--name-only", "HEAD").stdout.split()
        owners = {p for p in tree if p.endswith("DRAIN-OWNER.md")}
        assert owners == {
            "specs/alpha/DRAIN-OWNER.md",
            "specs/beta/DRAIN-OWNER.md",
            "specs/gamma/DRAIN-OWNER.md",
        }, owners
        # No lost update: each committed lease carries its own claimant's token.
        for slug in ("alpha", "beta", "gamma"):
            body = _git(bare, "show", f"HEAD:specs/{slug}/DRAIN-OWNER.md").stdout
            assert parse_owner(body).get("run_token") == f"tok-{slug}", (slug, body)
    print("scenario: b passed")


def scenario_c():
    """Two processes SIMULTANEOUSLY reclaim the SAME stale lease; exactly one
    reclaim commits. Both actively re-validate staleness and attempt the write
    — neither is a passive pre-seeded holder (round-10 respecification)."""
    stale_token = "tok-stale-foreign"
    # Backdate the seed commit so owner_liveness reads the spec dir's last
    # commit as older than the 15-min grace window -> ALL_STALE in every clone.
    old = "2020-01-01T00:00:00 +0000"
    commit_env = dict(os.environ, GIT_AUTHOR_DATE=old, GIT_COMMITTER_DATE=old)

    def populate(seed):
        spec_dir = Path(seed) / "specs" / "alpha"
        spec_dir.mkdir(parents=True)
        (spec_dir / "DRAIN-OWNER.md").write_text(
            format_owner(stale_token, "old-host", old, 1, "specs/alpha"),
            encoding="utf-8",
        )

    with tempfile.TemporaryDirectory() as root:
        bare = _make_bare(root)
        _seed(bare, root, populate, commit_env=commit_env)
        c1, c2 = _worker_clones(bare, root, 2)
        arglist = [(str(c1), "alpha", "tok-r1"), (str(c2), "alpha", "tok-r2")]
        results, timed_out = _run_race(_worker_reclaim, arglist, _SCENARIO_TIMEOUT_S)
        assert not timed_out, "scenario (c) deadlocked / timed out"
        assert len(results) == 2, f"scenario (c): expected 2 results, got {results}"
        assert all(r[2] != "error" for r in results), f"worker error: {results}"
        # Both racers independently decided to reclaim (neither saw it as FRESH,
        # neither was a passive holder): both reached a won/lost write outcome.
        assert all(r[2] in ("won", "lost") for r in results), (
            f"scenario (c): a worker did not attempt the reclaim write: {results}"
        )
        wins = [r for r in results if r[2] == "won"]
        losses = [r for r in results if r[2] == "lost"]
        assert len(wins) == 1, (
            f"scenario (c): not exactly one reclaim committed: {results}"
        )
        assert len(losses) == 1, f"scenario (c): loser missing/extra: {results}"
        winner_token = wins[0][1]
        assert winner_token != stale_token, "a racer, not the stale holder, must win"
        assert losses[0][3] == winner_token, (
            f"scenario (c): loser did not observe the winner's reclaim: {results}"
        )
        head = _git(bare, "show", "HEAD:specs/alpha/DRAIN-OWNER.md").stdout
        assert parse_owner(head).get("run_token") == winner_token, head
    print("scenario: c passed")


def main():
    for scenario in (scenario_a, scenario_b, scenario_c):
        try:
            scenario()
        except AssertionError as exc:
            print(f"FAIL: {scenario.__name__}: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:  # unexpected fixture/runtime failure
            print(f"ERROR: {scenario.__name__}: {exc!r}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
