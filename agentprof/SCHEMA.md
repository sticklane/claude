# Canonical sample schema (`agentprof/v1`)

The genericity contract of agentprof: any app in any language can be profiled
by emitting one JSON object per line (`.jsonl`) in this schema, then running
`agentprof build samples.jsonl -o profile.pb.gz`. Adapters (`agentprof
claude`, `agentprof gcp`) are just producers of this schema.

A versioned `"schema": "agentprof/v1"` marker is allowed on any line but not
required.

## Example

```json
{
  "time": "2026-07-02T18:04:11Z",
  "stack": ["fooszone", "/build", "agent:scout", "claude-haiku-4-5"],
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

## Fields

- `time`: RFC3339 timestamp, **required**. Profiles derive `time_nanos` /
  `duration_nanos` from the min/max sample time, never the wall clock.
- `stack`: non-empty array of strings, **required**, **root first** — the
  attribution hierarchy. The last element is the pprof leaf. For Claude Code:
  `project > skill > agent > model`.
- `values`: map of metric name → **non-negative integer**. Fractional values
  are invalid (encode money as micro-USD, time as milliseconds). Metric keys
  are unioned across all samples in a profile; a sample missing a metric
  contributes 0 for it.
- `labels`: **optional** map of string → string; becomes pprof string labels —
  dimensions you filter by (`-tagfocus`) rather than stack on, e.g. `session`,
  `source`, `model_raw`, `currency`, `reprime`.

## The `reprime` label

The `agentprof claude` adapter marks samples that re-primed the prompt cache
with the pprof label `reprime=true`. A sample earns the mark when it is a
main-loop model call, **past the session's first call**, whose
`cache_write_tokens` exceeds `--reprime-threshold` (default 50000; a threshold
of 0 disables the labeling). Re-priming is the per-turn cost of rebuilding a
prompt cache that lapsed between calls, so isolating these samples shows where
a session paid to re-warm its cache.

Two calls are deliberately never marked, because neither is a *re*-prime:

- a session's **first** main-loop call — its cache is cold by definition, so
  the initial write is priming, not re-priming;
- any **subagent** call — a subagent's cold start is a fresh cache, not a
  re-prime of the parent's.

The label only ever takes the value `"true"`; unmarked samples carry no
`reprime` key at all, so `-tagfocus reprime=true` selects exactly the
re-primes (README's "Slicing" section has the worked query).

## Cost-summary sections: `reprime` and `sessions`

Alongside the profile, `agentprof` emits a pre-aggregated "Cost (7d)" summary
JSON (consumed by the workboard cost panel). Two of its sections roll up the
views the `reprime` label and main-loop attribution make possible:

- `reprime` — the re-prime rollup over every sample labeled `reprime=true`:
  `count` (how many), `cache_write_tokens` (prompt cache re-written),
  `cost_microusd` (what those re-primes cost), and `by_project` (the same
  `{count, cache_write_tokens, cost_microusd}` broken out per project).
- `sessions` — one entry per session, keyed by session id, each a context-size
  profile: `project`, `calls`, `cost_microusd`, and the per-call context-size
  percentiles `p50_ctx` / `p90_ctx` (context measured as
  `cache_read_tokens + input_tokens`).

`p50_ctx` / `p90_ctx` are computed over that session's **main-loop model calls
only** — subagent calls carry the parent's `session` label but are excluded
from the percentiles. Main-loop context is the cost driver a growing session
pays for on every turn; folding a subagent's small, independent context into
the numbers would mask how heavy the main line itself has become.

## Well-known metrics and pprof units

| Metric name     | pprof unit     |
| --------------- | -------------- |
| `*_tokens`      | `tokens`       |
| `cost_microusd` | `microusd`     |
| `wall_ms`       | `milliseconds` |
| `duration_ms`   | `milliseconds` |
| `calls`         | `count`        |
| anything else   | `count`        |

Unknown metric names are allowed (unit `count`). When `cost_microusd` is
present it is the profile's default sample type and sorts first; remaining
sample types appear in sorted order.

## Validation (skip rules)

Readers skip a line — counting it, never failing — when any of these hold:

- the JSON is malformed;
- `stack` is missing, empty, or contains non-strings;
- any value in `values` is negative or not an integer (`1.5` is rejected,
  `1560` passes);
- `time` is missing or not RFC3339;
- the line is blank (skipped and counted like any other invalid line).

`agentprof build` reports the total on stderr as `skipped N invalid lines`
and exits 0 unless zero valid samples were read.
