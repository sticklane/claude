# Task 07: Document the otel subcommand in README

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: done
Depends on: 02, 03, 04, 05, 06
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (Phase 1 README; design pt 7 spool guidance)
Touch: agentprof/README.md

## Goal

`agentprof/README.md` documents the `otel` subcommand, which is entirely
undocumented today (`grep -c "otel serve" agentprof/README.md` → 0). Covers:
file mode (`agentprof otel <trace.json> -o profile.pb.gz`), the JSONL merge
form via `agentprof build`, `otel serve` (the live OTLP/HTTP receiver, its
`/v1/traces`, `/v1/logs`, `/v1/metrics` routes, gzip support), the two-tier
scope (OTel is pprof-only — it does NOT feed `costsummary`/the workboard cost
panel), the `cost_usd`→`cost_microusd` cost join, the supported dialects,
`--pricing`, and the durability/spool guidance (Gemini/Qwen `outfile` and
OTel Collector `fileexporter` → file mode; `OTEL_EXPORTER_OTLP_PROTOCOL=
http/protobuf` for gRPC-only emitters rather than a 4317 listener).

## Touch

README.md only. This is the single writer of README for this spec — it lands
last so it documents the metrics route (Task 05) and `--pricing` (Task 06)
as shipped. This is human-facing prose (the `/prose-review` charter): load
`prose-review` doctrine before drafting, and keep the copy scoped to what the
code actually does — every command shown must be one that runs.

## Steps

1. Read the shipped behavior from `cmd_otel.go` and the SPEC Scope section so
   the doc describes what exists, not aspiration (no `agentprof build`-via-
   pipe form — `build` reads positional paths only).
2. Add an `otel` section to `README.md` covering file mode, the JSONL→build
   merge form, `otel serve` and its routes, gzip, the pprof-only scope, the
   cost join, supported dialects, `--pricing`, and spool/durability guidance.
3. Verify every command block against the actual CLI (run `agentprof otel`
   with `-h` / against a fixture) so no invented flag or form appears.

## Acceptance

Runnable commands only:

- [x] `grep -c "otel serve" agentprof/README.md` → ≥1 (was 0 before this task) (L1)
- [x] `grep -c "/v1/logs" agentprof/README.md` → ≥1 (logs route documented) (L1)
- [x] `grep -c "OTEL_EXPORTER_OTLP_PROTOCOL" agentprof/README.md` → ≥1 (spool guidance present) (L1)
- [x] `bash agentprof/scripts/check.sh` → exits 0 (gofmt/vet/test unaffected by a docs-only change)

Depth ceiling: criteria are L1 (presence of documented commands/routes in
prose). Prose correctness is not mechanically checkable — the behavioral
complement is the `/prose-review` doctrine load in Steps and the
run-every-command-shown check in step 3.
