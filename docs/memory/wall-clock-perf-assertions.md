# Wall-clock perf assertions in a blocking check

Read this when a test in `scripts/check.sh` asserts a wall-clock ceiling, or
when a check that passes alone starts failing whenever anything else runs on
the host.

## The incident (2026-07-25, bd issue agentic-7pq)

`tests/test_agentic_latency.sh` asserted that the median of five `agentic
ready` runs over a 600-issue tracker stayed under **1 second**. That ceiling
was calibrated on a quiet host and left roughly 30% headroom, which is no
headroom at all for a wall-clock measurement: the same machine's ordinary
background activity swings the number by 6x.

Because `scripts/check.sh` runs every `tests/test_*.sh`, the single flaky
assertion exited the whole suite 1 for **every** change in the repo. Any task
whose acceptance criteria included a green root `check.sh` was blocked; two
batch-1 drain tasks (agentic-k2s, agentic-8os) merged under a documented
exception instead of a green gate.

## Measurements

All figures are the test's own median of five `agentic ready` runs at 600
seeded issues, on the same 10-core host.

| Condition | Load avg | Median |
| --- | --- | --- |
| Quiet host | 2.8 | 0.721s |
| Independent verifier, quiet host (three runs) | — | 0.723s / 0.944s / 1.003s |
| 10 synthetic busy-loop processes | 7.3 | 0.961s |
| 30 synthetic busy-loop processes | 8.7 | **1.375s — failed the 1s ceiling** |
| Ordinary background activity (a Go e2e suite, ffmpeg, Chrome) | 35 | 2.488s |
| Same, heavier | 63 | 4.364s |
| 30 synthetic processes on top of that background | 48 | 5.667s |
| Peak background load seen during this investigation | 92 | 7.615s |
| Four concurrent drain workers (field reports) | — | 2.058s / 3.946s / 4.875s / 5.522s |

## The decision

Not a bd regression, and not merely a stale ceiling. Re-baselining alone
could not fix it: the measurement's spread is 6x, so no fixed ceiling both
catches a real regression and survives an arbitrarily loaded host.
`scripts/check.sh` already runs the test in its `SERIAL` list, which controls
contention *within* one check run and does nothing about other processes on
the machine — which is where the load actually came from.

So the wall-clock ceiling was demoted from the assertion to a backstop, and
the invariant it was proxying for is now asserted directly.

- **Primary, deterministic:** count the `bd` process invocations `agentic
  ready` makes at 600 issues and require a small constant (measured: exactly
  1, a single `bd export`; bound: 5). Every tracker call in the toolkit goes
  through `agentic/bd.py`'s `shutil.which("bd")`, so a recording shim named
  `bd` placed first on `PATH` sees all of them. This is what "guards against a
  regression to per-issue bd calls" actually means, and it is load-invariant.
- **Secondary, wall clock:** the ceiling moved 1s → 60s, about 8x the worst
  loaded median measured here (7.615s at load 92) and comfortably inside
  `check.sh`'s 600s per-test timeout even in the worst case. It is a
  catastrophe backstop, not a performance budget — read it as "something is
  badly broken", never as an SLO for `agentic ready`. The measured spread
  tracks host oversubscription roughly linearly, so the margin is sized for a
  host several times busier than any yet observed. The guard itself now lives
  in the call count.

Quarantining the test (the `QUARANTINE` list's route, as used for
`tests/test_eval_coverage_lint.sh`) was the other candidate. It was rejected
because it would have kept the suite green by deleting the guard rather than
fixing it, and the guard's real invariant turned out to be cheap to assert
exactly.

## The general rule

A wall-clock assertion in a blocking check is a proxy. Before writing one,
ask what it is a proxy *for* — a call count, an allocation count, a query
count — and assert that instead; those are deterministic and survive a busy
host. If a wall-clock number must stay, give it headroom over the *loaded*
case, never the idle one, and never let it be the only thing standing between
the repo and a green gate.
