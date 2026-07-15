# Unattended workers can't use the Workflow tool or launch gated skills

When to read: authoring a task that will be drained/parallelized, debugging
a worker that returned DEFERRED/BLOCKED on an acceptance criterion it "couldn't
run," or smoke-testing a change to a gated skill (`/build`, `/drain`,
`/evals`).

## The gotcha

**Post-2026-07-11 migration, this is two different mechanisms, not one** —
don't assume `disable-model-invocation` frontmatter explains all three:

- `/evals` (and the `Workflow` tool, and `/deep-research`) are still
  genuinely removed from the model's reach — `disable-model-invocation`
  blocks the tool-call layer regardless of who's asking.
- `/build`, `/drain`, `/prioritize` dropped
  `disable-model-invocation` — they're model-invocable, but ONLY when the
  human's live message names the stage (CLAUDE.md's authoring
  conventions). A dispatched worker's prompt is synthesized by the
  orchestrator, never a live human utterance, so the practical
  conclusion is unchanged: **a worker still can't launch these**, but the
  reason is now "no live-user authorization in this context," not "the
  skill isn't in my toolset." Don't grep a worker's tool list to explain a
  DEFERRED on one of these four; check whether the dispatch prompt could
  ever satisfy the launch-authorization contract instead.

So any acceptance criterion that requires _observing a live Workflow run_ or
_launching a gated skill_ is unsatisfiable inside the worker, for either
reason above.

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

Confirmed 2026-07-06 (drain auto-breakdown feature, **pre-migration**): a
`general-purpose` background agent — full tool access, explicitly
instructed by a human-directed request to call `Skill(skill: "drain")` —
hit a hard `InputValidationError`-style block, not a soft refusal. That
was `disable-model-invocation` enforced at the tool-call layer.

**Unverified post-migration:** `/drain`/`/build`/`/prioritize`
no longer carry that flag, so it's an open question whether an
`Agent`-dispatched worker instructed to call `Skill(skill: "drain")` now
hits a hard block, a soft model-level refusal (the model reading its own
SKILL.md's launch-authorization paragraph and declining), or actually
succeeds — the mechanism moved from "tool-call-layer removal" to
"documented convention in the skill body," which is a different
enforcement shape. Don't assume the pre-migration hard-block result still
holds for these four without testing it directly; `/evals` (still
`disable-model-invocation: true`) should still hard-block the same way.

Consequence either way: an in-session `Agent` dispatch is not a reliable
way to smoke-test a gated skill's real invocation — it can only hand-walk
the skill's written procedure step-by-step (validates the _logic_, not
that the actual `/command` invocation works end-to-end). To really exercise
`/build`/`/drain`/`/evals`, use headless CLI
(`claude -p "/drain ..."`, what `evals/run.sh` already does) or the human
runs it directly. When reporting a smoke test's results, say plainly which
kind you ran — the caveat matters for how much the PASS is worth.
