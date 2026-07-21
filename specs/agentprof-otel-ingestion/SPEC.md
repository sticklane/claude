# agentprof OpenTelemetry ingestion for coding CLIs

Produced by the 2026-07-21 investigation session. All critic-raised
design decisions were resolved by the maintainer on 2026-07-21 (see
Decisions); scope is pprof-only profiling of OTel data.

## Problem

agentprof profiles agent spend by normalizing session activity into a
canonical sample schema (`agentprof/SCHEMA.md`): timestamp + root-first
stack + values (`input_tokens`, `output_tokens`, `cache_read_tokens`,
`cache_write_tokens`, `cost_microusd`, `calls`, `wall_ms`, `ctx_usage`)

- labels. Its sources are CLI-specific parsers: `claude` (transcripts
  under `~/.claude/projects/`), `antigravity`, `gcp`, `vertex`. We want
  profiling coverage of other coding CLIs (Gemini CLI, Codex, Qwen Code,
  Goose, Copilot, …) without a bespoke parser per CLI. OpenTelemetry is
  the portability layer: most actively-developed coding CLIs export OTLP;
  agentprof should consume it and turn it into pprof profiles.

## Scope (maintainer decision, 2026-07-21)

The OTel path exists to **generate pprof profiles** — canonically
`agentprof otel <trace.json> -o profile.pb.gz` (the `-o *.pb.gz` form
already emits pprof directly today; `agentprof build` is only needed to
merge OTel JSONL with other sources:
`agentprof otel <trace.json> -o s.jsonl && agentprof build s.jsonl -o
profile.pb.gz` — `build` reads positional file paths, not stdin, so a
pipe form is invalid). It does NOT feed `costsummary` — the workboard
cost panel remains claude+antigravity-only. This resolves what samples
the OTel path must produce: raw span-structured stacks for flamegraphs,
not the `project > skill > agent > model` frame convention costsummary
parses.

## Current code state (verified 2026-07-21)

- `agentprof otel` exists: file mode (OTLP/JSON export object or JSONL)
  and `otel serve` (live OTLP/HTTP receiver, default `localhost:4318`,
  JSON + protobuf).
- Traces only: `/v1/traces` registered; `/v1/metrics` and `/v1/logs`
  return 404 (`agentprof/cmd_otel.go:144-145`).
- Stack built as `[service.name, root_span…leaf_span]` from the span
  parent chain (`internal/otel/otel.go:178-232`); model is emitted as a
  label.
- Attribute aliases: `gen_ai.usage.input_tokens` →
  `gen_ai.usage.prompt_tokens`; `gen_ai.usage.output_tokens` →
  `gen_ai.usage.completion_tokens`; `gen_ai.response.model` →
  `gen_ai.request.model`; `gen_ai.system` → `gen_ai.provider.name`.
- `Flush` emits a sample only for spans with token attributes
  (`internal/otel/otel.go:98-113`).
- No cost computation on the otel path. `internal/pricing/` carries a
  Claude table (`table.go`, prefix-matched `claude-*`, snapshot
  2026-07-02) and a Gemini table (`gemini_table.go`, exact-match on a
  single Antigravity display-string key).
- `costsummary.Build` is invoked only from `cmd_claude.go:166`
  (unchanged by this spec — see Scope).
- `agentprof otel <input> -o out.pb.gz` already writes a pprof profile
  directly (`cmd_otel.go:33`; `output.Write` handles `.pb.gz`), so the
  otel→pprof consumer relationship exists today; `agentprof build`
  reads positional file paths only (`cmd_build.go:29`, no stdin).
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
   `input_tokens`, not `gen_ai.usage.input_tokens`), so attribute
   aliasing per dialect is unavoidable.

## Design: two-tier fidelity, trace-first with correlated events

**Tier 1 — high-fidelity native parsers (unchanged).** `claude` and
`antigravity` remain the source for cost rollups and the analyses OTel
cannot carry: `ctx_usage` percentiles, reprime detection, skillcheck's
trigger audit (needs prompt/reply heads, which OTel redacts by
default), untyped-fanout depth. Antigravity has no OTel path at all.

