# agentprof

pprof profiles for AI-agent token & spend attribution. `agentprof` captures a
window of activity — Claude Code transcripts, GCP billing exports, or any
app's own telemetry — as a genuine pprof protobuf profile (`.pb.gz`), so all
existing pprof tooling answers "where did the tokens/money go?": `-top`,
flame graphs, `-diff_base`, `--focus`, `-tagfocus`.

```
sources                adapters                  core                viewers
~/.claude JSONL  ──▶  agentprof claude  ──┐
bq billing JSON  ──▶  agentprof gcp     ──┼──▶ samples.jsonl ──▶ agentprof build ──▶ profile.pb.gz ──▶ go tool pprof
bq vertex logs   ──▶  agentprof vertex  ──┤
any app          ──▶  writes schema     ──┘
```

Stack frames are the attribution hierarchy (for Claude Code:
`project > skill > agent > model`), sample values are the metrics
(token counts, cost in micro-USD, call count), and pprof labels are the
dimensions you filter by rather than stack on (`session`, `source`,
`model_raw`, `currency`).

## Install

From a checkout of this repo (requires Go):

```sh
go build -o agentprof .
```

## Quickstart: profile a week of Claude Code

```sh
./agentprof claude --days 7 -o week.pb.gz && go tool pprof -http=:8080 week.pb.gz
```

This reads `~/.claude` (read-only), prices every assistant API response with
the built-in pricing table, and opens the pprof web UI — the Flame Graph view
reads like a CPU profile of your week: conversation turns are frames under
each project, and subagents nest under the turn (and agent) that spawned
them. Stacks look like:

```
main line:         [fooszone, t03 · /parallel specs/agentprof, parallel, main, claude-fable-5]
depth-1 subagent:  [fooszone, t03 · /parallel specs/agentprof, parallel, main, agent:general-purpose, claude-fable-5]
depth-2 subagent:  [fooszone, t03 · /parallel specs/agentprof, parallel, main, agent:general-purpose, agent:scout, claude-haiku-4-5]
workflow subagent: [fooszone, t03 · /parallel specs/agentprof, parallel, main, wf:review-changes, agent:workflow-subagent, claude-fable-5]
```

Workflow-spawned subagents all share the agentType `workflow-subagent`, so
they additionally get a `wf:<workflowName>` frame (once per spawn chain,
inherited by any agents the workflow agent spawns) to keep distinct workflows
apart in the flame graph. Subagents whose spawn linkage can't be resolved
(e.g. a missing meta file, or a workflow run that never appears in the
transcript) land under an `(unlinked)` frame instead of a turn.

Agent frames appear in two forms — bare (`agent:verifier`) and
plugin-namespaced (`agent:agentic:verifier`) — and both are the *same*
logical agent; the difference records where Claude Code resolved the
definition from. A bare name means the agent was dispatched from a
**repo-local `.claude/agents/` definition** (the norm in a checkout that
carries its own `scout`/`verifier`/`critic`/`implementation-worker` files,
such as the toolkit's dev checkout); the `agentic:` prefix means the same
agent was served by the installed **`agentic` plugin**, whose namespace the
transcript records verbatim. The adapter passes `agentType` straight through
(`agent:` + agentType) with no normalization, so — unlike skill frames, which
strip the plugin namespace so `agentic:build` and `build` collapse into one —
agent frames keep theirs, and the two dispatch sources stay distinguishable.
So expect bare frames from sessions whose cwd is a checkout with its own
`.claude/agents/`, and prefixed frames from every other repo dispatching via
the plugin; it is an attribution nuance, not a defect. For a
terminal summary:

```sh
go tool pprof -top week.pb.gz
```

The default metric is `cost_microusd` (1,000,000 = $1).

> **Note:** `-top`'s default node-fraction pruning
> hides small `tool:` frames unless you pass `-nodefraction=0 -edgefraction=0`
> (or narrow the window with `--days` or a `--focus` project filter) — so a
> missing `tool:` frame on a day-scale profile reads as pruning, not a broken
> feature.

## Switching metrics

One profile carries every metric; `-sample_index` picks which one to view:

```sh
go tool pprof -top -sample_index=output_tokens week.pb.gz
```

Claude Code profiles carry `cost_microusd`, `input_tokens`, `output_tokens`,
`cache_read_tokens`, `cache_write_tokens`, and `calls`. List the indexes for
any profile with `go tool pprof -raw week.pb.gz | head`.

## Slicing

Sessions are labels, not stack frames — flame graphs aggregate across
sessions, and `-tagfocus` slices one out. List label values, then focus
(label filters take regexps, so a session-id prefix works):

```sh
go tool pprof -tags week.pb.gz
go tool pprof -top -tagfocus 'session=7c576eff' week.pb.gz
```

Main-line and linked-subagent samples also carry a `turn` label (the
zero-padded turn ordinal; `(unlinked)` subagents have none), so one turn of
one session isolates with pprof's keyless `key:value` tagfocus form — each comma-separated regex matches against `key:value`:

```sh
go tool pprof -top -tagfocus 'session:7c576eff,turn:03' week.pb.gz
```

(The `session=...,turn=...` form does NOT work here — it ORs both strings
against the `session` key only.)

Other useful label filters: `-tagfocus priced=false` finds spend on models
the pricing table doesn't recognize; `-tagfocus source=gcp` isolates one
source in a mixed profile (below).

The `agentprof claude` adapter labels prompt-cache re-primes — non-first
main-loop calls whose cache write exceeds `--reprime-threshold` (default
50000) — with `reprime=true`, so a single tagfocus finds every re-prime and
what it cost:

```sh
go tool pprof -tagfocus reprime=true week.pb.gz
```

A session's first call and every subagent cold start are never marked (a
fresh cache is not a re-prime); [SCHEMA.md](SCHEMA.md)'s "The `reprime` label"
section has the full rule.

