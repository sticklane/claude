# Task 02: Per-session reprime fields in the cost summary

Status: done
Depends on: none
Priority: P1
Budget: 10 turns
Spec: ../SPEC.md (requirement R2a)
Touch: agentprof/internal/costsummary/, agentprof/SCHEMA.md

## Goal

The `--summary` output's `sessions` entries carry two new additive fields,
`reprime_count` and `reprime_cost_microusd`, aggregating each session's
samples labeled `reprime=true`. Existing field names are unchanged; older
summary JSON parses as before. SCHEMA.md documents the fields.

## Touch

costsummary package + SCHEMA.md only. Do NOT touch
`agentprof/internal/claude/` (the reprime label is shipped and correct)
or `agent-console/` (task 05 consumes these fields). Cross-spec:
`specs/untyped-agent-fanout/tasks/04-*` also edits costsummary and
declares a cross-spec `Depends on:` path to THIS task — one repo-wide
drain serializes them (this one lands first).

## Steps

1. Write the failing test first: a fixture with reprime-labeled and
   unlabeled samples across two sessions asserts each session's
   `reprime_count`/`reprime_cost_microusd` and that a session with no
   re-primes reports 0/0.
2. Extend the `sessions` rollup (`SessionStat`) additively; respect the
   `--merge` rolling-window aggregation path the existing sections use.
3. Document both fields in SCHEMA.md's cost-summary section.
4. `bash agentprof/scripts/check.sh` green.

## Acceptance

- [x] `cd agentprof && go test ./internal/costsummary/` → pass, including the new per-session reprime test — verifier: 17/17 pass incl. TestBuildSessionsSectionPerSessionReprimeAggregates (evidence/02-per-session-reprime-fields.md)
- [x] `cd agentprof && go build -o agentprof . && ./agentprof claude --days 7 --summary /tmp/s.json -o /dev/null && jq -e '.sessions | to_entries[0].value | has("reprime_count") and has("reprime_cost_microusd")' /tmp/s.json` → true — verifier: prints `true` (evidence/02-per-session-reprime-fields.md)
- [x] `grep -c 'reprime_count' agentprof/SCHEMA.md` → ≥ 1 — verifier: 2 (evidence/02-per-session-reprime-fields.md)
- [x] `bash agentprof/scripts/check.sh` → green — verifier: format-check/lint/tests ok, exit 0 (evidence/02-per-session-reprime-fields.md)
