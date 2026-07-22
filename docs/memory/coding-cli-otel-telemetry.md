# Coding-CLI OpenTelemetry capabilities (as of 2026-07)

Read when wiring or parsing a coding CLI's telemetry — extending
`agentprof otel`, answering "can we get X from CLI Y's telemetry", or
choosing between OTel ingestion and a native transcript/DB parser.
Full citations and the design consequences live in
`specs/agentprof-otel-ingestion/SPEC.md` (Research grounding); this file
is the re-research-avoidance summary.

## Signal shapes (cross-CLI invariants)

- Hierarchy lives in **traces** (span parent chains); per-request
  cost/tokens live in **log events**; metrics are pre-aggregated
  (~60s) and lose per-turn granularity.
- OTLP LogRecords carry `trace_id`/`span_id` (spec-standard), so
  cost-bearing events can be joined onto the span tree.
- **No coding-CLI semantic convention exists.** GenAI semconv
  (`gen_ai.*`) is Development-stability in its own repo;
  `gen_ai.system` is deprecated for `gen_ai.provider.name`. Every CLI
  is its own attribute dialect — alias tables must be data-driven.

## Per-CLI matrix

- **Claude Code**: opt-in `CLAUDE_CODE_ENABLE_TELEMETRY=1`;
  metrics+logs stable, traces beta
  (`CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`). Span tree:
  `claude_code.interaction` → `llm_request`/`tool`/`hook`; a
  subagent's spans nest under the parent's `claude_code.tool` span
  (full delegation chain in one trace). `llm_request` spans carry
  BARE token keys (`input_tokens`, `cache_creation_tokens` — not
  `gen_ai.usage.*`); the `claude_code.api_request` log event carries
  `cost_usd`. Log↔trace correlation only from CLI v2.1.212. Reads
  W3C `TRACEPARENT` (headless `-p` included) — an orchestrator can
  root the trace.
- **Gemini CLI / Qwen Code**: mature OTel (metrics+logs+traces, plus
  local `outfile` export); span NESTING and log correlation
  unverified from docs. Qwen is a Gemini fork with `qwen-code.*`
  names.
- **Codex**: `[otel]` + `[otel.trace_exporter]` config; interactive
  mode emits traces+logs+metrics, but `codex exec` emits zero metrics
  and `codex mcp-server` no OTel at all (openai/codex#12913).
  Fallback: rollout JSONL under `~/.codex/sessions/`.
- **Antigravity**: NO OTel export at all
  (google-antigravity/antigravity-cli#366) — the native conversation-DB
  parser is the only path.
- **No OTel**: Aider (PostHog analytics), Cursor CLI, Amp, Crush
  (PostHog). opencode: undocumented experimental flag only. Copilot
  CLI: enterprise-managed settings / SDK `TelemetryConfig` only.
