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
  `source`, `model_raw`, `currency`.

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