**Tier 2 — portable OTel ingestion → pprof (this spec's scope).**

1. **Traces are the stack backbone; add `/v1/logs` joined on trace
   context.** Extend the receiver and file mode with `/v1/logs`
   (OTLP/JSON + protobuf, gzip). When a log record carries
   `trace_id`/`span_id`, attach its values (notably cost) to the
   correlated span's sample. Log events without trace context degrade
   to flat samples (`[service.name, event name]` stacks) — token/cost
   totals intact, hierarchy absent. Add `/v1/metrics` last as a coarse
   cross-check.
2. **Raw span stacks are the product.** The existing
   `[service.name, root_span…leaf_span]` stack shape is kept: pprof
   flamegraphs should show the CLI's real span structure (e.g.
   `claude_code.interaction` → `claude_code.tool` →
   `claude_code.llm_request`). No canonical frame-convention mapping
   is built; costsummary never parses these samples (see Scope).
   Model stays a label (pprof filtering via `-tagfocus`-style flows).
3. **Attribute aliases per dialect, data-driven.** Detection by
   resource `service.name` and span/event-name prefix
   (`claude_code.*`, `gemini_cli.*`, `qwen-code.*`, `codex.*`; generic
   `gen_ai.*` fallback). Concretely for Claude Code: bare
   `input_tokens` / `output_tokens` / `cache_read_tokens` map to the
   canonical keys, and `cache_creation_tokens` → canonical
   **`cache_write_tokens`** (SCHEMA.md's key; passing the source key
   through verbatim would silently drop cache-write signal in pprof
   token profiles). Alias lists stay data-driven; the semconv is
   pre-stable.
4. **Session label and project frame.** Each dialect maps its session
   identifier (Claude `session.id`, Codex `conversation.id`, …) into
   `labels["session"]` for pprof tag filtering. `stack[0]` stays
   `service.name` (default project identity), with an optional
   receiver-side override (e.g. `--project`) as a nicety — sufficient
   for pprof scope since costsummary project attribution is not in
   play.
5. **Cost: prefer emitted, else compute where a table matches, else
   tokens-only.** Use an explicit cost attribute when present
   (Claude's `cost_usd`, fractional USD — convert to integer
   `cost_microusd` by ×1e6 and round). Cost-from-tokens via
   `internal/pricing/` is **Claude-only today**: the Claude table
   prefix-matches API model IDs, but the Gemini table is an exact-map
   lookup keyed on Antigravity display strings (single entry), which
   OTel's `gen_ai.response.model` API IDs never hit — Gemini stays
   tokens-only (Decision 6). Do NOT add new baked vendor tables
   (maintenance treadmill); at most accept a user-supplied pricing
   config for other dialects.
6. **Cost join semantics (Decision 4).** Relax the `Flush` gate: emit
   a sample for spans with tokens OR attached cost. If a cost event's
   `span_id` targets a frames-only ancestor (e.g. the `interaction`
   span), attach the cost to the token-bearing descendant whose span
   time range contains the event timestamp; if several qualify,
   earliest span start wins; if none contains it, use the latest
   token-bearing descendant that started before the event. Golden
   fixtures cover single- and multi-descendant cases against this
   rule. Verifying which span `span_id` actually targets in real
   emissions requires a live Claude Code capture — an explicit
   manual-pending step filed in `HUMAN.md`; fixture-based hardening
   proceeds without it.
7. **Durability/spool.** OTel is prospective-only: the receiver must be
   running while sessions happen, unlike retrospective transcript
   parsing. Mitigations, documented not built: Gemini/Qwen telemetry
   `outfile` → file mode; OTel Collector `fileexporter` JSONL → file
   mode. gRPC-only emitters: document
   `OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf` (all target CLIs
   support OTLP/HTTP) instead of adding a 4317 gRPC listener.
8. **TRACEPARENT stitching for fleets (opportunity, not core).** An
   orchestrator setting `TRACEPARENT` on spawned workers yields one
   cross-process delegation trace; the pprof profile then shows worker
   spend under the orchestrator frame. Candidate later integration:
   drain/fleet dispatch templates exporting trace context.
