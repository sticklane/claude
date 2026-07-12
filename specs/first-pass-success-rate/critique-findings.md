# Critique findings — first-pass-success-rate

Verdict: NOT READY (drain gen 7 critique intake, 2026-07-12)

1. **Pairing key (task identity) does not exist in the sample data — rate
   uncomputable as specified (conf 74).** Numerator pairs attempt-1 dispatches with
   relaunch/tournament siblings "for the same task", but agentprof-instrumentation
   inserts only `role:<role>` frames — no task-file frame; the spawn-prefix is the
   drain session's project/skill, shared across every task. The spec's fallback
   resolves to per-dispatch spawn identity, so attempt-1 and its relaunch get
   different identities and never pair → every attempt-1 reads retry-free → rate
   ~100% always (the meaningless output R2 is meant to prevent). This is a hidden
   cross-spec dependency on instrumentation owned by the dependency spec (listed here
   as out-of-scope), not an evidence detail.

2. **Aggregation shape has no slot for the rate; "per week" contradicts single
   7-day window (conf 62).** The cost-view summary is `{by_project,by_skill,by_agent_type,by_model,totals}`
   — collapsed totals, no per-sample data to pair on, single 7-day rolling cache.
   R3's "per week and per skill/project" has no structure to attach to; underspecified.

3. **Tournament-vs-attempt1 relationship undefined for denominator (conf 55).**
   Denominator keys on `role:worker-attempt1`. A task dispatched directly as tournament
   (t1/t2/t3) with no attempt-1 frame is silently excluded while tournament frames are
   treated as attempt-1 failure markers. Confirm tournament is always a retry of a
   prior attempt-1, else the rate double-counts/omits.

4. **AC4 "screenshot or DOM-grep evidence" — screenshot unavailable to unattended
   worker (conf 60).** DOM-grep is viable (server-side HTML) but needs real cached
   samples with an attempt-1+relaunch pair to render a non-trivial rate; no fixture/seed
   path specified → evidence step may stall. Make it curl+grep against a seeded cache,
   drop "screenshot" or mark manual-pending.

Non-blocking: both dependency specs exist and are open with task files; agentprof/ and
agent-console in-repo; R5 mirror obligation correctly N/A (Touch is code-only .py/.go).