`--focus` filters by stack frame instead — e.g. only samples under one
project:

```sh
go tool pprof -top --focus fooszone week.pb.gz
```

## Diffing two windows

`-diff_base` subtracts one profile from another. For example, capture the
last 30 days and subtract the last 7 to see what the older 23 days cost:

```sh
./agentprof claude --days 30 -o month.pb.gz
go tool pprof -top -diff_base=week.pb.gz month.pb.gz
```

Keep dated snapshots (`agentprof claude --days 7 -o 2026-07-02.pb.gz` from
cron, say) and `-diff_base` compares any two of them.

## Turn frames: secret scrubbing and naming

Turn frames are prompt snippets, and prompts sometimes contain pasted
credentials. Secret-shaped substrings are always replaced with `[redacted]`
before any prompt text reaches a profile, across three shape classes:

- **Known token prefixes** — `sk-`, `cfut_`, `ghp_`, `gho_`, `github_pat_`,
  `xoxb-`, `xoxp-`, `AKIA`, `ya29.`, `AIza`, `eyJ` — followed by 8+ token
  characters, matched only where the prefix starts a token run.
- **Mixed-case long runs** — any 24+-character `[A-Za-z0-9_-]` run that mixes
  digits, uppercase, and lowercase.
- **Keyword-gated hex** — a 24+-character hex run (`[0-9a-fA-F]`), redacted
  only when a secret keyword — `token`, `key`, `secret`, `password`,
  `bearer`, `credential`, or `api-key`/`api_key`, matched on a word boundary,
  case-insensitively — appears in the 40 bytes immediately before it. This
  catches all-lowercase hex API tokens, which the mixed-case rule misses,
  while leaving git SHAs and UUIDs in prose readable.

The keyword gate is a deliberate over-redaction trade-off: a hex string
labeled like a secret is redacted even when it is harmless, but an unlabeled
hex string — a git SHA or UUID sitting in prose with no keyword in its
preceding window — stays readable. That is the git-SHA carve-out: UUIDs, git
SHAs, model ids, and kebab-case slugs are not matched by shape alone.

Residual risk: a bare hex paste with no secret keyword nearby is
unredactable by shape — it is indistinguishable from a SHA — so shape-based
scrubbing cannot catch it. Mitigate this operationally: rotate any credential
that reaches a profile, keep raw secrets out of prompts in the first place
(paste hygiene), and add known-sensitive identifiers to the frame denylist
(below) so they are stripped regardless of shape.

Some frames are still uninformative (`t01 · done`, `t04 · [redacted]`).
`--name-turns` renames those — prompts of at most 4 words that aren't slash
commands, plus any frame showing `[redacted]` — to a short model-written
description like `t01 · fix flaky auth test`:

```sh
./agentprof claude --days 7 --name-turns -o week.pb.gz
```

