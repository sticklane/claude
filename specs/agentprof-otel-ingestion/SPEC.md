# agentprof OpenTelemetry ingestion for coding CLIs

Produced by the 2026-07-21 investigation session. Critic verdict on this
draft: NOT READY — five open decisions below must be resolved before
breakdown. This spec deliberately carries no `Breakdown-ready:` marker.

## Problem

agentprof profiles agent spend by normalizing session activity into a
canonical sample schema (`agentprof/SCHEMA.md`): timestamp + root-first
stack (project > skill > agent > model) + values (`input_tokens`,
`output_tokens`, `cache_read_tokens`, `cache_write_tokens`,
`cost_microusd`, `calls`, `wall_ms`, `ctx_usage`) + labels. Its sources
are CLI-specific parsers: `claude` (transcripts under
`~/.claude/projects/`), `antigravity`, `gcp`, `vertex`. We want coverage
of other coding CLIs (Gemini CLI, Codex, Qwen Code, Goose, Copilot, …)
without a bespoke parser per CLI. OpenTelemetry is the portability layer:
most actively-developed coding CLIs export OTLP; agentprof should consume
it.

## Current code state (verified 2026-07-21)

- `agentprof otel` exists: file mode (OTLP/JSON export object or JSONL)
  and `otel serve` (live OTLP/HTTP receiver, default `localhost:4318`,
  JSON + protobuf).
- Traces only: `/v1/traces` registered; `/v1/metrics` and `/v1/logs`
  return 404 (`agentprof/cmd_otel.go:144-145`).
- Stack built as `[service.name, root_span…leaf_span]` from the span
  parent chain (`internal/otel/otel.go:178-232`); model is emitted as a
  label, not a stack frame.
- Attribute aliases: `gen_ai.usage.input_tokens` →
  `gen_ai.usage.prompt_tokens`; `gen_ai.usage.output_tokens` →
  `gen_ai.usage.completion_tokens`; `gen_ai.response.model` →
  `gen_ai.request.model`; `gen_ai.system` → `gen_ai.provider.name`.
- `Flush` emits a sample only for spans with token attributes
  (`internal/otel/otel.go:98-113`).
- No cost computation on the otel path. `internal/pricing/` carries a
  Claude table (`table.go`, `claude-*` prefixes, snapshot 2026-07-02)
  AND a Gemini table (`gemini_table.go`).
- `costsummary.Build` is invoked only from `cmd_claude.go:166` — OTel
  samples currently never reach the cost rollups the workboard reads.
- The `otel` subcommand is undocumented in `agentprof/README.md`.

## Research grounding (external claims, with confidence)

1. **Traces carry hierarchy; trace-correlated log events carry cost.**
   Claude Code (`CLAUDE_CODE_ENABLE_TELEMETRY=1` +
   `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`) emits a real span tree:
   `claude_code.interaction` → `claude_code.llm_request` /
   `claude_code.tool` / `claude_code.hook`; a spawned subagent's
   `llm_request`/`tool` spans nest under the parent's
   `claude_code.tool` span — "the full delegation chain appears as one
   trace" (code.claude.com/docs/en/agent-sdk/observability;
   corroborated by OpenObserve and Langfuse integration docs).
   `claude_code.llm_request` spans carry `input_tokens`,
   `output_tokens`, `cache_read_tokens`, `cache_creation_tokens`; the
   `claude_code.api_request` log event adds `cost_usd`, and since CLI
   v2.1.212 log records carry `trace_id`/`span_id` (OTLP LogRecord
   trace-context fields are spec-standard).
2. **TRACEPARENT propagation stitches cross-process trees.** Claude
   Code reads W3C `TRACEPARENT`/`TRACESTATE` (including headless `-p`),
   so an orchestrator's span can root each CLI run's trace.
