Status: draft
Discovered-from: specs/workboard-weekly-cost-view/tasks/02-summary-flag.md
Spec: ../SPEC.md
Blocking: no

# Spec note: pure tool: samples have no explicit "no model" bucket in costsummary grouping

Pure `tool:` samples (e.g. `[proj, turn, skill, main, tool:Workflow]`, carrying only `duration_ms`) resolve their model to `"main"` under the R3 "last leaf frame that isn't tool:/role:/stage:" rule, so `duration_ms` lands in `by_model["main"]` in `agentprof/internal/costsummary/costsummary.go`'s `modelLeaf` — harmless today (tool samples carry no tokens/cost, and the panel shows cost/model, not duration), but worth a spec note once agentprof-instrumentation ships richer tool/duration frames, since the contract has no explicit "no model" bucket.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