Cost model: at most one `claude -p --model haiku` subprocess call per run,
batching only the turns not already cached. Accepted names live in
`${XDG_CACHE_HOME:-$HOME/.cache}/agentprof/turn-names.json`, keyed by prompt
content, so a run resolving fully from cache makes no subprocess call and is
byte-identical across reruns. The subprocess gets a scratch
`CLAUDE_CONFIG_DIR` under the same cache directory, so naming sessions never
appear in the `~/.claude` tree being profiled. Any naming failure (CLI
absent, timeout, malformed reply) keeps the snippet frames and prints one
stderr warning; informative frames and stack shape are never touched, and
without the flag output is unchanged.

## Frame denylist

Secret scrubbing (above) only catches token-shaped strings in prompt text. It
does not hide named identifiers you simply don't want in a shared profile —
the clearest example is a private skill's name, which flows into a `skill:`
frame straight from frame normalization, bypassing the prompt scrub entirely.
The frame denylist closes that gap.

If `~/.config/agentprof/frame-denylist` exists, it is read as one denied
substring per line (blank lines ignored). At sample-emit time, **every**
emitted frame string — project, turn, skill, agent, role/stage markers, and
model — is checked, and any frame containing a listed substring is replaced
wholesale with `(redacted)`. Point `--frame-denylist` at another path to
override the location:

```sh
./agentprof claude --days 7 --frame-denylist ./my-denylist -o week.pb.gz
```

With no denylist file present, output is unchanged. The denylist file itself
is **never committed** — it names the very strings you are trying to keep out
of shared artifacts, so it lives only on your machine.

**Pinned-evidence repo rule.** Any evidence profile committed under `specs/`
in this repository MUST be generated with the frame denylist active, so that
no private skill, project, or agent name is baked into a checked-in profile.
When you pin a profile as evidence, run the emit with `--frame-denylist`
pointing at your local denylist and confirm the redactions landed before
committing.

## Attribution normalization

The `agentprof claude` adapter normalizes a few frame and sample shapes so the
attribution hierarchy stays stable across machines and transcript quirks:

- **Skill frames from typed slash commands.** A turn's `skill:` frame normally
  comes from the transcript's `attributionSkill`. When that field is absent, the
  adapter falls back to the turn's `<command-name>` tag — a typed `/parallel`
  becomes `skill:parallel` (the plugin namespace is stripped, as with any skill
  frame). Built-in commands are excluded and stay `(no skill)`: `/clear`,
  `/model`, `/reload-plugins`, `/rate-limit-options`.
- **Project normalization.** The project frame (stack root) is normalized, not
  taken verbatim from the cwd basename: a session run from the home directory
  frames as `(home)` (never the home basename), an `mktemp`-shaped scratch dir
  (`tmp.<suffix>`) frames as `(tmp)`, and an agent sidecar directory is folded
  into its owning worktree or dropped — sidecar dirs are never projects. Home is
  resolved from `AGENTPROF_HOME` when set (falling back to the OS home dir), so
  hermetic tests can pin it independent of the machine.
- **Pending tool calls.** A `tool_use` block with no matching `tool_result`
  can't be given a duration, so unmatched calls in a response aggregate into a
  single `tool:(pending)` sample carrying a `pending_calls` count instead of one
  duration-less sample per call. The `--keep-pending` flag (library option
  `Options.KeepPending`) restores the old behavior (one `tool:(pending)` sample
  per unmatched call). Real runs report the unmatched-call count on stderr.

Duration-only tool samples (matched and pending alike) have no model leaf — the
model slot holds the `tool:` frame — so they aggregate under the cost-summary
`(tools)` bucket rather than any model; see [SCHEMA.md](SCHEMA.md)'s `by_model`
notes.

## GCP billing

`agentprof gcp` ingests a file of GCP billing standard-export rows as
produced by `bq query --format=json`; it makes no network or gcloud calls
itself. Export with exactly this query shape — **select the whole `project`,
`service`, and `sku` structs**:

```sql
SELECT project, service, sku, usage_start_time, cost, currency
FROM <billing_export_table>
WHERE usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
```

As a one-liner (substitute your billing export table, e.g.
`` `myproj.billing.gcp_billing_export_v1_XXXXXX` ``):

```sh
bq query --nouse_legacy_sql --format=json 'SELECT project, service, sku, usage_start_time, cost, currency FROM <billing_export_table> WHERE usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)' > billing.json
```