3. **Per-CLI trace maturity varies.** Codex: interactive mode emits
   traces+logs+metrics (`[otel.trace_exporter]` config); third-party
   docs (Coralogix) describe a `session_loop` root span with child
   spans per API call and tool invocation — likely, not
   official-doc-verified. `codex exec` emits zero metrics;
   `codex mcp-server` initializes no OTel (openai/codex#12913).
   Gemini CLI: mature metrics/logs/traces export, but span NESTING and
   log-trace correlation are UNVERIFIED from its docs. Qwen Code
   mirrors Gemini with `qwen-code.*` names. Goose emits OTLP/HTTP
   traces. Copilot CLI: enterprise-managed/SDK-driven only.
4. **Antigravity has no OTel export** (open request,
   google-antigravity/antigravity-cli#366) — it stays on the existing
   native DB parser.
5. **No-OTel CLIs:** Aider (PostHog analytics only), Cursor CLI, Amp,
   Crush (PostHog; OTel requested), opencode (experimental
   undocumented flag).
6. **No coding-CLI semantic convention exists.** GenAI semconv is
   Development-stability in its own repo; `gen_ai.system` is deprecated
   for `gen_ai.provider.name`. Each CLI namespaces its own
   span/event/metric names and attribute keys (Claude Code uses bare
   `input_tokens`, not `gen_ai.usage.input_tokens`), so a mapping layer
   is unavoidable.

## Design: two-tier fidelity, trace-first with correlated events

**Tier 1 — high-fidelity native parsers (unchanged).** `claude` and
`antigravity` remain primary for those runtimes: `ctx_usage`
percentiles, reprime detection, skillcheck's trigger audit (needs
prompt/reply heads, which OTel redacts by default), and untyped-fanout
depth all require transcript-level data; Antigravity has no OTel path
at all. OTel does not replace these parsers.

**Tier 2 — portable OTel ingestion (this spec's scope).**

1. **Traces are the stack backbone; add `/v1/logs` joined on trace
   context.** Extend the receiver and file mode with `/v1/logs`
   (OTLP/JSON + protobuf, gzip). When a log record carries
   `trace_id`/`span_id`, attach its values (notably cost) to the
   correlated span's sample. Log events without trace context degrade
   to flat samples — cost rollups intact, hierarchy absent. Add
   `/v1/metrics` last as a coarse cross-check.
2. **Frame-convention mapping per dialect.** The current
   `[service.name, span names…]` stack does not conform to the
   `project > skill > agent > model` frame convention costsummary
   parses by prefix (`skill:`, `agent:`, `main`, model leaf). Each
   dialect must map spans into canonical frames, and the model must
   become the leaf frame for OTel samples (today it is only a label).
   Shape per dialect is Open decision 1.
3. **Attribute aliases per dialect, data-driven.** Detection by
   resource `service.name` and span/event-name prefix
   (`claude_code.*`, `gemini_cli.*`, `qwen-code.*`, `codex.*`; generic
   `gen_ai.*` fallback). Concretely for Claude Code:
   `input_tokens` → canonical `input_tokens`, `output_tokens` →
   `output_tokens`, `cache_read_tokens` → `cache_read_tokens`, and
   `cache_creation_tokens` → canonical **`cache_write_tokens`** (the
   reprime rollups and SCHEMA.md consume `cache_write_tokens`; passing
   the source key through verbatim would silently drop cache-write
   signal). Alias lists stay data-driven; the semconv is pre-stable.
4. **Session and project mapping.** Each dialect maps its session
   identifier (Claude `session.id`, Codex `conversation.id`, …) into
   `labels["session"]` so `distinctSessions`/`sessionStats` work.
   OTel has no project dimension; the project frame source is Open
   decision 5.
5. **Cost: prefer emitted, else compute from existing tables, else
   tokens-only.** Use an explicit cost attribute when present
   (Claude's `cost_usd`, fractional USD — convert to integer
   `cost_microusd` by ×1e6 and round). For token-only dialects whose
   models are covered by the tables already in `internal/pricing/`
   (Claude, Gemini), compute cost from tokens. Do NOT add new baked
   vendor tables (maintenance treadmill); at most accept a
   user-supplied pricing config for other dialects.
6. **Durability/spool.** OTel is prospective-only: the receiver must be
   running while sessions happen, unlike retrospective transcript
   parsing. Mitigations, documented not built: Gemini/Qwen telemetry
   `outfile` → file mode; OTel Collector `fileexporter` JSONL → file
   mode. gRPC-only emitters: document
   `OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf` (all target CLIs
   support OTLP/HTTP) instead of adding a 4317 gRPC listener.
7. **TRACEPARENT stitching for fleets (opportunity, not core).** An
   orchestrator setting `TRACEPARENT` on spawned workers yields one
   cross-process delegation trace; the stack builder then attributes
   worker spend under the orchestrator frame. Candidate later
   integration: drain/fleet dispatch templates exporting trace context.
8. **No bespoke file parsers for no-OTel CLIs.** Rejected as a
   treadmill against undocumented, churning formats. Build one only on
   demonstrated demand.

## Open decisions (critic round 1 — resolve before READY)

1. **Frame mapping shape per dialect** (critic finding 1, high). How do
   `claude_code.*` spans map into `project > skill > agent > model`
   frames? Recommendation: `interaction` → `main`-equivalent frame;
   the `claude_code.tool` span that roots a subagent → `agent:<name>`
   frame from `agent.name`; `llm_request` → model leaf from its model
   attribute; skill frames from `skill.name` when present. Flat
   dialects get `[project, model]` only.
2. **Wiring OTel samples into costsummary** (finding 2, high).
   `costsummary.Build` is claude-adapter-only today. Recommendation:
   route `otel` output through costsummary so the workboard cost panel
   covers OTel sources; alternative is declaring the panel
   claude-only and OTel pprof-only — but that halves the feature's
   value and should be an explicit choice, not a default.
3. **Tier 1 / Tier 2 double-counting for Claude sessions** (finding 3,
   high). A user running both the transcript parser and Claude-Code
   OTel ingestion over the same sessions double-books cost.
   Recommendation: dedup on session id at merge time, Tier 1 wins;
   simplest safe default is excluding `claude_code.*` OTel samples
   from merged cost rollups unless the transcript source is absent.
4. **Log→span join target vs the `hasTokens` gate** (finding 4, high).
   Claude's cost lives on the `api_request` log event; tokens live on
   the `llm_request` span; `Flush` drops token-less spans. Specify
   which span the event's `span_id` targets in practice and how
   attached-cost-only spans survive — recommendation: relax the gate
   to emit samples for spans with tokens OR attached cost, and if the
   join target is a frames-only ancestor, attach cost to the nearest
   token-bearing descendant sample; verify actual `span_id` targeting
   against a live capture before hardening.
5. **Project frame source for OTel samples** (finding 6, medium). OTel
   carries no project dimension; using `service.name` as `stack[0]`
   collapses all projects per CLI binary. Recommendation: default
   project = `service.name`, overridable via receiver-side config
   (e.g. `--project` flag or a resource-attribute mapping), stated in
   SCHEMA.md.

## Phasing

- **Phase 1:** `/v1/logs` ingestion + gzip; trace-context join;
  `claude_code.*` span/event dialect (aliases incl.
  `cache_creation_tokens`→`cache_write_tokens`); frame-convention
  mapping; README documentation of the `otel` subcommand.
- **Phase 2:** `codex.*`/`gemini_cli.*`/`qwen-code.*` dialects;
  `/v1/metrics`; cost pass-through (×1e6 conversion) + existing-table
  computation + optional user pricing config; golden OTLP JSON
  fixtures per dialect (fixture files only, no live CLIs in tests).
  Live-verify Gemini span nesting and Codex span shape against real
  exports before hardening those dialects.
- **Phase 3 (dropped by default):** per-CLI file adapters, demand-only.

## Draft acceptance criteria (to be anchored at breakdown)

- `bash agentprof/scripts/check.sh` green (existing gate).
- New golden-fixture tests per dialect under `internal/otel/testdata/`
  exercising logs ingestion, trace-context join, frame mapping, and
  micro-USD conversion; test names to be anchored against
  confirmed-absent literals at breakdown time per
  docs/memory/anchored-acceptance-criteria.md.
- `agentprof/README.md` documents the `otel` subcommand (currently
  absent — `grep -c "otel serve" agentprof/README.md` → 0 today).

## Known limitations (accepted, stated)

- Hierarchy depth depends on trace enablement: Claude Code's span tree
  is beta-flagged (working, third-party corroborated, subject to
  change); Codex needs `[otel.trace_exporter]` and has headless/MCP
  gaps; Gemini nesting unverified. Where traces are off, ingestion
  degrades to flat cost-correct samples.
- skillcheck-class content analyses cannot run on OTel data without
  content-logging opt-ins (`OTEL_LOG_USER_PROMPTS=1` etc.); out of
  scope.
- Reprime detection over OTel is a possible future Claude-only port;
  other CLIs lack cache-token granularity. `ctx_usage` exists in no
  OTel signal.
- Data loss while the receiver is down is inherent to the push model;
  spool mitigations reduce but don't eliminate it.
