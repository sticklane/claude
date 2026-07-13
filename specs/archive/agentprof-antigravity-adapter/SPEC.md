# agentprof: Antigravity adapter (`agentprof antigravity`)

Status: open
Priority: P1
Breakdown-ready: true

## Problem

agentprof is harness-agnostic by design — `cmd_claude.go`, `cmd_gcp.go`,
`cmd_vertex.go`, and `cmd_otel.go` are four independent adapters that all
normalize into one `internal/schema.Sample` (`agentprof/SCHEMA.md`). But
there is no `agentprof antigravity` adapter, and `workboard.py`'s
`compute_spend()` (`.claude/skills/workboard/workboard.py:1263`, mirrored
byte-for-byte at `antigravity/.agents/skills/workboard/workboard.py:1263`)
only ever shells out to `agentprof claude -o summary --claude-dir
~/.claude`. Every session run through Antigravity (real, confirmed-present
session logs at `~/.gemini/antigravity-cli/conversations/*.db`, one SQLite
file per CASCADE/conversation — confirmed by joining `trajectory_meta`'s
`cascade_id` column against the `.db` filename, see Solution; a cascade can
contain multiple distinct trajectories, each with its own `trajectory_id`,
so "one file per trajectory" is imprecise and not used elsewhere in this
spec) is completely invisible to the workboard's cost/spend rollup —
Antigravity work costs real money and tokens but shows up nowhere.

Confirmed this session by opening `~/.gemini/antigravity-cli/conversations/
1a00dd5f-b2a6-441a-b2a3-d31368ad34fa.db` read-only with `sqlite3 ... ".schema"`
and `protoc --decode_raw` on its blob columns (no `.proto` schema is shipped
with Antigravity — only raw field-number decoding is available):

- Tables: `trajectory_meta` (trajectory_id PK, cascade_id, trajectory_type,
  source), `steps` (idx PK, step_type, status, metadata/error_details/
  permissions/task_details/render_info/step_payload blobs, step_format),
  `gen_metadata` (idx PK, data blob, size), `executor_metadata`,
  `parent_references`, `trajectory_metadata_blob`, `battle_mode_infos`.
- **All substantive data lives in protobuf-encoded blob columns** — no
  plain-text or JSON column carries tokens, cost, or model name.
- `gen_metadata` = one row per model generation. In the sample DB it has 34
  rows, exactly matching the 34 `steps` rows with `step_type=15` — `idx` is
  the join key between the two tables for a generation event. Decoded
  fields: field 4 is a token-usage submessage (sub-fields 1/2/3/6/9/10 are
  numeric counts — which sub-field is prompt vs. completion vs. cache is
  NOT yet confirmed against a labeled fixture, see R2); field 9.4 is a
  protobuf `Timestamp` (seconds+nanos) for generation time; field 19 is a
  short model slug (`"gemini-default"` observed); field 20 is a repeated
  `{key, value}` string map including `model_enum` (an internal enum name
  like `"MODEL_PLACEHOLDER_M20"`, not a stable model id), `trajectory_id`,
  `used_claude` / `used_claude_conservative` / `used_non_gemini_model`
  (stringified booleans — the closest thing to a model-family marker), and
  `last_step_index`; field 21 is a human-readable model display string
  (`"Gemini 3.5 Flash (Medium)"` observed) — the best available model-name
  signal, but a display label, not a stable id.
