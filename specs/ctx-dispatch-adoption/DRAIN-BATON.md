Run-token: 213b64b2b9be6090
Generation: 2
Spec: specs/ctx-dispatch-adoption
Breakdown-failed:
Intake-failed:
Stub-intake-failed:

## Done / next

Generation 1 was a no-argument (whole `specs/` queue) launch. Recorded 5
verdicts this generation, all DONE, all merged and pushed to `main`:

1. ctx-doc-drift-gate/tasks/01-conformance-test.md — docs↔binary
   conformance gate (context-tree). Spec review: skipped (tests-only).
   Lease released — nothing else dispatchable in that spec (02/03
   blocked, 04/05 draft stubs this run discovered).
2. ctx-output-shape-gaps/tasks/01-zero-result-tails.md — zero-result
   diagnostic tails for `ctx refs`/`ctx deps`.
3. ctx-dispatch-adoption/tasks/02-breakdown-structure-gathering.md —
   /breakdown gathers structure via ctx before scouts.
4. ctx-dispatch-adoption/tasks/03-critic-grant-onboard-allowlist.md —
   critic ctx grant + onboard allowlist entry.
5. ctx-dispatch-adoption/tasks/04-agentprof-ctx-telemetry.md — agentprof
   per-session ctx-usage telemetry.

Two scanner-blocking bugs were also fixed and pushed before dispatch
began (see `main` commits `d7e96627`, `db5ca124`): `drain_frontier.py`
rejected `Status: draft`/`obsolete` (both long-established, widely-used
statuses), and one already-`done` task had a malformed `Depends on`
value. Both blocked any whole-tree scan; fixed via TDD (RED test →
GREEN fix), `context-tree`/repo gates green.

**Next:** re-run `python3 .claude/skills/drain/drain_frontier.py
specs/*/` fresh at step 1 — task `ctx-dispatch-adoption/06-plugin-bump-close.md`
was BLOCKED this generation on unmet deps `02, 03`, both now DONE, so it
is very likely dispatchable next. `ctx-output-shape-gaps/tasks/02-tree-files-mode.md`
(P2) was admitted but never dispatched this generation (verdict budget
ran out first) — dispatch it first in this spec (still held).

## Anomalies

- 5 new `Status: draft` discovery stubs were scaffolded this generation
  (ctx-doc-drift-gate/04, /05; ctx-dispatch-adoption/07, /08, /09, /10 —
  six total, not five) from worker `## Discovered` reports. None are
  dispatchable directly; stub intake screens them in a future pass. Task
  10 (`ctx-dispatch-adoption/tasks/10-agentprof-skill-invocations-wrong-field.md`)
  documents a real production correctness bug in agentprof's existing
  `SkillInvocations` skill-attribution path (reads the wrong JSON field,
  silently undercounts) — worth prioritizing at stub-intake time despite
  `Blocking: no`.
- No parked/zombie tasks, no degradation triggers. This generation ended
  on the verdict-budget baton trigger (5 verdicts at W=1) plus a
  session-refresh wake-budget hook firing simultaneously (3 re-primes /
  250k-token context) — both pointed at the same hand-off, so no
  conflict to reconcile.
- `ctx-output-shape-gaps` and `ctx-dispatch-adoption` leases are both
  still held (this same Run-token, Generation now 2 in both
  `DRAIN-OWNER.md` files, updated in this same commit) — the swarm-mode
  spec-lease cap is 3; `ctx-doc-drift-gate`'s lease already released
  (nothing left to dispatch there). A fresh admission pass may claim a
  third spec (e.g. `ctx-cujs`, dispatchable in the last frontier scan but
  not claimed — spec-cap was already at 3 with ctx-doc-drift-gate still
  held at claim time).