> **Warning:** do NOT select dotted subfields (`project.id`,
> `service.description`, `sku.description`). bq flattens them to colliding
> keys (`description`, `description_1`, …) and the rows become ambiguous.
> Select the whole structs; the adapter reads the nested shape (and also
> accepts aliased flat keys `project_id`, `service_description`,
> `sku_description`). String-encoded numerics (`"cost": "1.5"`) and
> bq's `YYYY-MM-DD HH:MM:SS` timestamps are handled.

Then build and view (stacks are `project > service > SKU`; a runnable sample
export ships in `testdata/`):

```sh
./agentprof gcp testdata/gcp-billing.json -o gcp.pb.gz
go tool pprof -top gcp.pb.gz
```

Rows with a missing required field or negative cost (credits) are skipped
and counted on stderr. Currency passes through as a `currency` label — no
conversion.

### Label frames

`--frame-labels k1,k2` inserts one `key:value` frame per requested key after
the project frame, in flag order (add `labels` to the SELECT above to export
them):

```sh
./agentprof gcp --frame-labels team testdata/gcp-billing.json -o gcp.pb.gz
```

Stacks become `project > team:vision > service > SKU`; rows lacking a key
(or with an unusable `labels` field) get `team:(none)` rather than being
dropped. This is how Vertex AI spend gets a semantic dimension: labels set on
`generateContent` requests (the `labels` request field) propagate into the
billing export's `labels` column, so tagging calls in code (`team`,
`feature`, `pipeline`, …) makes them first-class frames here.

## Vertex AI request-response logs