- `steps.metadata` for `step_type=21` (tool-call steps) carries lifecycle
  timestamps and a tool name/args submessage (field 4: `{1: call-id, 2:
  tool name e.g. "run_command", 3: JSON args string, 7: large opaque blob —
  not decodable, not attempted}) but **no token or cost data** — cost only
  ever lives on `step_type=15` / `gen_metadata` rows.
- `trajectory_meta` + `trajectory_metadata_blob` carry the workspace path
  (`file://` URI), git branch, `cascade_id`, and a project label
  (`"default-cli-project"` observed) — the closest equivalent to Claude
  Code's project/session attribution for the Stack's root levels.
- There is no stage/role marker in Antigravity's data model equivalent to
  the `stage:`/`role:` frames the `agentprof-instrumentation` spec's R8
  added to the antigravity mirror's `drain.md`/`build.md` workflow text —
  Antigravity's `steps` table has no free-text frame or skill-name field to
  match against. Skill/agent-level attribution is therefore OUT OF SCOPE
  for this spec (see Out of scope).
- No `cost_microusd` anywhere. Cost must be computed from (token counts +
  model name) via a new Gemini-specific rate table, mirroring
  `internal/pricing/table.go`'s prefix-match `Price(model string, usage
  Usage) (int64, bool)` design — but that table is Anthropic-only and keyed
  by stable Claude model ids; Gemini's rate card is a different price
  structure entirely and the only model signal in the data (`field 21`'s
  display string) is not a stable id in the same namespace, so this spec
  adds a sibling `internal/pricing` table + a display-string
  normalization step, not a reuse of the existing Claude table.

## Solution

Add a new `internal/antigravity` package (parsed, not reusing
`internal/claude`) plus a `cmd_antigravity.go` subcommand, following
`cmd_claude.go`'s existing shape as closely as the data allows:

1. **Minimal protobuf field-walker**, hand-rolled in Go (`internal/
   antigravity/protowire.go` or similar) — a tag/varint/length-delimited
   reader over the raw wire format that extracts specific `(field number,
   wire type)` paths already reverse-engineered above (no dependency on
   `protoc` being installed on the machine running `agentprof`, no
   generated `.pb.go` from a `.proto` file that doesn't exist upstream).
   This is a targeted extractor, not a general protobuf decoder — it reads
   only the field numbers this spec's parsing needs and treats anything
   else as opaque/skippable, which is exactly the wire format's
   self-describing design (every field carries its own tag + length).
   Malformed or unrecognized bytes in a blob are a per-row skip, not a
   fatal error, matching `SCHEMA.md`'s existing skip-rules philosophy. This
   walker is the riskiest new code in the adapter (hand-rolled wire-format
   parsing with no upstream `.proto` to validate against) and gets its own
   direct unit tests, independent of `Collect` (R1 covers the walker's
   `Collect`-level integration; a dedicated walker test covers the parser
   in isolation) — see R1's acceptance coverage.
2. **Collect(dir string, cutoff time.Time) ([]schema.Sample, int, error)**
   in `internal/antigravity/antigravity.go`: glob `dir/conversations/*.db`
   (default `dir` = `~/.gemini/antigravity-cli`), open each SQLite file
   read-only (`file:...?mode=ro`), join `steps` (`step_type=15`) to
   `gen_metadata` on `idx`, and for each joined row emit one
   `schema.Sample`:
   - `Time`: field 9.4's protobuf Timestamp, converted to `time.Time`.
   - `Stack`: `[project, "antigravity", model]` where `project` comes from
     the single row of `trajectory_metadata_blob` (`id="main"`), reading
     the exact field path confirmed against the inspected fixture: outer
     field 1 is a submessage whose sub-field 1 is the workspace `file://`
     URI and sub-field 4 is the git branch (`project` = basename of
     sub-field 1's URI, falling back to the raw URI if basename extraction
     fails); outer field 18 is the project label string (e.g.
     `"default-cli-project"`) — prefer field 18 when present and
     non-empty, falling back to the workspace-URI basename only when field
     18 is empty. `model` in the Stack leaf is the RAW field-21 display
     string (e.g. `"Gemini 3.5 Flash (Medium)"`), unmodified — passed
     as-is to `PriceGemini` (R3), which is itself keyed on that same raw
     display string; there is no separate "normalization" transform, and
     none should be invented, since `PriceGemini`'s map keys and the Stack
     leaf must be byte-identical for R3's lookup to ever hit.
     (Outer field 6 is a self-referential `cascade_id` string
     — confirmed this session to equal both the `.db` filename basename
     and the `cascade_id` column of the separate `trajectory_meta` table
     for the same file; this is the SAME value R4/Solution item 5 use as
     `Labels["session"]`, so a worker may read it directly from
     `trajectory_metadata_blob` field 6 without a second join through
     `trajectory_meta` if that's simpler to implement. Outer field 3 is a
     distinct, unidentified id this spec does not use — noted only so a
     worker doesn't mistake it for the cascade id or confuse it with
     `gen_metadata`'s separate `trajectory_id` key, which is yet a third,
     finer-grained id — none of these three ids are interchangeable.)
     `"antigravity"` is a fixed
     harness-marker frame, parallel to how Claude Code samples' stack
     roots are `project > skill > agent > model` — Antigravity has no
     skill/agent equivalent (see Out of scope), so the harness name fills
     that gap rather than being omitted, keeping stack depth comparable
     across adapters for pprof's tree view.
   - `Values`: `input_tokens`, `output_tokens`, `cache_read_tokens` (best
     mapping of `gen_metadata` field 4's sub-fields per R2's fixture work;
     any sub-field that can't be confidently mapped is left OUT of Values
     rather than guessed), `cost_microusd` (from the new pricing table,
     R3), `calls: 1`.
   - `Labels`: `source: "antigravity"`, `session` = the **cascade_id**
     (`trajectory_meta.cascade_id` — confirmed this session to equal the
     `.db` file's own basename, e.g. `1a00dd5f-b2a6-441a-b2a3-d31368ad34fa`,
     and to equal the directory name `scan_antigravity()` in `workboard.py`
     already yields as each conversation's `"id"` from
     `~/.gemini/antigravity*/brain/<id>/` — this is the id namespace R4's
     merge must key on, NOT `gen_metadata`'s own `trajectory_id` string,
     which is a different, finer-grained id for the trajectory *within*
     that cascade and does not appear in `workboard.py` anywhere), `
     trajectory_id` (the finer-grained id from `gen_metadata` field 20,
     kept as a label for drill-down but never used as the merge key),
     `model_raw` (the unnormalized field-21 display string), `db_file`
     (basename of the source `.db`, for debugging).
   - Rows whose db file is locked (an active `-wal`/`-shm` pair mid-write)
     are retried once after opening read-only fails, then skipped with a
     stderr note — never block on a live Antigravity session's lock.
3. **Gemini pricing table** (`internal/pricing/gemini_table.go` or a new
   `internal/geministypes` — final placement decided in review, not gating
   this spec): a `PriceGemini(displayName string, usage Usage) (int64,
   bool)` sibling to `Price`, keyed by a small explicit map from known
   display strings (e.g. `"Gemini 3.5 Flash (Medium)"`) to a rate row
   sourced from Google's published Gemini API pricing. An unmapped display
   string returns `priced=false` (no `cost_microusd` key emitted for that
   sample) — identical convention to `Price`'s existing `priced` bool, so
   `workboard.py`'s summary rows already tolerate a costless row (R4).
4. **`cmd_antigravity.go`**: `cmdAntigravity(args, stdout, stderr) int`,
   mirroring `cmdClaude`'s flag shape for the flags THIS spec's acceptance
   criteria exercise — `--antigravity-dir` (default
   `~/.gemini/antigravity-cli`), `--days`/`--since`, `-o` — by reusing
   `internal/output` unchanged. `--merge` and `--summary <path>` (the
   rolling-JSONL-cache and `internal/costsummary` paths `cmdClaude` also
   exposes) are OUT OF SCOPE for this spec: `workboard.py`'s dual-harness
   merge (Solution item 5) only ever calls `-o summary`, so wiring
   `--merge`/`--summary` for Antigravity with no consumer and no test
   coverage would be unverified surface area; add them in a follow-up
   spec if/when a caller needs them. The
   `-o summary` path reuses `summary.go`'s existing `summarize()` /
   `summaryRow` list shape UNCHANGED (this is the JSON array of `{session,
   model, input_tokens, output_tokens, cache_read_tokens,
   cache_write_tokens, cost_microusd, priced}` that `agentprof claude -o
   summary` already emits, per `summary.go:16-24,33-82` — it is a
   different object from `internal/costsummary.Build`'s
   `by_project`/`by_model`/`totals` shape, which stays reserved for the
   separate `--summary <path>` flag and is NOT what `workboard.py` parses;
   the two must not be confused, see R5). `cmdAntigravity` exits 1 with a
   "no samples found" stderr message when `Collect` returns zero samples
   (mirroring `cmd_claude.go:75-77`'s existing empty-result guard) — this
   guard lives in `cmd_antigravity.go` itself (package `main`), not in
   `internal/antigravity`, since `Collect`'s own return type has no exit
   code to set (R6).
5. **`workboard.py` dual-harness spend**: add a new `compute_antigravity_
   spend(antigravity_dir, cascade_ids)` function, structurally parallel to
   `compute_spend` (same subprocess/timeout/fail-soft shape, shelling out
   to `agentprof antigravity -o summary --antigravity-dir <dir> --days
   3650`), but filtering each returned row by `row["session"] in
   cascade_ids` where `cascade_ids = {c["id"] for c in antigravity}` —
   `antigravity` being the `scan_antigravity()` result workboard.py's
   `build_dashboard` (or equivalent) already computes at
   `workboard.py:1462`, one call site above the existing `compute_spend`
   call at `workboard.py:1479`. This is the corrected id-set: `compute_
   spend`'s existing `session_ids` parameter is Claude-session-only and
   antigravity's cascade ids are never members of it (an antigravity row
   filtered against `{s["id"] for s in sessions}` at line 1479 would
   silently zero out — this is why a bolt-on to the existing function is
   wrong; a sibling function with its own id-set is required). The
   dashboard's `"spend"` key becomes the result of a new `merge_spend
   (claude_spend, antigravity_spend)` helper whose return shape is a
   drop-in replacement for what `compute_spend` returns today (same keys
   `render_spend_section` at `workboard.py:1385-1399` already reads — this
   spec does NOT change the renderer, so the merge must match its existing
   contract exactly):
   - `by_model`: `compute_spend` returns this as a LIST already sorted by
     `(-cost_microusd, model)` (`workboard.py:1324-1329`), consumed by a
     plain `for m in by_model:` loop (`workboard.py:1399`) — `merge_spend`
     concatenates both harnesses' `by_model` lists (Claude and Gemini
     model names never collide, so no per-model aggregation is needed) and
     RE-SORTS the combined list by the same `(-cost_microusd, model)` key,
     never leaving it as two separately-sorted blocks.
   - `by_session`: both harnesses return this as a dict keyed by session/
     cascade id (`workboard.py:1314`) — cascade ids and Claude session ids
     are different UUID spaces, so `merge_spend` unions the two dicts
     directly (`{**claude_spend["by_session"], **antigravity_spend
     ["by_session"]}`, no key collision possible).
   - `available`/`reason`: `render_spend_section` gates the ENTIRE spend
     panel on one top-level `spend.get("available")`
     (`workboard.py:1385`) — there is no per-harness rendering path today,
     and this spec does not add one. `merge_spend` therefore sets the
     top-level `available = claude_spend["available"] or
     antigravity_spend["available"]` (spend renders whenever at least one
     harness loaded) and a top-level `reason` set only when BOTH harnesses
     failed (concatenating both failure reasons); when exactly one harness
     failed, `merge_spend` additionally sets two new, renderer-optional
     keys `claude_available`/`claude_reason` and
     `antigravity_available`/`antigravity_reason` so a future UI change
     could surface the partial-failure detail, but `render_spend_section`
     itself is NOT required to change to consume them (out of scope
     beyond making the top-level gate correct). A broken Antigravity call
     must never blank out `by_model`/`by_session` rows the Claude call
     already populated, and vice versa.
   Applies to both `.claude/skills/workboard/workboard.py` and its mirror
   at `antigravity/.agents/skills/workboard/workboard.py` in the same
   change, per this repo's CLAUDE.md mirror-parity convention.

## Requirements

- **R0 (human-gated prerequisite, blocks R2)**: produce a labeled fixture
  confirming which `gen_metadata` field-4 sub-field is prompt tokens, which
  is completion tokens, and which (if any) is a cache-read count. This
  requires a human to run one real, short Antigravity session with a
  known, hand-counted prompt/response pair and commit the resulting
  `.db` file, UNMODIFIED (a real SQLite file, not extracted rows — R1's
  `Collect` and the e2e acceptance criterion both open it via SQLite, so
  a non-`.db` extraction cannot satisfy either), to `internal/antigravity/
  testdata/conversations/<cascade_id>.db` — that exact `conversations/`
  subdirectory, because `Collect` globs `<dir>/conversations/*.db` (R1),
  so `--antigravity-dir internal/antigravity/testdata` resolves the glob
  to `internal/antigravity/testdata/conversations/*.db`, not
  `internal/antigravity/testdata/*.db`. This step is NOT executable
  from spec text alone by a `/build` or `/drain` worker — `/breakdown`
  MUST mark whichever task covers this as manual-pending (the pattern in
  docs/memory/unattended-worker-tool-limits.md) rather than assigning it
  to an unattended worker, and every task that depends on the confirmed
  mapping (R2, and any `Values`-emitting code in Solution item 2) is
  blocked on this fixture landing first.
- **R1**: `internal/antigravity.Collect(dir string, cutoff time.Time)
  ([]schema.Sample, int, error)` opens every `*.db` file under
  `<dir>/conversations/`, joins `steps` (`step_type=15`) to `gen_metadata`
  on `idx`, and returns one `schema.Sample` per joined row whose generation
  timestamp falls within the cutoff window, plus a count of skipped rows
  (locked/corrupt db files, or blobs the field-walker can't parse) — this
  is a new signature for a new adapter; it is not required to match
  `claude.Collect`'s 4-return-value shape (`[]schema.Sample, []Turn, int,
  error`), which carries a Claude-specific `Turn` type this adapter has no
  equivalent for.
- **R2 (blocked on R0)**: once R0's fixture confirms the mapping,
  `gen_metadata` field 4's token-count sub-fields are mapped to
  `input_tokens`/`output_tokens`/`cache_read_tokens` in
  `internal/antigravity`, using exactly the sub-field assignment R0's
  fixture justifies; the mapping and the fixture that justified it both
  live in `internal/antigravity/testdata/`. Any sub-field whose meaning
  the fixture can't confirm is left out of `Values` rather than guessed
  (Solution's rule).
- **R3**: `PriceGemini` ships with an explicit, hermetic rate table sourced
  from Google's published Gemini API pricing, keyed by the following
  model display strings — the exact set confirmed present in the fixture
  `.db` files inspected during this spec's authoring, committed to
  `internal/pricing/testdata/` as the fixture backing this requirement's
  test: `"Gemini 3.5 Flash (Medium)"` (the only display string actually
  observed this session — any other display string a future `.db` emits
  is simply unmapped until a rate row is added for it, per the next
  clause). An unmapped display string returns `priced=false` and the
  emitted sample omits `cost_microusd` rather than defaulting to `0` (a
  present `0` would misreport as "free," which is worse than "unpriced").
- **R4**: `workboard.py` gains a new `compute_antigravity_spend
  (antigravity_dir, cascade_ids)` function (both the original
  `.claude/skills/workboard/workboard.py` and its mirror at
  `antigravity/.agents/skills/workboard/workboard.py`) that shells out to
  `agentprof antigravity -o summary`, filters returned rows by
  `row["session"] in cascade_ids` (never by the Claude-only `session_ids`
  `compute_spend` already filters by — the two id spaces do not overlap,
  see Solution item 5), and a `merge_spend(claude_spend, antigravity_spend)`
  helper implementing exactly the by_model-concatenate-and-resort,
  by_session-dict-union, and single-top-level-`available`-OR contract
  Solution item 5 specifies (matching `render_spend_section`'s existing
  read contract at `workboard.py:1385-1399` without modifying that
  function) — a broken Antigravity call must not blank out working Claude
  numbers or vice versa, and (this is the requirement's observable
  contract) an Antigravity `.db` whose cascade id IS in `cascade_ids` must
  actually contribute a nonzero amount to the dashboard's rendered total
  spend, not silently compute to zero via a mismatched id-set.
- **R5**: `agentprof antigravity -o summary` emits the SAME JSON shape
  `agentprof claude -o summary` already emits — the `summaryRow` list from
  `summary.go`'s `summarize()` (`{session, model, input_tokens,
  output_tokens, cache_read_tokens, cache_write_tokens, cost_microusd,
  priced}` per row), NOT `internal/costsummary.Build`'s
  `by_project`/`by_model`/`totals` object (that shape is reserved for the
  separate `--summary <path>` flag and is never what `workboard.py`
  parses from stdout) — so `workboard.py`'s existing row-parsing
  (`json.loads(stdout)` expecting a list, `workboard.py:1297-1302`) needs
  no shape-specific branching between the two harnesses.
- **R6**: A markerless/no-op run (`--antigravity-dir` pointing at an empty
  or nonexistent directory) exits 1 with a clear "no samples found"
  message, matching `cmdClaude`'s existing empty-result behavior — never a
  silent zero-row success that would make a broken adapter look like "no
  Antigravity usage."

## Out of scope

- Skill/agent/stage-level attribution for Antigravity samples (parallel to
  Claude Code's `skill:`/`agent:` frames or the `agentprof-instrumentation`
  spec's `stage:`/`role:` markers). Antigravity's `steps` table has no
  analogous free-text field to key off, and inferring one from tool-call
  JSON args (`step_type=21` field 4.3) would be speculative pattern-
  matching, not a confirmed convention — a future spec if/when Antigravity
  workflow text is instrumented with an equivalent marker convention.
- Parsing `step_type=21` (tool-call) steps into `tool:<name>` duration
  samples analogous to the Claude adapter's tool-call timing (if/when that
  lands via `agentprof-instrumentation`). Tool-call steps carry no cost
  data; adding them is a separate, additive spec.
- A general-purpose Go protobuf decoder or vendoring a `.proto` schema
  (none is published for Antigravity's internal format). The field-walker
  this spec adds is intentionally narrow and reverse-engineered.
- `battle_mode_infos`, `parent_references`, `executor_metadata` tables —
  observed empty or not shown to carry cost-relevant data in the inspected
  fixture; revisit only if a future fixture shows otherwise.
- Any change to `internal/pricing/table.go`'s existing Claude rate table.
- Live-tailing or streaming Antigravity sessions; this adapter reads
  completed/in-progress `.db` files the same way `claude.Collect` reads
  JSONL transcripts — a point-in-time batch read, not a daemon.

## Acceptance criteria

- [ ] R0's fixture — a real, committed, UNMODIFIED SQLite file at
      `internal/antigravity/testdata/conversations/<cascade_id>.db` (not
      extracted rows: R1's `Collect` and the e2e criterion below both open
      it via SQLite) plus a short README noting the hand-counted ground
      truth — exists and is referenced by a `go test` in
      `internal/antigravity/...` before any task implements R2. A
      human-gated prerequisite, not a command a `/drain` worker runs
      unattended (see R0).
- [ ] `go test ./internal/antigravity/...` passes against the COMMITTED
      fixture from R0 (never a live `~/.gemini` directory, which is
      machine-specific and mutable), including: (a) direct unit tests of
      the protobuf field-walker in isolation — varint decoding, extracting
      a nested field path (e.g. `9.4`'s Timestamp), and a malformed-blob
      input skipping rather than panicking; (b) `Collect`-level
      integration tests covering R1's join + skip-on-lock/corrupt (a
      corrupted-copy fixture for the skip path), R2's fixture-backed token
      mapping, AND a fixture row's `Stack` project frame matching the
      expected basename/label from Solution item 2's field-1/field-18
      extraction rule (the untested fallback path a worker could otherwise
      ship broken); (c) `Collect` returning zero samples (not an exit
      code — see the next bullet for R6's actual exit-code assertion) for
      an empty/nonexistent `dir`.
- [ ] `go test ./...` (root package) includes a `cmd_antigravity_test.go`
      case — mirroring `cmd_claude_test.go`'s existing empty-result
      test — asserting `cmdAntigravity` exits 1 with a "no samples found"
      message for an empty/nonexistent `--antigravity-dir` (R6; this
      exit-code guard lives in `cmd_antigravity.go`, package `main`, not
      in `internal/antigravity`, since `Collect` itself has no exit code
      to set).
- [ ] `go test ./internal/pricing/...` passes against the committed
      fixture from R3 — covering the mapped display string
      (`"Gemini 3.5 Flash (Medium)"`) pricing correctly, and an unmapped
      display string returning `priced=false` with `cost_microusd`
      omitted. This test is hermetic (fixture-backed, not
      machine-state-dependent).
- [ ] `go build ./...` succeeds with the new `cmd_antigravity.go` wired
      into `main.go`'s subcommand dispatch.
- [ ] `agentprof antigravity -o summary --antigravity-dir
      internal/antigravity/testdata --days 3650` (the committed fixture at
      `internal/antigravity/testdata/conversations/<cascade_id>.db` — NOT
      a live machine path — reproducible in CI and on any worker's
      machine; `Collect` globs `<dir>/conversations/*.db`, so the
      `conversations/` subdirectory is required for this exact command to
      find the fixture) exits 0 and emits a JSON array matching
      `summary.go`'s `summaryRow` shape (R5), i.e. the exact same shape
      `agentprof claude -o summary` already emits — the end-to-end check,
      exercising the adapter against real (fixture) data the way a user
      would.
- [ ] `python3 -m pytest antigravity/.agents/skills/workboard/
      test_workboard.py` and the equivalent test path for `.claude/skills/
      workboard/` both pass, covering R4: a fabricated `agentprof
      antigravity -o summary` stdout (mocked subprocess, not a real
      binary call) whose `session` value IS a member of the passed
      `cascade_ids` must contribute a nonzero amount to
      `merge_spend`'s result, proving the id-set plumbing works — plus the
      existing independent-degrade-on-failure case for each harness. This
      mocked test proves the merge arithmetic; it does NOT prove the
      real-world equivalence the next criterion checks.
- [ ] GATING manual check (not optional, not skippable even though it
      can't run in CI — this is the only check that verifies the load-
      bearing empirical claim the whole R4 fix depends on): with a real
      Antigravity `.db` present, confirm that a `scan_antigravity()` brain-
      directory id (`~/.gemini/antigravity*/brain/<id>/`) actually equals
      that same session's `.db` basename under `conversations/` — if this
      equivalence ever breaks (e.g. a future Antigravity version renames
      one tree independently of the other), R4's id-set filter silently
      zeroes Antigravity spend again, the exact bug this spec fixes. Then
      confirm `workboard.py`'s rendered dashboard spend total changes
      (increases) once the Antigravity call is wired in, versus the
      Claude-only baseline from before this change. Depends on this
      machine's mutable `~/.gemini` state, so it is local-only and not
      part of the automated gate — but the task closing R4 must not be
      marked done without running it.

## Open questions

(none)

## Parallelization

Tasks 02 (protobuf field-walker) and 03 (Gemini pricing table) are
disjoint in `Touch` (`internal/antigravity/protowire.go` vs.
`internal/pricing/gemini_table.go`) and share no undecided design — the
walker's field paths and the pricing table's display-string map are each
fully specified in this SPEC.md already — so they run concurrently.

Task 01 (the R0 fixture) is independent of both in `Touch` too, but it is
`Status: blocked`/human-only (docs/memory/unattended-worker-tool-limits.md)
rather than a worker-dispatchable task, so it is not listed in a `- Group:`
line — it proceeds on its own (human) schedule alongside 02 and 03.

Task 04 (`Collect`) depends on all three of 01, 02, and 03 (it calls into
the walker and the pricing table, and its integration tests run against
Task 01's committed fixture) and cannot start until all three land. Tasks
05, 06, and 07 form a strict serial chain after 04 (`cmd_antigravity.go`
→ `workboard.py` dual-harness spend → the manual GATING check) — each
depends on its predecessor's code existing, so none of them parallelize
with each other or with 04.

- Group: 02, 03

## Closure (2026-07-13 verification sweep)

All Go criteria pass. The one failing workboard test was unrelated drift,
fixed on main 2026-07-13 (bd33658). Closed verified.
