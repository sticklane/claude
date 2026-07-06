# agentprof: tool-call latency + cheap subskill markers

Status: open
Priority: P1

## Problem

agentprof's profiles today carry six sample types (`cost_microusd`,
`input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`,
`calls`) but no wall-clock timing at all. `claude.go:518` parses each
assistant response's RFC3339Nano `timestamp` into `response.time`, but
that time is discarded at sample-output time (`claude.go:706-728`) —
`Sample.Time` records when the response happened, never how long
anything took, and NOTHING in the current parser captures a `tool_result`
line's timestamp or a `tool_use` block's own timestamp as a distinct
value (both live inside assistant/user JSONL lines the parser doesn't
currently retain per-line timing for). A real transcript confirms the
raw data exists to build this from scratch: `tool_use` and its matching
`tool_result` are two distinct JSONL lines with independent timestamps,
paired by the tool_use `id` — one observed pair had an 8ms delta — but
capturing that pairing with timestamps is NEW parser work, not a reuse of
any existing mechanism (the existing `toolUses`/`spawn` id-matching in
`claude.go` links tool_use ids to subagent spawns, and carries no
timestamp).

Separately, the stack frames a profile shows today are coarse:
`skill:<name>` / `agent:<type>` / a model-name leaf. For a multi-stage
skill like `/drain` (inventory, dispatch, collect-the-verdict, baton-pass,
batch-interview — `drain/SKILL.md`'s five `##`-headed steps, including the
`## 3a` baton-pass subsection) or `/build` (load, plan, implement, verify,
close-out — `build/SKILL.md`'s five `##`-headed steps), the profile can't
show which STAGE consumed the cost/tokens/time — only that the skill as a
whole did. Reconstructing that today would mean an LLM re-reading the
transcript (expensive, contradicts the point of a cheap profile) or
hand-reading raw JSONL.

## Solution

**Tool-call duration** (`internal/claude`, new capture — not a reuse of
existing id-matching): for each `tool_use` block in an assistant message,
record that message's timestamp; for its matching `tool_result` (matched
by `id`, in a `type:"user"` JSONL line — a new per-line timestamp capture,
since the parser doesn't retain this today), record that line's
timestamp. Emit a *second*, independent sample alongside the existing
model-call sample:

- Stack: identical to the parent assistant message's model-call sample,
  except the leaf model-name frame is replaced with `tool:<name>` (a
  SIBLING of the model-name leaf's position, never nested under it) —
  `<name>` is the tool's own name from the `tool_use` block (e.g. `Bash`,
  `Read`, `WebFetch`).
- Values: `{"duration_ms": clamp0(tool_result_ts - tool_use_message_ts)}`
  where `clamp0(d) = max(0, d.Milliseconds())` — a non-positive delta
  (clock skew, out-of-order lines) clamps to exactly `0`, never negative;
  a real sub-millisecond call also reports `0` (accepted rounding, not an
  error).
- A `tool_use` with no matching `tool_result` anywhere in the transcript
  (cancelled/interrupted) emits a sample with a `tool:(pending)` leaf and
  an EMPTY Values map — no `duration_ms` key at all, never fabricated.
  Because this sample carries no sample-type value, it is invisible to
  `go tool pprof -top`/any `-sample_index` view by design; verify its
  existence by inspecting the parsed `[]schema.Sample` slice directly in
  a Go test, never via pprof CLI output.
- Concurrent tool calls in one assistant turn each get their own
  independently-timed sample; their `duration_ms` values MAY sum to more
  than the turn's real wall-clock span under concurrency — accepted,
  documented, not solved here (identical in kind to how cost/tokens
  already sum per call regardless of overlap).

**Model-call duration**: each existing model-call sample gains a
`duration_ms` value: `clamp0(this_response_ts - previous_ts)`, where
`previous_ts` is the timestamp of the immediately preceding line in the
same transcript file for which this spec's own changes give the parser a
captured timestamp — i.e., the previous assistant message, OR (once this
spec's tool_result capture lands) the previous user message carrying a
`tool_result`. Lines the parser already skips today (meta/sidecar lines)
remain skipped and are never "previous" for this purpose. The first
sample in a transcript has no previous line — omit `duration_ms` for that
one sample only, in every session.

**Subskill markers**: two independent, deterministic marker conventions,
each with an HTML-comment DETECTION pattern in transcript text and a
distinct, explicit INSERTED FRAME name (following the repo's existing
`prefix:value` frame convention — `skill:`, `agent:`, `tool:` — the marker
text and the frame name are NOT the same string). Both are matched by
agentprof via plain string/regex — no LLM call — and both are scoped to
drain and build only for this spec (not pushed to all ~25 skills):

1. **Role marker** (drain only, detection pattern
   `<!-- agentprof:role=(?P<role>[a-z0-9-]+) -->`, inserted frame
   `role:<role>`): drain's five dispatch call sites each get their own
   added instruction naming a literal, already-filled-in marker line to
   prepend to that specific dispatch's prompt before it's sent —
   `worker-attempt1`, `worker-relaunch`, `worker-tournament-t1`,
   `worker-tournament-t2`, `worker-tournament-t3` respectively. These
   five call sites are NOT all in one place: the attempt-1 base dispatch
   instruction lives in `drain/SKILL.md`'s step 2 (Dispatch); the
   attempt-2 relaunch and all three tournament-entrant dispatches are
   built in step 3 (Collect the verdict, where the slot-machine/
   tournament routing lives) at `drain/SKILL.md:208` (relaunch) and
   `:218-222` (the three tournament entrants) — each of those gets its
   own added instruction at its own call site, not bundled into step 2.
   None of the five are a single shared placeholder in `reference.md`;
   the base worker-prompt body in `reference.md:245` stays role-agnostic
   and unedited, since it's reused verbatim across variants and a single
   embedded literal there could not distinguish them. The marker lands in
   the DISPATCHED SUB-AGENT's own transcript. Insertion rule: the
   `role:<role>` frame is
   inserted as the immediate child of that sub-agent's spawn-prefix,
   immediately before its `agent:<type>` frame — e.g. a normal subagent
   sample's stack `[...spawn-prefix, "agent:general-purpose",
   "claude-sonnet-5"]` becomes `[...spawn-prefix, "role:worker-attempt1",
   "agent:general-purpose", "claude-sonnet-5"]` from the marker's position
   in that sub-agent's transcript onward.
2. **Stage marker** (drain and build, detection pattern
   `<!-- agentprof:stage=(?P<stage>[a-z0-9-]+) -->`, inserted frame
   `stage:<stage>`): `drain/SKILL.md`'s five top-level steps and
   `build/SKILL.md`'s five top-level steps each gain an instruction to
   open with the matching literal line EVERY TIME that step is entered —
   `stage=inventory`, `stage=dispatch`, `stage=collect-verdict`,
   `stage=baton-pass`, `stage=batch-interview` for drain (five, including
   the `## 3a` baton-pass subsection as its own stage); `stage=load`,
   `stage=plan`, `stage=implement`, `stage=verify`, `stage=close-out` for
   build. Drain's step 3 explicitly loops back to step 2 while anything
   is dispatchable (`SKILL.md`'s "Loop to step 2" instruction), so
   `stage=dispatch` and `stage=collect-verdict` each re-fire on every
   loop iteration, not once per session — this is required, not
   incidental: the parser rule "until the next `stage=` marker" means a
   single per-session emission would misattribute every iteration after
   the first to whichever stage last emitted. This marker lands in the
   ORCHESTRATING session's OWN transcript (the main session running
   `/drain` or `/build`). Insertion rule: the
   `stage:<stage>` frame is inserted as the immediate child of the
   `skill:<name>` frame, immediately before whatever frame currently
   follows it — e.g. a model-call sample's stack `[project, turn, skill,
   "main", model]` becomes `[project, turn, skill, "stage:dispatch",
   "main", model]`; a tool-call sample under the same context becomes
   `[project, turn, skill, "stage:dispatch", "main", "tool:Bash"]` — from
   the marker's position in the ORCHESTRATOR's transcript onward, until
   the next `stage=` marker or transcript end.

agentprof's parser scans assistant-message text for either detection
pattern and, when found, inserts the corresponding frame at the rule
above for every sample from that point in the transcript until the next
marker of the same kind or end of transcript. A transcript with neither
marker (any skill other than drain/build, and every transcript predating
this change) is parsed to the exact stack shapes agentprof produces
today — this is a strictly additive parser change.

## Requirements

- **R1**: Each `tool_use`/`tool_result` pair (matched by `id`, a NEW
  timestamp capture on both the assistant line's `tool_use` block and the
  user line's `tool_result` block) produces one new sample with a
  `tool:<name>` leaf frame at the model-name leaf's position, and
  `duration_ms = clamp0(...)` in its Values map.
- **R2**: A `tool_use` with no matching `tool_result` produces a
  `tool:(pending)` frame with an EMPTY Values map (no fabricated
  duration); verified by inspecting the parsed sample slice directly in a
  Go test, never via `go tool pprof` output.
- **R3**: Each existing model-call sample gains
  `duration_ms = clamp0(this_response_ts - previous_ts)`, where
  `previous_ts` is defined exactly as in Solution's "Model-call duration"
  paragraph; the first sample in each transcript omits `duration_ms`.
- **R4**: `drain/SKILL.md` gains five distinct, hardcoded marker-line
  instructions, one per dispatch call site — the attempt-1 instruction in
  step 2 (Dispatch), governing BOTH of step 2's attempt-1 launch paths
  (the single-worker launch and the concurrent group-throughput launch
  that sends all group members in one message — both are "attempt-1,"
  neither gets a different role value); the relaunch and three
  tournament-entrant instructions each at their own call site in step 3
  (Collect the verdict, `SKILL.md:208` and `:218-222`) — each naming its
  own literal `<!-- agentprof:role=<role> -->` value to prepend to that
  dispatch's prompt. `reference.md`'s shared worker-prompt body is NOT
  edited.
- **R5**: `drain/SKILL.md`'s five top-level steps (inventory, dispatch,
  collect-the-verdict, baton-pass, batch-interview) and `build/SKILL.md`'s
  five top-level steps (load, plan, implement, verify, close-out) each
  gain an instruction to open with the matching
  `<!-- agentprof:stage=<name> -->` line EVERY TIME that step is entered
  (not once per session — see Solution's stage-marker paragraph for why
  drain's step 2/3 loop makes this required).
- **R8**: `antigravity/.agents/workflows/drain.md` and `.../build.md`
  (the mirrors of `drain/SKILL.md` and `build/SKILL.md`) receive the
  equivalent stage-marker and role-marker instructions in the same
  commit, per CLAUDE.md's mirroring convention; `.claude-plugin/
  plugin.json`'s version is bumped. If a reviewer determines the mirror
  genuinely doesn't apply (e.g. antigravity's workflow files have no
  analogous dispatch-prompt construction step), that's a documented
  carve-out recorded as evidence, not a silent skip — CLAUDE.md's own
  convention names this exact failure mode ("an unlisted mirror silently
  ships un-mirrored").
- **R6**: agentprof's parser detects both marker patterns via regex and
  inserts the corresponding frame per the exact position rules in
  Solution; a transcript containing neither marker gets neither a
  `role:` nor a `stage:` frame anywhere in its stacks (marker detection
  is strictly opt-in per transcript).
- **R7**: For a markerless transcript, every EXISTING model-call sample's
  Stack is byte-identical to today's parser's output, and no EXISTING
  Values key is removed or altered in meaning (only added to: `duration_ms`
  per R3). This is NOT a claim that the sample set is unchanged overall —
  R1 adds brand-new `tool:`-leaf samples that didn't exist before, in
  every transcript, marker or not; R7 constrains only the pre-existing
  model-call samples, which is what makes markers themselves opt-in
  (R6) while duration tracking (R1, R3) is unconditional and universal.

## Out of scope

- Extending markers to any skill other than drain and build.
- Extending the LLM turn-namer (`internal/naming`) to infer stage
  boundaries automatically — contradicts the "cheap, no large token
  spend" goal; markers are deterministic text, not model inference.
- Any change to `agentprof claude --days N`'s existing cost/token sample
  types — this spec only adds new sample types and frames.
- Reconciling concurrent tool-call duration overlap into a single
  wall-clock-accurate number — documented as an accepted characteristic.
- The `--since`/`--merge` incremental-caching work — that's
  `specs/workboard-weekly-cost-view/SPEC.md`, which depends on this spec
  only for richer data (once it lands, the weekly view picks up
  `duration_ms`/`tool:`/`stage:`/`role:` automatically with no further
  change there), never for its own core mechanism.
- Verifying marker EMISSION at runtime beyond a single hand-run E2E check
  (acceptance criteria's last item) — whether the orchestrating model
  actually follows the new SKILL.md instruction each run is a prompt-
  following question, not something a deterministic test can force; the
  grep-based acceptance criteria only verify the INSTRUCTION TEXT exists,
  not that every future run emits it.

## Acceptance criteria

- [ ] `go test ./...` (agentprof) passes, including new tests for R1/R3
      using a fixture transcript with a `tool_use`/`tool_result` pair
      with a known timestamp delta, asserting the emitted sample's
      `duration_ms` matches exactly; a second fixture with a negative
      delta (clock skew) asserts `duration_ms == 0` (R1, R3's clamp rule).
- [ ] A fixture with an unresolved `tool_use` (no matching `tool_result`)
      produces a `tool:(pending)` sample with an empty Values map,
      asserted directly on the parsed `[]schema.Sample` slice (R2).
- [ ] A fixture transcript containing a
      `<!-- agentprof:role=worker-attempt1 -->` marker produces samples
      with a `role:worker-attempt1` frame inserted immediately before
      `agent:<type>` in that sub-agent's stack; a fixture with no marker
      produces the pre-existing stack shape unchanged (R4, R6, R7).
- [ ] A fixture transcript containing a
      `<!-- agentprof:stage=dispatch -->` marker produces samples with a
      `stage:dispatch` frame inserted immediately after `skill:<name>`
      and before `main`; samples before the marker (or after a later
      marker) attach to their own respective stage frames, not
      `dispatch` (R5, R6).
- [ ] `grep -c 'agentprof:role=' .claude/skills/drain/SKILL.md` → 5 (R4).
- [ ] `grep -c 'agentprof:stage=' .claude/skills/drain/SKILL.md` → 5 and
      `grep -c 'agentprof:stage=' .claude/skills/build/SKILL.md` → 5 (R5).
- [ ] `antigravity/.agents/workflows/drain.md` and `.../build.md` carry
      the equivalent marker instructions (or the implementation's
      evidence names an explicit, reviewed carve-out for why not), and
      `.claude-plugin/plugin.json`'s version is higher than before (R8).
- [ ] **Manual-pending** (emission depends on runtime prompt-following,
      not a deterministic check): run `/drain` once for real, then
      `agentprof claude --days 1 -o /tmp/x.pb.gz`; `go tool pprof -top
      -sample_index=duration_ms /tmp/x.pb.gz` shows at least one `tool:`
      frame with non-zero cumulative duration, recorded as evidence
      (screenshot or `-top` text output), not an automated pass/fail.

## Open questions

(none)
