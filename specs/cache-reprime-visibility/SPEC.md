# agentprof: cache re-prime and context-size visibility

Status: open
Priority: P1
Breakdown-ready: true

## Problem

Cache re-primes are the single largest hidden cost in the 2026-06-27→07-11
agentprof window (see EVIDENCE.md): 915 samples each wrote >60k tokens of
prompt cache in one call — 155 MTok of the window's 409 MTok total cache
writes — with a bundled sample cost of ~$1,713 out of $9,195 total. The
shape is a long-lived session resumed after the cache TTL expired: the
entire accumulated context (observed up to 671k tokens) re-writes at the
1.25× cache-write rate before any work happens. A turn reading "how are we
doing?" cost $2.54 in cache-write alone.

specs/drain-wake-cost attacked the *behavioral* side for drain-shaped
sessions (baton size triggers, doctrine). What's still missing is
*visibility*: nothing in agentprof marks a re-prime, so finding them means
re-running the ad-hoc jq/python spelunking that produced EVIDENCE.md here
and in drain-wake-cost. Context-size economics are similarly invisible —
the window's median session is 2 turns (discipline holds), but the 23
sessions with ≥8 turns and the top-15 sessions ($2.9k, 32% of total spend)
can only be found by hand today.

Mechanically: `internal/claude/claude.go` already emits per-model-call
samples carrying `cache_write_tokens` and a `session` label. NOTE the
emission order: all main-loop responses first (transcript order, with tool
samples interleaved), then each subagent's block appended after
(claude.go:311-342) — the per-session stream is NOT globally
timestamp-ordered, and subagent samples carry the parent's `session`
label. Any "first call" logic must therefore be scoped per transcript
(main-loop vs each agent sidecar), not per session-label. Detecting a
re-prime is still a pure parse-time derivation — no new transcript data
needed.
`internal/costsummary` already rolls samples up into by_project/by_skill/
by_agent_type/by_model buckets, and agent-console's workboard cost panel
(specs/workboard-weekly-cost-view, shipped) renders that summary JSON.

## Solution

Derive a re-prime signal at parse time, roll it up in the cost summary
(counts, tokens, cost, plus per-session context-size stats), and surface
one re-prime line in the existing workboard cost panel. Pure derivation
from data agentprof already parses; thresholds flag-tunable.

## Requirements

- R1 **Re-prime label at parse time.** In `internal/claude`, when a
  MAIN-LOOP model-call sample (stack has no `agent:` frame) is not the
  main loop's first model call in its transcript and its
  `cache_write_tokens` exceeds a threshold (default 50,000; flag
  `--reprime-threshold`), attach label `reprime=true` to the sample.
  Subagent samples are never marked (a fresh worker writing >50k on its
  first call is a cold start, not a re-prime), and the main loop's first
  model call is never marked. Threshold 0 disables the label entirely.
- R2 **Summary rollup.** `--summary` output gains a `reprime` section:
  count of re-prime samples, total cache_write tokens in them, their total
  `cost_microusd`, and a by_project breakdown. Existing sections and field
  names are unchanged (additive only — the workboard panel and any saved
  summaries keep parsing). Under `--merge`, both the `reprime` and
  `sessions` sections aggregate the merged rolling window
  (`forGrouping` in `costsummary.Build`, cmd_claude.go:126-127) like the
  existing buckets — never just the current refresh's samples.
- R3 **Per-session context stats in summary.** `--summary` gains a
  `sessions` section: for each session id, project, calls, total cost, and
  p50/p90 of per-call context size (`cache_read_tokens + input_tokens`
  per call). This makes the long-session tail (≥8 turns, 100k+/call
  contexts) enumerable without raw-JSONL spelunking.
- R4 **Workboard re-prime line.** The agent-console workboard cost panel
  shows one line from the new `reprime` section (count + cost for the
  window), sourced from the same summary JSON refresh path
  specs/workboard-weekly-cost-view shipped. No new endpoint.
- R5 **Docs.** SCHEMA.md documents the `reprime` label and the two new
  summary sections; README gets one example (find your re-primes:
  `-tagfocus reprime=true`).

## Out of scope

- Changing drain/skill behavior to *avoid* re-primes (specs/drain-wake-cost
  owns that; this spec only measures).
- Harness/TTL changes; inferring the actual TTL boundary from timestamps
  (a re-prime is defined by write size, not by proving cache expiry).
- Historical backfill of saved summary JSONs.

## Acceptance criteria

- [ ] `cd agentprof && go test ./...` passes, including a new test fixture
  where a mid-session MAIN-LOOP call writes >50k cache tokens and gets
  `reprime=true`, while the main loop's first call (also >50k write) and a
  subagent's first call (>50k write, same session label) both do not (R1)
- [ ] `agentprof claude --days 7 --summary /tmp/s.json -o /dev/null` (or a
  testdata-driven equivalent) produces a summary whose JSON contains a
  `reprime` key with `count`, `cache_write_tokens`, `cost_microusd`, and
  `by_project`, and a `sessions` key with per-session `p50_ctx`/`p90_ctx`
  (R2, R3)
- [ ] Existing summary consumers unaffected:
  `cd agentprof && go test ./internal/costsummary/` passes with no changes
  to existing field names (R2)
- [ ] `bash agent-console/scripts/check.sh` passes and the workboard cost
  panel template/renderer includes the re-prime line when the summary JSON
  carries the section, omits it gracefully when absent (R4)
- [ ] `grep -qi 'reprime' agentprof/SCHEMA.md && grep -qi 'reprime' agentprof/README.md` (R5)
- [ ] `bash agentprof/scripts/check.sh` green (gofmt, vet, tests)

## Open questions

- Whether p50/p90 context stats should be per-session or per-(session,
  agent) — main-loop context is the cost driver; default to main-loop-only
  samples for the stats, note the choice in SCHEMA.md.

## Parallelization

Task map: 01 = R1 parser label; 02 = R2+R3 summary sections (after 01);
03 = R4 workboard line and 04 = R5 docs both depend on 02 and are
disjoint in Touch (agent-console/ vs agentprof docs) with no shared
undecided design (format grammar per specs/drain-rolling-window/SPEC.md's
Parallelization section).

- Group: 03, 04
