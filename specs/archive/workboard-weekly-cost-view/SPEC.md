# Workboard: incremental weekly cost/token view

Status: open
Priority: P1

## Problem

There's no default view of "where did cost/tokens go this week" in
workboard — today that requires manually running `agentprof claude --days
N` (a full re-parse of every transcript file in the window,
`agentprof/internal/claude/claude.go:108-147,185-201` — session inclusion
is all-or-nothing by max mtime, and `Collect()` has no API for "give me
only what changed since X") followed by `go tool pprof -top` per
dimension. Re-running that full scan on every workboard page load would
mean reprocessing potentially thousands of transcript lines per request —
expensive, and explicitly what should be avoided per the "only add stuff
we don't already have yet" requirement.

agent-console already has a caching precedent: `_board_cache`
(`agent-console.py:309`, `BOARD_TTL=45` seconds) and `_plugins_cache`
(`agent-console.py:211`, 60 seconds) — both short-lived in-memory caches
that don't survive a process restart and aren't designed for a multi-day
rolling window. `render_workboard` (`agent-console.py:1118`) is a pure
function of pre-built board data — it does no I/O itself; the HTTP
handler that serves `/workboard` builds that data (via the cached
`board()` helper) and passes it in. Any new data source for this spec
must be plumbed through that same handler, not called from inside
`render_workboard`.

`agentprof claude`'s CLI (`cmd_claude.go`) has an `-o <path>` flag whose
`.pb.gz` suffix writes a pprof profile and any other value writes JSONL
(`internal/output/output.go:20-26`); `--days N` defaults to 30
(`cmd_claude.go:22`) and is always present on the flag set whether or not
a caller passed it explicitly. Critically, a pprof `.pb.gz` profile has
NO per-sample timestamp — `pprofenc.Build` collapses all per-sample times
into two profile-LEVEL scalars (`TimeNanos`/`DurationNanos`) before
writing; the per-sample `schema.Sample.Time` field only survives in
agentprof's OWN JSONL format (`internal/schema/schema.go`'s
`MarshalLine`/`Read`, which already round-trip `Time` losslessly). This
rules out a `.pb.gz` file as the rolling cache: a 7-day eviction rule
needs per-sample time, so the cache must be JSONL, not `.pb.gz`.

## Solution

