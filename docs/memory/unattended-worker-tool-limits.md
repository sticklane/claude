# Unattended workers can't use the Workflow tool or `disable-model-invocation` skills

When to read: authoring a task that will be drained/parallelized, debugging
a worker that returned DEFERRED/BLOCKED on an acceptance criterion it "couldn't
run," or smoke-testing a change to a gated skill (`/build`, `/drain`,
`/autopilot`, `/evals`).

## The gotcha

A `general-purpose` background worker (what drain/autopilot dispatch)
does **not** have the `Workflow` tool, and cannot invoke any
`disable-model-invocation` skill (`/build`, `/drain`, `/evals`,
`/deep-research`, …) — those are removed from the model's reach by design. So
any acceptance criterion that requires _observing a live Workflow run_ or
_launching a gated skill_ is unsatisfiable inside the worker.

Seen 3× in the 2026-07-04 drain: ultra-mode's "a Workflow run is observable"
e2e, wte-04's `[repo-deep-research]` resolution probe, and um-03's open-gate
panel e2e.

## How to author around it

- Give the criterion an **orchestrator-resolvable** escape: the main session
  (not a worker) HAS the Workflow tool, so it can run the probe post-merge and
  flip the task done (as done for wte-04's AC3 — launched `deep-research` by
  name, confirmed the marker, then completed the task).
- OR let the worker mark that one criterion **manual-pending with the reason**,
  and say so explicitly in the criterion text (as um-03's criterion 4 did) —
  this is satisfaction, not a DEFERRED.
- Don't write a drain-able task whose ONLY path to green needs a tool the
  worker lacks with no such escape — it will DEFER and stall the queue.

## Testing implication: you can't smoke-test a gated skill via Agent dispatch

Confirmed 2026-07-06 (drain auto-breakdown feature): a `general-purpose`
background agent — full tool access, explicitly instructed by a
human-directed request to call `Skill(skill: "drain")` — hit a hard
`InputValidationError`-style block, not a soft refusal. The
`disable-model-invocation` gate is enforced at the tool-call layer
regardless of who or what is asking; it doesn't matter that a human's
instructions are what ultimately drove the call.

Consequence: an in-session `Agent` dispatch can never exercise a gated
skill's real invocation for a smoke test — it can only hand-walk the
skill's written procedure step-by-step (which validates the *logic*, not
that the actual `/command` invocation works end-to-end). To really exercise
`/build`/`/drain`/`/autopilot`/`/evals`, use headless CLI
(`claude -p "/drain ..."`, what `evals/run.sh` already does) or the human
runs it directly. When reporting a smoke test's results, say plainly which
kind you ran — the caveat matters for how much the PASS is worth.