9. **No bespoke file parsers for no-OTel CLIs.** Rejected as a
   treadmill against undocumented, churning formats. Build one only on
   demonstrated demand.

## Decisions (resolved by maintainer, 2026-07-21)

1. **Frame mapping** — not built. OTel is a pprof source; raw span
   stacks are the desired output ("otel should be used to generate
   pprof"). Resolves critic round-1 finding 1 by scoping.
2. **costsummary wiring** — no. OTel samples are pprof-only; the
   workboard cost panel stays claude+antigravity. Resolves round-1
   finding 2.
3. **Tier 1/Tier 2 double-counting** — moot under Decision 2: OTel
   samples never enter merged cost rollups, and pprof profiles are
   built per-source invocation. Resolves round-1 finding 3.
4. **Log→span cost join** — relaxed gate + timestamp-containment
   descendant rule (design pt 6 states the multi-descendant
   tie-break), with live-capture verification as a manual-pending
   step. Resolves round-1 finding 4; tie-break refined after round 3.
5. **Project frame** — `service.name` default, optional override flag
   (design pt 4). Resolves round-1 finding 6.
6. **Gemini cost-from-tokens** — tokens-only; no model-ID→table-key
   normalization until Gemini cost is actually wanted. Resolves
   round-2 finding 1.

## Phasing

- **Phase 1:** `/v1/logs` ingestion + gzip; trace-context join with the
  relaxed flush gate; `claude_code.*` span/event aliases (incl.
  `cache_creation_tokens`→`cache_write_tokens`); cost attach with
  ×1e6 micro-USD conversion; README documentation of the `otel`
  subcommand.
- **Phase 2:** `codex.*`/`gemini_cli.*`/`qwen-code.*` dialects;
  `/v1/metrics`; cost-from-tokens via the Claude table for token-only
  Claude-model samples; optional user pricing config; golden OTLP JSON
  fixtures per dialect (fixture files only, no live CLIs in tests).
  Live-verify Gemini span nesting and Codex span shape against real
  exports before hardening those dialects — like the Claude cost-join
  capture, these are human-run manual-pending steps
  (docs/memory/unattended-worker-tool-limits.md), not gates on
  drained tasks.
- **Phase 3 (dropped by default):** per-CLI file adapters, demand-only.

## Draft acceptance criteria (to be anchored at breakdown)

- `bash agentprof/scripts/check.sh` green (existing gate).
- New golden-fixture tests under `internal/otel/testdata/` exercising:
  logs ingestion (JSON + protobuf), trace-context cost join incl. the
  frames-only-ancestor fallback and the multi-descendant timestamp
  tie-break, the relaxed flush gate, dialect
  aliasing (`cache_creation_tokens`→`cache_write_tokens`), and
  micro-USD conversion; test names to be anchored against
  confirmed-absent literals at breakdown time per
  docs/memory/anchored-acceptance-criteria.md.
- `agentprof/README.md` documents the `otel` subcommand (currently
  absent — `grep -c "otel serve" agentprof/README.md` → 0 today).

## Known limitations (accepted, stated)

- OTel sources are excluded from the workboard cost panel by design
  (Decision 2); cross-CLI spend comparison happens in pprof, not the
  cost rollups.
- Hierarchy depth depends on trace enablement: Claude Code's span tree
  is beta-flagged (working, third-party corroborated, subject to
  change); Codex needs `[otel.trace_exporter]` and has headless/MCP
  gaps; Gemini nesting unverified. Where traces are off, ingestion
  degrades to flat token/cost-correct samples.
- skillcheck-class content analyses cannot run on OTel data without
  content-logging opt-ins (`OTEL_LOG_USER_PROMPTS=1` etc.); out of
  scope.
- Reprime detection over OTel is a possible future Claude-only port;
  other CLIs lack cache-token granularity. `ctx_usage` exists in no
  OTel signal.
- Data loss while the receiver is down is inherent to the push model;
  spool mitigations reduce but don't eliminate it.