**`agentprof claude` gains `--since <RFC3339>`**, mutually exclusive with
an EXPLICITLY-passed `--days` (detected via `flag.FlagSet.Visit`, since
`--days` always carries its default of `30` otherwise and a presence
check alone can't distinguish "user passed --days 30" from "default"),
filtering sessions by the same max-mtime check `inWindow()` already does,
against an absolute cutoff instead of a relative one.

**`agentprof claude` gains `--merge <path>`**, using JSONL as the cache
format (never `.pb.gz`, per the Problem section's finding) via the
EXISTING `schema.Read`/`output.Write` functions — no new encoder or
decoder needed:

- Read `<path>` via `schema.Read` (a missing file is treated as zero
  existing samples, not an error).
- Run the normal `Collect()` pass for the `--since` cutoff to get this
  run's fresh samples.
- Drop every existing sample whose `Labels["session"]` also appears among
  the fresh samples' session labels (the fresh reparse is authoritative
  for any session whose mtime advanced — this correctly replaces a
  still-being-written session's stale contribution without double-
  counting it).
- Append the fresh samples (fresh samples may legitimately be an EMPTY
  slice — the common steady-state case, e.g. an hourly refresh that finds
  nothing new since the last run).
- Drop every remaining sample (existing survivors plus freshly appended)
  whose `Time` is older than `now - 7d`.
- Write the merged result to `-o` (which may be the same path as
  `--merge`). THE MERGED RESULT MAY ITSELF BE EMPTY (a fully idle 7-day
  window with nothing fresh evicts everything) — `--merge` mode has TWO
  independent zero-sample guards to bypass, not one: `cmdClaude`'s own
  "no samples found" check (which today runs unconditionally before any
  output step) AND `output.Write`'s separate internal
  `errors.New("no samples to write")` guard on an empty slice. Neither
  may fire in `--merge` mode: write an empty JSONL file directly
  (equivalent to truncating `-o` to zero bytes) instead of routing an
  empty merged slice through `output.Write` at all, and skip
  `cmdClaude`'s pre-write empty check whenever `--merge` is set,
  regardless of whether the fresh Collect() pass or the final merged
  result is what's empty.

**`agentprof claude` gains `--summary <path>`**, writing a small
pre-aggregated JSON alongside the normal output — computed by agentprof
itself, which already owns the frame-hierarchy convention (project /
skill / agent / model position in the stack), rather than parsed out of
`go tool pprof -top` text (which aggregates by frame name with no
indication of a frame's ROLE — it cannot cleanly answer "top-5 models"
versus "top-5 skills" since both are just same-shaped rows). The summary
groups every sample's each Value by:
`{by_project: {name: {sample_type: total}}, by_skill: {...}, by_agent_type: {...}, by_model: {...}, totals: {sample_type: total}}`
— `project` = `Stack[0]`; `skill` = the first frame matching
`^skill:`/exactly `(no skill)`; `agent_type` = the first frame matching
`^agent:`; `model` = the last (leaf) frame that isn't a `tool:`/
`role:`/`stage:` frame (forward-compatible with
`specs/agentprof-instrumentation`'s new frame kinds once that spec
lands — this spec's summary code simply ignores frame kinds it doesn't
recognize as project/skill/agent/model, so it degrades gracefully today
and gets richer automatically once that spec ships new frame prefixes).
A sample with no frame matching the skill rule (e.g. an `(unlinked)`
subagent stack, which carries neither `skill:` nor `(no skill)`) falls
into a `(no skill)` bucket in `by_skill` rather than being silently
dropped — it still counts in `by_project`/`by_model`/`totals` either way.
NOTE (no requirement change; R3's model rule stays exactly as specified
above): the model rule has no explicit "no model" bucket, so a pure
`tool:` sample — one carrying only `duration_ms`, no tokens/cost — does
not resolve to "no model"; the leaf rule simply skips its `tool:` frame
and resolves to the preceding non-tool frame (e.g. `main`), so that
sample's `duration_ms` lands in `by_model["main"]`. This is harmless for
the "Cost (7d)" panel today (it renders cost, not duration), but worth
naming once `specs/agentprof-instrumentation`'s richer `tool:`/duration
frames ship, since the contract will then carry duration samples whose
only honest model attribution would be a bucket this rule does not
provide.
**When `--merge` is present, `--summary` is computed from the FINAL
merged, post-eviction sample set — the full rolling 7-day window — never
from the fresh `Collect()` pass alone** (the panel is titled "Cost (7d)";
a summary of only this run's fresh delta would show the wrong period).
When `--merge` is absent, `--summary` is computed from the fresh
`Collect()` output directly. `--summary` also writes a top-level
`sessions_added` integer: the count of DISTINCT `Labels["session"]`
values present in this run's fresh samples (i.e. sessions touched since
the last refresh, whether previously-unseen or updated) — `0` when fresh
is empty, computed the same way with or without `--merge`.

**`agentprof/scripts/refresh-profile.sh`** (already an hourly launchd job,
`com.sjaconette.agentprof-refresh`) gains a second step: maintain
`~/.local/state/agentprof/weekly-7d.jsonl` and
`~/.local/state/agentprof/weekly-7d-summary.json` via
`agentprof claude --since <mtime of weekly-7d.jsonl, or 7 days ago if
absent> --merge ~/.local/state/agentprof/weekly-7d.jsonl -o
~/.local/state/agentprof/weekly-7d.jsonl --summary
~/.local/state/agentprof/weekly-7d-summary.json`. No new launchd agent —
the existing hourly cadence is the refresh cadence; page loads never
trigger a rescan or a subprocess call.

**A new CSRF-protected `POST /api/cost/refresh`** (agent-console.py,
mirrors `/api/profile/refresh`'s handler at `agent-console.py:1544-1577`
and its route registration at `1653`) runs the same refresh step
synchronously for a manual "refresh now" button. The handler reads
`sessions_added` back out of the just-written `weekly-7d-summary.json`
(agentprof computes and writes it, per the `--summary` description
above — the handler never derives this count itself) and returns
`{"ok": true, "sessions_added": N}`.

**New workboard panel**: a "Cost (7d)" tile alongside the existing
specs/tasks/active/inbox tiles (`agent-console.py:1128-1141`, panel
bodies at `1147-1175`, `render_workboard` itself at `1118`). The
`/workboard` HTTP handler reads `weekly-7d-summary.json` (a small file —
cheap even called on every request; no subprocess, no transcript
reparse) and passes its parsed dict into `render_workboard` as a new
argument; `render_workboard` stays a pure function, only formatting
whatever summary dict it's given (never doing file I/O itself, matching
its existing purity). It renders total cost (from `totals.cost_microusd`,
formatted as a dollar string via plain division in Python — not a pprof
unit-scaling trick, per the earlier decision to leave the recorded unit
as `cost_microusd`) plus top-5 rows from `by_model`, `by_skill`, and
`by_project`.

