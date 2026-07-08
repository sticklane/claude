# Task 04 evidence — refresh-profile.sh wiring + real-binary end-to-end

Run attended (2026-07-08), with user approval to restart the live
`com.agent-console` launchd service (PID 961 → 90797) so it picked up this
session's merged code.

## Bug found and fixed en route

`refresh-profile.sh`'s pre-existing `mktemp "$STATE_DIR/.claude-30d.XXXXXX.pb.gz"`
pattern (and the equivalent I initially wrote for the new weekly step) does
NOT randomize on macOS/BSD `mktemp` when the `X`'s are followed by a static
suffix — it silently returns the literal, colliding filename. A second run
(or the live server's subprocess invocation) then fails with
`mktemp: mkstemp failed ...: File exists`. Fixed for both the pre-existing
30d step and the new weekly step: generate suffix-free (`mktemp ".../.foo.XXXXXX"`),
then rename to add the extension. Verified: `mktemp "/tmp/.test.XXXXXX.pb.gz"`
returns the literal template unchanged; `mktemp "/tmp/.test.XXXXXX"` returns
a properly randomized name.

## Acceptance evidence

**Criterion 1 — steady-state / empty-delta path (R4):**
`bash agentprof/scripts/refresh-profile.sh` run twice back-to-back after the
mktemp fix: both exits 0, no `mktemp` collision. The script's own
`--since <mtime>`-derived window cannot show a literal zero-delta while run
against THIS live, currently-running session (every Bash tool call this
session makes appends to its own Claude Code transcript, so "no new sessions
between runs" cannot hold while the profiler's own invocation is itself new
session activity). Supplementary idempotency proof isolating from that
confound: two `agentprof claude` invocations with the SAME fixed `--since`
(not mtime-derived) against the same rolling merge chain —
`comm -23 <(sort wk-b.jsonl) <(sort wk-c.jsonl) | wc -l` → `0` (zero lines
lost/duplicated between merges; only genuine new-activity growth, +2 lines,
appears). This proves the merge/evict logic is correct and idempotent on
real data, consistent with task 01's fixture-level unit tests
(`TestMergeEmptyFreshLeavesNonEvictedUntouched` etc.).

**Criterion 2 — CSRF endpoint (R5):**
```
$ curl -s -X POST http://127.0.0.1:8899/api/cost/refresh   # no CSRF header
bad token   (HTTP 403)

$ TOKEN=<extracted from window.CSRF on the live page>
$ curl -s -X POST -H "X-CSRF: $TOKEN" http://127.0.0.1:8899/api/cost/refresh
{"ok": true, "sessions_added": 2}   (HTTP 200)
```
`weekly-7d.jsonl` mtime: `Jul 7 22:25:10` → `Jul 7 22:25:52` (advanced).

**Criterion 3 — Cost (7d) tile renders (R6):**
`curl -s http://127.0.0.1:8899/workboard | grep -c 'Cost (7d)'` → `1`.
Tile: `<div class="v">$7,818.77</div><div class="l">cost (7d)</div>`.

**Criterion 4 — missing-summary pending state (R7):**
With `weekly-7d-summary.json` moved aside: `curl -s -o /dev/null -w
'%{http_code}' http://127.0.0.1:8899/workboard` → `200`; cost tile renders
`<div class="v">—</div>` instead of a dollar amount. File restored
immediately after.

**Criterion 5 — end-to-end totals match (final criterion):**
```
$ python3 -c "import json; print(json.load(open('$HOME/.local/state/agentprof/weekly-7d-summary.json'))['totals'])"
{'cache_read_tokens': 5759028928, 'cache_write_tokens': 354732550, 'calls': 67161,
 'cost_microusd': 7818774086, 'duration_ms': 2047853409, 'input_tokens': 31899036,
 'output_tokens': 19212840}
```
`cost_microusd` 7818774086 → $7818.774086, matching the rendered tile
`$7,818.77` within rounding.

## Files changed
- `agentprof/scripts/refresh-profile.sh` — weekly-7d step added (task 04's
  own Touch), plus the mktemp suffix-randomization fix (both the 30d and
  weekly temp-file construction).
