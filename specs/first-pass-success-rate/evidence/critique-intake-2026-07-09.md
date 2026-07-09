# Critique intake verdict: NOT READY (2026-07-09, single-pass)

Dependencies verified done and real (role: frames land at
agentprof/internal/claude/claude.go:332; markers emitted in drain/SKILL.md;
JSONL cache + --summary exist). The blocking problem is data content:

1. (80) The per-dispatch/per-task identity the metric needs is ABSENT from
   persisted samples ({Time, Stack, Values, Labels{source,session,turn}} —
   no task-path frame, no tool_use id). Drain's concurrent group launch
   makes K attempt-1 workers share Stack+session+turn → the denominator
   collapses; attempt-1 vs relaunch can never pair by spawn identity.
   Resolve at spec time: either (a) persist a per-dispatch identity label
   (reopens the agentprof dependency; violates R1's no-new-parse claim —
   must be scoped), or (b) redefine as counting:
   1 − count(worker-relaunch)/count(worker-attempt1), with the concurrent
   same-turn counting mechanism specified (today's cache cannot do it).
2. (78) costsummary.Build sums cost by project/skill/agent/model and
   ignores role: — the "same code path, small delta" premise is wrong;
   state which artifact the rate reads and re-scope.
3. (65) Acceptance fixtures sidestep the real failure mode — add a
   concurrent same-session+turn fixture that must count as 2, and a
   per-skill/project split fixture.

Route: NOT READY → human checklist. Next: resolve the identity question in
the spec (likely alongside a small agentprof follow-up), then re-run
/critique.
