Run-token: c11f6ca343ed7836
Generation: 2
Spec: specs/drain-worker-dispatch-hardening

## Done / next

Generation 1 (attended, 2026-07-16) drained specs/rigor-tier to completion
this run:

- rigor-tier: 4/4 tasks done (02 build/drain Rigor gate-scaling P0, 01
  /idea+/breakdown Rigor header P1, 03 /list-specs tier display +
  quality-discipline scoping P2, 04 closing version bump 0.9.14→0.9.15
  P3), spec review clean (0 findings), lease released. All merges clean
  or trivially resolved (Status-line in-progress/done conflicts only),
  all project gates green each time (specs/status.sh, claude plugin
  validate, tests/test_*.sh, bin/check-agent-model-pins,
  evals/lint-ultra-gate.sh, evals/lint-skill-size-gate.sh).

Next (in priority/dependency order, per the original plan):

1. specs/drain-worker-dispatch-hardening — task 03 (P2, dep 02 done) →
   task 05 (P1, gates 01-04, becomes dispatchable once 03 lands).
2. specs/context-blowout-subagent-guards — task 01 (P2, no deps).
3. Exhaustion-trigger work (stub intake, then 3b auto-breakdown):
   - Stub intake on 6 draft stubs: narrow-autopilot/tasks/07, shared-viz-renderer/tasks/05,
     shared-viz-renderer/tasks/06, trajectory-evals/tasks/05,
     trajectory-evals/tasks/06, trajectory-evals/tasks/07.
   - 3b auto-breakdown: specs/codebase-context-tree (Breakdown-ready: true,
     no tasks/ yet).
4. Spec-completion reviews for drain-worker-dispatch-hardening and
   context-blowout-subagent-guards once each lands a DONE task this run.

All other specs in scope (19 of 26) are already done/obsolete — nothing
else to do there. Full inventory taken this run; no need to re-scan.

## Anomalies

- At gen-1 startup, `claude agents --json` showed a stale/ambiguous
  background session record ("Drain hub specs", id 021af2aa, state
  blocked, started ~12 days prior) — cwd did not resolve into this repo
  and no lease file contested it, so it was treated as non-live and
  ignored. Worth a glance if a successor generation sees odd concurrent
  activity, but it did not manifest as a real collision this run.
- Removed one genuinely stale orchestrator worktree/branch at session
  start (`.claude/worktrees/drain-orchestrator` on
  `drain-orchestrator-rigor-tier`, confirmed ancestor of main with no
  unique commits) and replaced it with this generation's own isolated
  checkout (branch `drain-orchestrator-run`). A successor generation
  should do the same liveness check before reusing or removing it.
- No DRAIN-OWNER.md is currently held by any spec — this baton is
  written at a clean boundary (no lease in flight), so a fresh claim on
  drain-worker-dispatch-hardening is a normal step-1 claim, not a
  baton-lineage adoption... UNLESS the successor generation's
  `Run-token:` is passed through unchanged (it should adopt this same
  token per the re-claim invariant, since this is a continuation of the
  same run, not a fresh launch).
