# Task 05: /v1/metrics ingestion (coarse cross-check)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: pending
Depends on: 02
Priority: P3
Budget: 16 turns
Spec: ../SPEC.md (design pt 1 "add /v1/metrics last"; Phase 2)
Touch: agentprof/cmd_otel.go, agentprof/cmd_otel_test.go, agentprof/internal/otel/metrics.go, agentprof/internal/otel/metrics_test.go, agentprof/internal/otel/testdata/

## Goal

The `otel serve` receiver accepts `/v1/metrics` (OTLP/JSON + protobuf, gzip)
as a coarse cross-check signal, decoding OTLP metrics into token/cost totals
where the CLI emits them. This is the lowest-fidelity tier (design pt 1
"coarse cross-check") — traces remain the stack backbone and logs the cost
source; metrics never override a trace-derived sample.

## Touch

Adds the `/v1/metrics` route in `cmd_otel.go` and a new
`internal/otel/metrics.go` decoder (plus its test); reuses the gzip and
content-type plumbing from Task 02. Do NOT modify `otel.go`'s span/cost join
or the dialect table (Tasks 01–04) — keep metrics decoding in its own file so
this task stays disjoint from the otel.go-editing tasks.

## Steps

1. Write failing tests first:
   - in `cmd_otel_test.go`: a POST to `/v1/metrics` (JSON, then protobuf,
     then gzip) returns success instead of 404;
   - in `metrics_test.go`: a metrics-export fixture decodes into the
     expected coarse totals.
   Confirm they fail (route 404s today — see `cmd_otel.go:145` and the
   existing `TestOtelServeNonTracePathsReturn404`, which must be updated to
   drop `/v1/metrics`).
2. Add `internal/otel/metrics.go` decoding OTLP `metrics/v1` proto (vendored
   at `go.opentelemetry.io/proto/otlp v1.10.0`) into a coarse totals struct.
3. Register `/v1/metrics` in the receiver handler alongside `/v1/traces` and
   `/v1/logs`, reusing gzip + content-type handling; keep `/` and other
   unknown paths returning 404 (update `TestOtelServeNonTracePathsReturn404`
   accordingly).
4. Add a golden metrics fixture under `internal/otel/testdata/`.

## Acceptance

Runnable commands only:

- [ ] `cd agentprof && go test . -run 'OtelServe.*Metrics|Metrics' -v` → metrics route + decode tests pass (L2)
- [ ] `grep -c '/v1/metrics' agentprof/cmd_otel.go` → ≥1 (route registered, no longer only in a comment)
- [ ] `bash agentprof/scripts/check.sh` → exits 0
