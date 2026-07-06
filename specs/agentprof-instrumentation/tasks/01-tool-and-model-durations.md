# Task 01: Per-line timestamp capture + tool-call and model-call duration samples

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P1
Budget: 20 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R7's Values half)
Touch: agentprof/internal/, agentprof/testdata/

<!-- PLAN (delete at close-out)
Files:
1. internal/claude/duration_test.go (NEW) — failing tests first: R1 known-delta
   tool duration, R1 negative-delta clamp→0, R2 unresolved tool_use→tool:(pending)
   empty Values, R3 model-call duration_ms present on all but first sample.
2. internal/claude/claude.go — (a) add Name to contentBlock; (b) capture
   tool_result ts per transcript (toolResults map) + per-line prevTs tracking for
   model-call duration; (c) capture tool_use {id,name} on deduped response
   (toolCalls); (d) compute model-call duration_ms on response (omit first per
   transcript); (e) emit tool:<name>/tool:(pending) samples in collect() with
   leaf replaced; clamp0 helper. tool_use_message_ts == response.time (same line).
3. internal/pprofenc/pprofenc.go — unitFor: duration_ms → milliseconds. SCHEMA.md
   table row.
4. Update existing fixture-count tests + testdata/claude-dir.expected.json for the
   3 new tool samples (sess-0001) and duration_ms totals: claude_test.go counts
   10→13 and window 6→9, add duration_ms to totals want, add 3 tool stacks;
   cmd_claude_test.go 10→13.
Fixture-derived numbers: tool:Workflow dur=15000 (toolu_W), toolu_A→pending,
agent-W toolu_WS→pending; model durs: sess1 msg_a2=45000; sess2 b2=60000,
reqfb=60000, b3=180000; grand duration_ms total=360000.
Risk: brittle fixture recomputation — verify every number against parser output.
-->

## Goal

The agentprof parser retains per-line timestamps it currently discards, pairs
each `tool_use` block (assistant line) with its `tool_result` (user line,
matched by id), and emits: (a) one NEW sample per pair with a `tool:<name>`
leaf at the model-name leaf's position and
`duration_ms = clamp0(tool_result_ts - tool_use_message_ts)`; (b) a
`tool:(pending)` sample with an EMPTY Values map for unresolved `tool_use`s;
(c) `duration_ms = clamp0(this_response_ts - previous_ts)` added to every
existing model-call sample except the first sample of each transcript, where
`previous_ts` is the previous parser-captured line per SPEC.md's
"Model-call duration" paragraph. No existing Values key is removed or
altered (R7's Values constraint).

## Touch

All Go work stays under `agentprof/` (parser in `internal/claude/`, plus
whatever sample-type/schema registration the new `duration_ms` value key
needs elsewhere under `internal/`). Do NOT touch `.claude/skills/`,
`antigravity/`, or `.claude-plugin/` — those belong to task 03. Do NOT add
marker (`role:`/`stage:`) handling — that is task 02, which edits the same
parser files after this task.

## Steps

1. Write the failing tests first, on fixture transcripts under
   `agentprof/testdata/` (or the package's existing fixture location):
   a `tool_use`/`tool_result` pair with a known timestamp delta asserting
   the exact `duration_ms`; a negative-delta (clock-skew) pair asserting
   `duration_ms == 0`; an unresolved `tool_use` asserting a
   `tool:(pending)` leaf with an empty Values map by inspecting the parsed
   `[]schema.Sample` slice directly (NEVER via `go tool pprof` output — a
   value-less sample is invisible there by design); a model-call
   `duration_ms` test including the first-sample-omits rule.
2. Extend the parser (around `claude.go:518` and `claude.go:706-728`,
   line refs approximate) to retain per-line timestamps for assistant
   messages AND `tool_result`-carrying user lines; this is NEW capture, not
   a reuse of the existing `toolUses`/`spawn` id-matching.
3. Emit the new `tool:<name>` samples (stack = parent model-call sample's
   stack with the model-name leaf replaced by `tool:<name>`, a sibling
   position, never nested under the model leaf) and the `tool:(pending)`
   no-values samples. Concurrent tool calls each get their own sample;
   overlap summing above wall-clock is accepted and documented in a code
   comment only if the code can't show it.
4. Add `duration_ms` to existing model-call samples per R3; lines the
   parser already skips remain skipped and are never "previous".
5. Register `duration_ms` wherever sample-value types are declared so
   `-sample_index=duration_ms` works in pprof output.

## Acceptance

- [ ] `cd agentprof && go test ./...` → pass, including the new R1/R3
      fixture tests (exact known-delta match; negative delta → exactly 0).
- [ ] `cd agentprof && go test ./... -run 'Pending'` → pass: unresolved
      `tool_use` yields `tool:(pending)` with empty Values, asserted on the
      parsed sample slice directly (R2).
- [ ] `cd agentprof && go test ./... -run 'Duration'` → pass: model-call
      `duration_ms` present on all but each transcript's first sample (R3).
- [ ] `cd agentprof && gofmt -l . | wc -l` → 0.
