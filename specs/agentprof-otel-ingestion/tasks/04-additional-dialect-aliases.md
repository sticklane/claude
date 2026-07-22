# Task 04: codex / gemini_cli / qwen-code dialect aliases

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: pending
Depends on: 03
Priority: P2
Budget: 16 turns
Spec: ../SPEC.md (design pt 3, 4; Phase 2 dialects)
Touch: agentprof/internal/otel/otel.go, agentprof/internal/otel/otel_test.go, agentprof/internal/otel/testdata/

## Goal

The dialect-detection scaffold from Task 01 recognizes three more coding-CLI
dialects — `codex.*`, `gemini_cli.*`, `qwen-code.*` — each mapping its
span/event-name prefix and session identifier into the canonical schema, with
a generic `gen_ai.*` fallback for unrecognized services. Each dialect maps
its session identifier (Claude `session.id`, Codex `conversation.id`, …) into
`labels["session"]` for pprof tag filtering. Alias lists stay data-driven.
Detection is by resource `service.name` and span/event-name prefix. Golden
OTLP JSON fixtures exercise each dialect (fixture files only — no live CLIs
in tests).

## Touch

Extends the alias/dialect table in `internal/otel/otel.go`; do NOT alter the
cost-join logic (Tasks 02/03). Add per-dialect fixtures under
`internal/otel/testdata/` with `codex`/`gemini`/`qwen` prefixes.

## Steps

1. Write failing tests first in `otel_test.go`: one per dialect asserting a
   representative span under `codex.*` / `gemini_cli.*` / `qwen-code.*` emits
   a sample with the expected canonical token values and a
   `labels["session"]` populated from that dialect's session key; plus a
   generic `gen_ai.*` service falling back to the base alias set. Confirm
   they fail for the right reason.
2. Add each dialect's detection prefix and alias entries to the data-driven
   table introduced in Task 01. Map each dialect's session identifier into
   `labels["session"]` (`session.id`, `conversation.id`, …).
3. Keep the `gen_ai.*` generic fallback as the default when no dialect
   prefix matches.
4. Add golden JSON fixtures under `internal/otel/testdata/`, one per dialect.

## Acceptance

Runnable commands only:

- [ ] `cd agentprof && go test ./internal/otel/ -run 'Codex|Gemini|Qwen|Dialect' -v` → per-dialect tests pass (L2)
- [ ] `grep -c 'gemini_cli' agentprof/internal/otel/otel.go` → ≥1 (dialect registered)
- [ ] `grep -c 'labels\["session"\]\|"session"' agentprof/internal/otel/otel.go` → ≥1 (session label mapped)
- [ ] `bash agentprof/scripts/check.sh` → exits 0
- [ ] MANUAL-PENDING (human, not drain-gated): live-verify Gemini CLI span
      nesting and Codex `session_loop` span shape against real exports before
      relying on those dialects in production — SPEC.md Phasing marks this a
      human-run manual-pending step (docs/memory/unattended-worker-tool-limits.md),
      not a gate on this drained task; fixture-based aliasing lands now.
