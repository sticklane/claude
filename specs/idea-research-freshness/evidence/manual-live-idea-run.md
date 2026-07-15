# Manual-pending: live `/idea` run against the freshness fixtures

This spec's mechanical checks (tasks 01–03) confirm the freshness checker,
the `/idea` grounding-check step, and its antigravity mirror in isolation.
One criterion cannot be verified unattended: an actual `/idea` invocation
observing the grounding-check behavior end to end. An unattended worker
cannot run `/idea` — CLAUDE.md's execution-stage launch-authorization
contract requires a live user request naming the stage — so it is recorded
here for a human or attended session to tick after running `/idea` live.

## How to run

In an attended session, invoke `/idea` against each scenario fixture under
`.claude/skills/idea/test-fixtures/research-freshness/` and confirm the
observed behavior matches the mechanical checks:

- `fresh/` — the grounding-check step finds a `Verified:` stamp inside the
  90-day window, so `/idea` dispatches **no** research agent and cites the
  existing doc location.
- `stale/` — the stamp is older than 90 days, so `/idea` dispatches research
  and writes back a refreshed `Verified:` stamp.
- `no-stamp/` — no `Verified:` stamp present, so `/idea` dispatches research
  and writes back a fresh `Verified:` stamp.
- paraphrase — a paraphrase-only rewording of the `fresh/` idea that carries
  the same grounding intent but uses **no** listed trigger phrase; the
  grounding-check step still fires (trigger patterns are illustrative, not
  exhaustive) and behaves as the `fresh/` case does.

## Scenarios (tick after the live run confirms each)

- [ ] `fresh/`: `/idea` dispatches no research agent and cites the existing location.
- [ ] `stale/`: `/idea` dispatches research and writes back a refreshed stamp.
- [ ] `no-stamp/`: `/idea` dispatches research and writes back a refreshed stamp.
- [ ] paraphrase (fresh intent, no listed trigger phrase): grounding check still fires and behaves as `fresh/`.
