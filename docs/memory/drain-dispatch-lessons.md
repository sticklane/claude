# Drain dispatch lessons (queue 5, 2026-07-05)

Three worker-dispatch patterns that earned their keep across 8 dispatches;
each is a clause the orchestrator adds to the worker prompt (or a procedure
it follows), not a task-file edit.

## Pre-existing red gate → hand workers the baseline

When a repo gate is already red on main (queue 5: `tests/test_workboard_render.sh`,
two assertions), name the exact failing assertions in every dispatch prompt as
factual context: "verify it fails identically at your branch point (baseline);
it is NOT your acceptance; do not chase it; do not make it worse." Without
this, a conscientious worker either false-BLOCKs on the red gate or
scope-creeps into fixing it. The orchestrator likewise accepts post-merge
gate runs "green modulo the named baseline" — comparing to baseline, never
absolute green, until a task actually owns that fix.

## Worker-spawned sub-agent notifications route to the orchestrator

A background worker that fans out its own sub-agent (verifier, reviewer) may
never receive that sub-agent's completion notification — it can land on the
orchestrator session instead (observed live: a worker's verifier notification
arrived at drain while the worker kept running). Dispatch prompts must carry:
"do NOT block waiting on a notification from a sub-agent you spawn — run the
pass inline, or read its output directly." Orchestrators receiving a stray
sub-agent notification should log-and-ignore it, not treat it as the worker's
verdict.

## Cross-repo task: worktree the other repo too, never its live checkout

For a task whose Touch is in a different repo (queue 5: vendoring into
~/agent-console, whose working tree backs a live launchd service): the worker
keeps toolkit bookkeeping (task file, evidence) on its toolkit branch as
normal, and does the code work in a `git worktree` of the OTHER repo on a
task branch (worktree under the session scratchpad), leaving the live
checkout untouched. The orchestrator merges both branches at collect time,
re-runs the other repo's gate on the real path, pushes both, and restarts
the service (label `com.agent-console`, not com.sjaconette.*) so the running
process picks up the merged code.
