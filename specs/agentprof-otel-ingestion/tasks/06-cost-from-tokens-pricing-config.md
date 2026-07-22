# Task 06: cost-from-tokens (Claude table) + optional user pricing config

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: in-progress
Depends on: 04
Priority: P2
Budget: 18 turns
Spec: ../SPEC.md (design pt 5; Decision 6; Phase 2)
Touch: agentprof/internal/otel/otel.go, agentprof/internal/otel/otel_test.go, agentprof/cmd_otel.go, agentprof/cmd_otel_test.go, agentprof/internal/otel/testdata/

## Goal

When a Claude-model OTel sample carries tokens but no emitted cost, cost is
computed from tokens via the existing `internal/pricing` Claude table
(prefix-matched `claude-*`) and emitted as `cost_microusd`. An emitted cost
attribute still wins (prefer emitted, else compute where a table matches,
else tokens-only). Gemini stays tokens-only (Decision 6 — the Gemini table
is exact-map on Antigravity display strings that OTel API model IDs never
hit; no model-ID→table-key normalization is added). Optionally, a
user-supplied pricing config (`--pricing <file>`) supplies rates for other
dialects. No new baked vendor tables are added (maintenance treadmill,
design pt 5).

## Touch

Adds cost-from-tokens computation to `internal/otel/otel.go` (calling
`internal/pricing.Price`) and a `--pricing` flag in `cmd_otel.go`. Depends on
Task 04 because it edits the same `otel.go` sample-emission surface as the
dialect table. Do NOT add new hard-coded vendor rate tables. Add fixtures
under `internal/otel/testdata/` with `pricing`-prefixed names.

## Steps

1. Write failing tests first:
   - in `otel_test.go`: a token-only span with a `claude-*` model gets a
     `cost_microusd` computed from `internal/pricing.Price`; a span with an
     emitted cost keeps the emitted value (emitted wins over computed); a
     Gemini-model token-only span stays tokens-only (no `cost_microusd`);
   - a `--pricing`-supplied config applies its rates to a matching
     non-Claude model.
   Confirm each fails for the right reason.
2. In `sample()`/`Flush`, when a span has tokens, no attached cost, and its
   model prefix-matches the Claude pricing table, call
   `pricing.Price(model, usage)` and emit `cost_microusd` when priced.
3. Add a `--pricing <file>` flag to `cmd_otel.go` (and `otel serve`) parsing
   a simple user rate table, threaded into the accumulator; absent flag ⇒
   Claude-table-only behavior.
4. Add golden fixtures under `internal/otel/testdata/` for the Claude
   compute path and the user-config path.

## Acceptance

Runnable commands only:

- [ ] `cd agentprof && go test ./internal/otel/ -run 'CostFromTokens|Pricing|Emitted' -v` → compute + precedence + Gemini-tokens-only tests pass (L2)
- [ ] `cd agentprof && go test . -run 'Otel.*Pricing' -v` → `--pricing` flag test passes (L2)
- [ ] `grep -c 'internal/pricing' agentprof/internal/otel/otel.go` → ≥1 (pricing table wired)
- [ ] `bash agentprof/scripts/check.sh` → exits 0