## Requirements

- **R1**: `agentprof claude --since <RFC3339>` filters sessions by the
  same `inWindow()` max-mtime check as `--days`. Providing `--since`
  together with an EXPLICITLY-passed `--days` (detected via
  `fs.Visit`, not by checking `*days != 0`) is a usage error (nonzero
  exit, stderr message, no output written); providing `--since` alone
  (leaving `--days` at its default) is not an error.
- **R2**: `agentprof claude ... --merge <path> -o <path>`: reads the
  existing JSONL at `<path>` via `schema.Read` (missing file = zero
  samples, not an error); drops existing samples whose session label
  matches any fresh sample's session label; appends fresh samples (an
  EMPTY fresh-sample set is valid and must not trigger the "no samples
  found" exit-1 path that applies outside `--merge` mode); drops samples
  with `Time` older than `now - 7d`; writes the result via `output.Write`
  to a non-`.pb.gz` `-o` path. `--merge` combined with a `.pb.gz` `-o`
  path is a usage error (nonzero exit, stderr message, no output
  written) — a pprof profile can't round-trip per-sample `Time`, so
  writing one here would silently break the next merge's eviction step.
- **R3**: `agentprof claude ... --summary <path>` writes the JSON shape
  described in Solution, grouping every sample's Values by project/
  skill/agent_type/model as defined there (a sample matching no skill
  frame falls into `by_skill`'s `(no skill)` bucket, never dropped),
  plus a `totals` object summing every sample type across all samples,
  plus a top-level `sessions_added` integer (distinct `Labels["session"]`
  count among this run's fresh samples). When `--merge` is also given,
  the grouping and totals are computed from the final merged,
  post-eviction sample set, not the fresh samples alone —
  `sessions_added` is the one exception, always counted from fresh only.
- **R4**: `refresh-profile.sh` maintains `weekly-7d.jsonl` and
  `weekly-7d-summary.json` incrementally on its existing hourly cadence,
  using the previous run's `weekly-7d.jsonl` mtime as `--since` (falling
  back to 7 days ago on first run / missing file).
- **R5**: `POST /api/cost/refresh` triggers the same incremental refresh
  synchronously, CSRF-protected identically to `/api/profile/refresh`,
  returning `{"ok": true, "sessions_added": N}` on success.
- **R6**: The `/workboard` HTTP handler reads `weekly-7d-summary.json` and
  passes it into `render_workboard`, which gains a "Cost (7d)" tile +
  panel rendering `totals.cost_microusd` as a dollar string and top-5
  rows from `by_model`/`by_skill`/`by_project` — `render_workboard` does
  no file I/O; the handler does.
- **R7**: A page load with no `weekly-7d-summary.json` present yet (fresh
  install) renders the panel in an explicit empty/pending state via a
  200 response, never a 500 — the first hourly refresh (or a manual
  "refresh now" click) populates it.

## Out of scope

- Any change to `cost_microusd`'s recorded unit (decided: stays as-is;
  dollar formatting happens in workboard's own rendering, not pprof).
- The `duration_ms`/`tool:`/`stage:`/`role:` instrumentation work — that's
  `specs/agentprof-instrumentation/SPEC.md`. This spec's summary grouping
  (R3) ignores frame kinds it doesn't recognize, so it works unmodified
  today and gets richer automatically once that spec ships, with no
  further change needed here.
- A rolling window other than 7 days, or a user-configurable window
  length — fixed at 7 days for this spec.
- Historical data before this spec ships — the rolling window starts
  empty and fills in over its first 7 days of hourly refreshes (or
  immediately via one manual refresh covering a `--since` 7 days back).
- Emitting a `.pb.gz` copy of the rolling cache for viewing in pprof's own
  UI — the cache is JSONL only; anyone wanting a pprof view can run
  `agentprof claude --since ... -o x.pb.gz` separately at any time, which
  already works unmodified.

## Acceptance criteria

- [ ] `go test ./...` (agentprof) passes, including: `--since`+explicit
      `--days` mutual exclusivity via `fs.Visit` (R1); merge semantics
      with a fixture existing-cache + fresh-run where one session
      overlaps (old samples for it dropped, not duplicated) and one
      session is new-only (appended) (R2); a merge run with an EMPTY
      fresh-sample set does not exit nonzero and leaves non-evicted
      samples untouched (R2); a merge run where EVERY existing sample is
      older than 7 days and fresh is also empty writes a valid empty
      JSONL file and exits 0, never routing through `output.Write`'s
      zero-sample error (R2); `--summary` output grouping for a fixture
      with known project/skill/agent/model frames, including one
      `(unlinked)`-shaped sample landing in `by_skill`'s `(no skill)`
      bucket rather than vanishing (R3); `sessions_added` matching the
      fixture's distinct session count (R3).
- [ ] `agentprof claude --since 2020-01-01T00:00:00Z --days 1 -o /tmp/x`
      → nonzero exit, stderr mentions both flags; `agentprof claude
    --since 2020-01-01T00:00:00Z -o /tmp/x` (no explicit `--days`) →
      exits 0 (R1).
- [ ] Running `agentprof/scripts/refresh-profile.sh` twice in a row (no
      new sessions between runs) leaves `weekly-7d.jsonl`'s sample count
      unchanged the second time, and the script exits 0 both times (R4 —
      proves the steady-state empty-delta merge path from R2 works
      end-to-end, not just in the unit test).
- [ ] `curl -s -X POST -H "X-CSRF: $TOKEN" http://127.0.0.1:8899/api/cost/refresh`
      → `{"ok": true, ...}` and `weekly-7d.jsonl`'s mtime advances (R5).
- [ ] `curl -s http://127.0.0.1:8899/workboard | grep -c 'Cost (7d)'` → ≥ 1
      (R6).
- [ ] With `weekly-7d-summary.json` temporarily moved aside, `curl -s -o
    /dev/null -w '%{http_code}' http://127.0.0.1:8899/workboard` → 200,
      and the page body shows the empty/pending state (R7).
- [ ] End-to-end: after one manual refresh,
      `python3 -c "import json; print(json.load(open('$HOME/.local/state/agentprof/weekly-7d-summary.json'))['totals'])"`
      shows nonzero totals matching (within rounding) the numbers
      rendered in the workboard panel for the same period.

## Open questions

(none)

## Parallelization

- **Group A (serial chain)**: 01 → 02 — both edit `cmd_claude.go` and the
  same internal packages; Touch overlap forces serialization.
- **Group B (parallel with Group A)**: 03 — disjoint Touch
  (`agent-console/` only) and the summary JSON shape is a value contract
  pinned verbatim in this spec (R3), owned by the spec, so neither side
  may adapt it unilaterally. Task 03 tests against fixture JSON matching
  the pinned shape; the real-binary seam is NOT considered proven until
  task 04.
- **04** runs last (depends on 01, 02, 03) — it is deliberately the
  integration task that drives real binaries across the seam
  (script → agentprof → summary JSON → panel), per the known failure mode
  where two fixture-tested sides of a pinned contract still ship a dead
  seam.
- NOTE: `specs/agentprof-instrumentation` also has tasks touching
  `agentprof/internal/` — the two specs' Go tasks must not run
  concurrently with each other (cross-spec Touch overlap); their
  skill-text/console tasks are mutually disjoint.
