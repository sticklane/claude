# CUJ-3 — Fan-out with scouts

Live, 2026-07-22, both legs.

## Pre-flight guard leg (spec's 30-vs-20 fixture)

```
preflight_fanout.sh 30
  REFUSED — estimate 30 x 36000 = 1080000 tokens, above threshold 20
  agents. Pass --override to proceed anyway.        exit=1
preflight_fanout.sh 30 --override
  above threshold 20, proceeding (explicit --override given)  exit=0
```

`tests/test_preflight_fanout.sh` → 8/8, `PREFLIGHT TEST OK`.

## Authored-workflow leg (dogfood)

The /work implementation itself ran as an authored native workflow
(run `wf_7626ae77-431`): mechanical recon stages pinned cheap-tier
(`model: 'haiku'`), judgment stages (skill authoring, verify) on
opus/session tier, every stage returning a schema'd result. Results
the run kept were filed to bd before session end — the epic
`agentic-5ge` children — and the eval scenario
(`evals/work/01-queue-discipline`) asserts the same contract
mechanically: the authored script must carry a cheap-tier `model:`
option on its scout stage (assert passes, `1/1 scenarios passed`).

Tiering doctrine: `.claude/rules/token-discipline.md` (cited, not
restated).