`agentprof vertex` ingests rows from the Vertex AI request-response logging
table — enable request-response logging on your Gemini / Claude-on-Vertex
usage and every `generateContent` / `rawPredict` call lands in a BigQuery
table with the full response body, including per-request token counts,
within minutes (versus the billing export's daily, SKU-level lag). Export
the table with `bq` and feed the file in:

```sh
bq query --nouse_legacy_sql --format=json 'SELECT * FROM mydataset.request_response_logging WHERE logging_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)' > vertex.json
./agentprof vertex vertex.json -o vertex.pb.gz
go tool pprof -top -sample_index=input_tokens vertex.pb.gz
```

Stacks are `project > location > model > method` (e.g. `proj-vertex >
us-central1 > gemini-2.0-flash > GenerateContent`), and each row carries its
token counts (`input_tokens`, `output_tokens`, cache metrics when present)
plus `calls`. Both Gemini-shaped (`usageMetadata`) and Anthropic-shaped
(`usage`) response bodies are recognized, per row; streaming calls read
usage from the final response chunk. Claude models are priced with the
built-in pricing table (`claude-sonnet-4@20250514` and friends resolve to
their dated rates) and labeled `priced=true` with `cost_microusd`; Gemini
and other unrecognized models keep their token counts and are labeled
`priced=false` with no cost metric. No prompt or response text ever appears
in frames or labels. Rows without a parseable `logging_time` or usage data
are skipped and counted on stderr. A runnable sample export ships in
`testdata/vertex-logs.json`.

## OpenTelemetry traces

`agentprof otel` turns an OpenTelemetry (OTel) trace export into a pprof
profile. Coding CLIs that emit OTLP — Claude Code, Codex, Gemini CLI, and Qwen
Code — record each LLM request as a span carrying its token counts, and
agentprof reads that span tree into `[service.name, root_span…leaf_span]`
stacks with the model as a label. Point it at an OTLP/JSON export file:

```sh
./agentprof otel trace.json -o otel.pb.gz
go tool pprof -top -sample_index=input_tokens otel.pb.gz
```

The input is a single OTLP/JSON trace-export object, or JSONL of such objects
as written by the OpenTelemetry Collector's `fileexporter`. Logs-export
objects are accepted in the same stream, so a Collector file that mixes traces
and cost-bearing log events feeds straight in. Only spans carrying a
recognized token attribute — `input_tokens`, `output_tokens`,
`cache_read_tokens`, `cache_creation_tokens`, or their `gen_ai.usage.*`
semantic-convention aliases — become samples; the rest are skipped and counted
on stderr. To merge OTel spend with other sources, write JSONL instead of
`.pb.gz` and hand the file to `agentprof build`; `build` reads positional file
paths, so there is no pipe form:

```sh
./agentprof otel trace.json -o otel.jsonl
./agentprof build otel.jsonl claude.jsonl -o all.pb.gz
```

A span is attributed to a CLI by its span-name prefix (`claude_code.`,
`codex.`, `gemini_cli.`, `qwen-code.`), and the matched dialect fixes which
attribute carries the session id — `session.id` for Claude Code, Gemini CLI,
and Qwen Code; `conversation.id` for Codex — surfaced as the `session` label. A
`gen_ai.*` service that matches no prefix still profiles: it falls back to a
generic session key with no dialect label.

Claude Code reports dollar cost on a separate `claude_code.api_request` log
event rather than on the span. When a cost-bearing log record (`cost_usd`, or
the `gen_ai.usage.cost` alias) shares a trace and span id with a span, its cost
joins that span's sample as `cost_microusd` (`round(cost_usd × 1e6)`); a cost
record with no trace context degrades to a flat `[service, event-name]` sample.
For non-Claude dialects that report tokens but no cost, `--pricing` supplies a
rate table — a JSON file whose `models` array prefix-matches model ids to
per-million-token USD prices:

```json
{"models": [{"prefix": "gemini-2.5", "input": 1.25, "output": 10, "cache_read": 0.31, "cache_write": 1.625}]}
```

```sh
./agentprof otel trace.json --pricing rates.json -o otel.pb.gz
```

Entries are matched in list order, first match wins, so list a more specific
prefix before a shorter one it overlaps. Claude models are always priced from
the built-in table regardless of `--pricing`.

Because OTel is prospective — a trace exists only while a session runs and
exports it — `otel serve` runs a live OTLP/HTTP receiver so you can capture as
sessions happen instead of exporting a file afterward:

```sh
./agentprof otel serve --addr localhost:4318 -o session.pb.gz
```

It listens on `localhost:4318` by default and accepts `/v1/traces`,
`/v1/logs`, and `/v1/metrics` in JSON or protobuf, transparently
decompressing gzip request bodies (`Content-Encoding: gzip`). Point a CLI's
OTLP/HTTP exporter at it, run your sessions, then stop the receiver with
Ctrl-C: it drains in-flight requests, flushes the accumulated spans to `-o`
(required for `serve`), and reports the sample count on stderr. Traces build
the profile and correlated log events add cost; `/v1/metrics` is decoded only
as a coarse cross-check total and never overrides a trace sample.

The OTel path produces pprof profiles for flamegraph analysis only — it does
not feed `costsummary` or the workboard cost panel, which stay Claude- and
Antigravity-sourced. Its samples are raw span-structured stacks, not the
`project > skill > agent > model` frames costsummary parses.

A live receiver misses any session that runs while it is down. Two file-mode
spool paths close that gap: Gemini CLI and Qwen Code can write telemetry to a
local `outfile`, and an OpenTelemetry Collector can persist batches through its
`fileexporter` — feed either file to `agentprof otel` afterward. For an emitter
that speaks only gRPC, set `OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf` (every
target CLI supports OTLP/HTTP) rather than expecting a 4317 gRPC listener;
`otel serve` is HTTP-only.

## Mixed-source profiles

`agentprof build` merges any number of canonical-schema JSONL files into one
profile. Adapters emit JSONL when `-o` doesn't end in `.pb.gz`:

```sh
./agentprof claude --days 7 -o claude.jsonl
./agentprof gcp testdata/gcp-billing.json -o gcp.jsonl
./agentprof build claude.jsonl gcp.jsonl -o all.pb.gz
go tool pprof -top all.pb.gz
```

Metric keys are unioned: `-sample_index=cost_microusd` (the default)
compares sources on the shared cost metric, and token metrics exist with 0
for GCP samples. Sources stay separated by the `source` label, not by stack
namespacing:

```sh
go tool pprof -top -tagfocus source=gcp all.pb.gz
```

## Profiling your own app: the canonical schema

Any app in any language is profiled by writing one JSON object per line in
the `agentprof/v1` schema and running it through `agentprof build`. The full
contract — field rules, well-known metric units, validation/skip rules — is
[SCHEMA.md](SCHEMA.md). The shape:

```json
{
  "time": "2026-07-02T18:04:11Z",
  "stack": [
    "fooszone",
    "t03 · /build specs/turns",
    "/build",
    "main",
    "agent:scout",
    "claude-haiku-4-5"
  ],
  "values": {
    "input_tokens": 10101,
    "output_tokens": 1560,
    "cache_read_tokens": 18118,
    "cache_write_tokens": 14266,
    "cost_microusd": 41230,
    "calls": 1
  },
  "labels": { "source": "claude-code", "session": "7c576eff-..." }
}
```

- `time`: RFC3339, required.
- `stack`: non-empty array of strings, required, **root first**; the last
  element is the pprof leaf.
- `values`: metric name → non-negative integer. Well-known units: `*_tokens`
  → `tokens`, `cost_microusd` → `microusd`, `wall_ms` → `milliseconds`,
  `duration_ms` → `milliseconds`, `calls` → `count`; unknown metric names get
  unit `count`.
- `labels`: optional string → string map; becomes pprof string labels.

Invalid lines are skipped and counted (`skipped N invalid lines` on stderr),
never fatal — unless a file yields zero valid samples. Try it with the
bundled sample (2 of its 6 lines are deliberately invalid):

```sh
./agentprof build testdata/samples-custom.jsonl -o custom.pb.gz
go tool pprof -top custom.pb.gz
```

## Auditing skill triggers and outcomes

`agentprof skillcheck` is a read-only report, not a profile adapter: instead
of pricing token spend it reads this machine's Claude Code transcripts and
audits how a skill actually got used. For every `Skill` tool invocation it
finds, it classifies whether the trigger was a correct model auto-trigger or
a misfire, judges whether correctly-triggered runs reached a successful
outcome, and flags user turns that read like a skill should have fired but
didn't. A skill author reads the per-skill trigger-accuracy and
outcome-success counts while iterating on a `SKILL.md`'s `description` and
body — the same window the cost report gives on spend.

```sh
./agentprof skillcheck --days 7 --format table
```

Explicit slash-command invocations and skill self-chains are counted but
never scored as correct or misfired — only model auto-triggers carry a
trigger verdict. Outcome grading runs a `claude -p` judge subprocess;
`--judge-tier` picks its model (`scout` by default, `deep`, or `frontier`),
and each judge call gets an isolated `CLAUDE_CONFIG_DIR` so grading never
writes into the `~/.claude` tree being audited. `--skill NAME` restricts the
report to one skill; `--format json` (the default) emits the full per-skill
aggregate with a transcript citation on every finding.

## Commands

| Command                                                                   | What it does                                                               |
| ------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `agentprof claude [--claude-dir PATH] [--days N \| --since RFC3339] [--merge cache.jsonl] [--summary costs.json] [--name-turns] [--reprime-threshold N] [--keep-pending] [--frame-denylist PATH] [-o out]` | Claude Code transcripts → samples. Defaults: `~/.claude`, 30 days (`--since` is the mutually-exclusive absolute cutoff), `--reprime-threshold 50000` (0 disables), denylist `~/.config/agentprof/frame-denylist`, stdout. `--merge` keeps a 7-day rolling JSONL cache; `--summary` writes the pre-aggregated Cost JSON the workboard panel reads; `--keep-pending` keeps one `tool:(pending)` sample per unmatched tool call instead of consolidating them. |
| `agentprof gcp <billing.json> [--frame-labels k1,k2] [-o out]`            | GCP billing export rows → samples.                                         |
| `agentprof vertex <logs.json> [-o out]`                                   | Vertex AI request-response logging rows → samples.                         |
| `agentprof otel <trace.json> [--pricing config.json] [-o out]`            | OTLP/JSON trace export (or Collector JSONL) → samples.                      |
| `agentprof otel serve [--addr localhost:4318] [--pricing config.json] -o out` | Live OTLP/HTTP receiver (`/v1/traces`, `/v1/logs`, `/v1/metrics`; JSON, protobuf, gzip) → samples on Ctrl-C. |
| `agentprof build <samples.jsonl>... -o out.pb.gz`                         | Canonical-schema JSONL → pprof profile.                                    |
| `agentprof skillcheck [--claude-dir PATH] [--days N \| --since RFC3339] [--skill NAME] [--judge-tier scout\|deep\|frontier] [--format json\|table] [-o out]` | Claude Code transcripts → per-skill skill-trigger and outcome audit (read-only; emits a report, not a profile). |
| `agentprof --version`                                                     | Print version.                                                             |

For all adapters, an `-o` path ending `.pb.gz` writes the pprof profile
directly; any other path (or stdout) emits canonical-schema JSONL.

Pricing for Claude models lives in a built-in table
(`internal/pricing/pricing.go`, rates from
<https://docs.claude.com/en/docs/about-claude/pricing>). Messages from
unrecognized models keep their token counts, get `cost_microusd: 0`, and are
labeled `priced=false` so unpriced spend is findable.
