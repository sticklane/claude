# Task 02: reprime + sessions sections in the cost summary

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: 01
Priority: P1
Budget: 8 turns
Spec: ../SPEC.md (requirements R2, R3)
Touch: agentprof/internal/costsummary/, agentprof/testdata/

## Goal

`--summary` JSON gains two additive sections. `reprime`: count of
reprime-labeled samples, their total cache_write tokens, total
cost_microusd, and a by_project breakdown. `sessions`: per session id —
project, calls, total cost, and p50/p90 of per-call context size
(cache_read_tokens + input_tokens), computed over MAIN-LOOP samples only
(the spec's stated default; task 04 documents the choice). Existing
sections and field names unchanged.

## Touch

costsummary only. Under `--merge`, both sections aggregate `forGrouping`
(the merged rolling window, cmd_claude.go:126-127) like existing buckets —
never just the fresh slice. Do NOT touch `internal/claude/` (task 01
owns it), `agent-console/` (task 03), or docs (task 04). If
`costsummary.Build`'s signature already receives what you need, do not
change cmd_claude.go; if a change there is unavoidable, keep it to the
Build call site.

## Steps

1. Failing tests first in `internal/costsummary`: fixture samples with
   reprime labels and multi-session main-loop/agent mixes; assert
   `reprime.count/cache_write_tokens/cost_microusd/by_project` and
   `sessions.<id>.p50_ctx/p90_ctx` (agent samples excluded from ctx
   percentiles).
2. Implement both sections in Build over the forGrouping slice.
3. Confirm no existing field name changes (backward-compat test on a
   pre-change golden summary if one exists; otherwise assert key set
   superset).

## Acceptance

- [ ] `cd agentprof && go test ./internal/costsummary/` → pass, including
  new fixtures asserting `reprime` (count, cache_write_tokens,
  cost_microusd, by_project) and `sessions` (p50_ctx, p90_ctx,
  main-loop-only)
- [ ] `cd agentprof && go test ./...` → pass (no existing consumer broken)
- [ ] `bash agentprof/scripts/check.sh` → green
