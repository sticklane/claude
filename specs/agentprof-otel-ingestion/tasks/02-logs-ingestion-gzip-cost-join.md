# Task 02: /v1/logs ingestion, gzip, and trace-context cost join

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: done
Depends on: 01
Priority: P1
Budget: 26 turns
Spec: ../SPEC.md (design pts 1, 5, 6; Phase 1 logs + cost join)
Touch: agentprof/internal/otel/otel.go, agentprof/internal/otel/otel_test.go, agentprof/cmd_otel.go, agentprof/cmd_otel_test.go, agentprof/internal/otel/testdata/

## Goal

The OTel path ingests OTLP **log** records (OTLP/JSON + protobuf) in both the
`otel serve` receiver (new `/v1/logs` route) and file mode, and joins a log
record's cost onto its correlated span. A log record carrying
`trace_id`/`span_id` whose `span_id` matches a token-bearing span attaches
its cost to that span's sample; Claude Code's fractional-USD `cost_usd`
converts to integer `cost_microusd` via ×1e6 (round). The `Flush` gate is
relaxed to emit a sample for a span with tokens **OR** attached cost. A log
record without trace context degrades to a flat sample
(`[service.name, event-name]` stack) with token/cost intact and hierarchy
absent. Requests with `Content-Encoding: gzip` are decompressed on all
receiver routes.

## Touch

Handles only the direct span_id→same-span join. The frames-only-ancestor
fallback and multi-descendant timestamp tie-break are Task 03 — do NOT
implement the descendant walk here; a cost event targeting a non-token span
may attach nothing yet (Task 03 completes that path). Add fixtures under
`internal/otel/testdata/` with `logs`/`cost`-prefixed names.

## Steps

1. Write failing tests first:
   - in `otel_test.go`: a log record with `span_id` matching a token-bearing
     span attaches `cost_microusd` to that span's sample; `cost_usd` of e.g.
     `0.041230` becomes `cost_microusd: 41230`; a cost-only span (cost
     attached, no tokens) is now emitted under the relaxed gate; a log
     record with no trace context yields a flat `[service, event-name]`
     sample;
   - in `cmd_otel_test.go`: a POST to `/v1/logs` (JSON) returns success and
     the accumulated log is joined at flush; a gzip-`Content-Encoding` body
     is decoded; `/v1/logs` protobuf POST decodes.
   Confirm each fails for the right reason (route 404s / logs unparsed
   today).
2. Add OTLP logs decoding to the `Accumulator`: `AddLogsJSON` (reuse the
   existing hex-ID→base64 rewrite for `trace_id`/`span_id`) and
   `AddLogsProto`, decoding into `logs/v1` proto types (already vendored at
   `go.opentelemetry.io/proto/otlp v1.10.0`). Store each record's
   `trace_id`, `span_id`, timestamp, and cost (from the Claude
   `cost_usd`-style attribute) plus resource `service.name`.
3. In `Flush`, before resolving samples, index cost records by
   `(trace_id, span_id)` and attach each to the matching token-bearing span;
   relax the emit gate to `hasTokens || hasCost`. A record with no
   `span_id`/`trace_id` produces a standalone flat sample.
4. Convert `cost_usd` (fractional USD, float) to `cost_microusd` (int64) via
   `round(cost_usd * 1e6)` and emit into `Values`.
5. In `cmd_otel.go`: register `/v1/logs` (POST, JSON + protobuf, mirroring
   `/v1/traces`); add gzip `Content-Encoding` decompression shared by all
   routes; in file mode, accept logs-export objects alongside trace-export
   objects (detect by decode, try both) so Collector `fileexporter` JSONL of
   mixed records works.
6. Add golden fixtures under `internal/otel/testdata/`: a trace + a
   correlated cost log, and an uncorrelated cost log.

## Acceptance

Runnable commands only:

- [x] `cd agentprof && go test ./internal/otel/ -run 'Cost|Log|Flush' -v` → new join/gate tests pass (L2)
- [x] `cd agentprof && go test . -run 'OtelServe.*Logs|OtelServe.*Gzip' -v` → `/v1/logs` + gzip receiver tests pass (L2)
- [x] `grep -c '/v1/logs' agentprof/cmd_otel.go` → ≥1 (route registered)
- [x] `grep -c 'cost_microusd' agentprof/internal/otel/otel.go` → ≥1 (cost emit path)
- [x] `bash agentprof/scripts/check.sh` → exits 0
- [ ] MANUAL-PENDING (human, not drain-gated): confirm against a real Claude
      Code capture which span the `claude_code.api_request` cost event's
      `span_id` actually targets — the spec files this as a manual-pending
      live-capture step (SPEC.md design pt 6). Fixture-based hardening in
      this task and Task 03 proceeds without it; a human runs the live check
      post-merge per docs/memory/unattended-worker-tool-limits.md.
