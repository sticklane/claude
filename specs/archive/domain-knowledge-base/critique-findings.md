# Critique findings — domain-knowledge-base

Verdict: **NOT READY** (drain gen 4 critique intake, 2026-07-12; Run-token e83f34f07094a4fa)

The spec proposes a new human-invoked `/domain-knowledge` skill, but most of its
acceptance criteria are unsatisfiable by an unattended drain worker (they require
live `deep-research`/`Workflow` dispatch and interactive skill runs), and it
depends on an unbuilt sibling spec. Needs a human revision before breakdown.

## Ranked findings (from the critic agent)

1. **Core criteria gate on a `deep-research`/`Workflow` dispatch a drain worker
   cannot perform (conf 90).** SPEC.md:169-171 and 176-179 require actually running
   the Workflow fan-out and an E2E `/domain-knowledge` run. CLAUDE.md:110-114
   prohibits gating drained-task acceptance on Workflow/`/evals`/execution-stage
   skills; R5 (SPEC.md:110) also sets `disable-model-invocation: true` so a worker
   can't even invoke the skill. Fix: give these criteria an explicit manual-pending
   path (cite docs/memory/unattended-worker-tool-limits.md).

2. **~6 of 8 behavioral criteria require live interactive runs, not runnable
   commands (conf 85).** SPEC.md:156-168 describe live-session behavior; one needs
   an `AskUserQuestion` prompt unavailable to background workers
   (token-discipline.md:116-123). Fix: split into (a) grep-able authoring tasks
   drain can close and (b) a human-verified behavioral checklist run post-merge.

3. **"Open questions: (none)" but R3 defers a drain-unresolvable design decision
   (conf 80).** SPEC.md:181-183 says none, yet R3 (SPEC.md:82-103) tells the
   implementer to verify the harness Workflow contract at implementation time —
   which needs exercising Workflow. Fix: resolve the ultracode-requirement question
   before /breakdown and move the answer into the spec.

4. **Cheap grep-able authoring conventions have no acceptance criterion (conf
   75).** `disable-model-invocation: true`, the `Next stage:` line, first-30-lines
   contract, <500-line bound — all requirements, no checkbox. Fix: add grep/line-
   count criteria.

5. **Hidden dependency on unbuilt sibling `idea-research-freshness` (conf 70).**
   R2/R1b/R4 defer the `Verified:` stamp convention to that spec, which is itself
   unbuilt (SPEC.md only, no tasks). Fix: declare an ordering dependency
   (idea-research-freshness ships first) or self-contain the `Verified: YYYY-MM-DD`
   + 90-day parse rule here.

## Next step

Human revises SPEC.md: add manual-pending paths for the research/E2E criteria,
split authoring vs behavioral verification, resolve R3, add the missing grep
criteria, and settle the idea-research-freshness ordering. Then re-run /critique.
Do not /breakdown until READY.
