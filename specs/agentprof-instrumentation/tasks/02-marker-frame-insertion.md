# Task 02: Role/stage marker detection and frame insertion in the parser

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: 01
Priority: P1
Budget: 16 turns
Spec: ../SPEC.md (requirements R6, R7)
Touch: agentprof/internal/, agentprof/testdata/

## Goal

agentprof's parser detects the two marker patterns in assistant-message text
via plain regex — `<!-- agentprof:role=(?P<role>[a-z0-9-]+) -->` and
`<!-- agentprof:stage=(?P<stage>[a-z0-9-]+) -->` — and inserts the
corresponding frame (`role:<role>` immediately before the sub-agent's
`agent:<type>` frame; `stage:<stage>` immediately after the orchestrator's
`skill:<name>` frame) into every sample from the marker's position until the
next marker of the same kind or transcript end. A transcript with neither
marker parses to stacks byte-identical to today's output (markers are
strictly opt-in). No LLM call anywhere.

## Touch

Same parser files as task 01 (hence the dependency — same-file edits must
serialize). Do NOT touch `.claude/skills/`, `antigravity/`, or
`.claude-plugin/` — the marker-emitting instructions are task 03, and this
parser work must not assume they exist (fixtures carry the marker text).

## Steps

1. Write the failing tests first, on fixtures:
   (a) a sub-agent transcript containing
   `<!-- agentprof:role=worker-attempt1 -->` asserting stacks like
   `[...spawn-prefix, "role:worker-attempt1", "agent:general-purpose",
   <model>]`; (b) an orchestrator transcript with
   `<!-- agentprof:stage=dispatch -->` followed later by a second
   `stage=` marker, asserting samples between the two attach to
   `stage:dispatch` (inserted between `skill:<name>` and the frame that
   follows it, e.g. `main`) and samples after the second marker attach to
   the new stage — for both model-call and `tool:` samples; (c) a
   markerless fixture asserting every pre-existing model-call sample's
   Stack is byte-identical to the pre-change parser output (R7).
2. Implement detection + insertion per SPEC.md's exact position rules;
   scope: `role:` applies within the transcript that contains the marker
   (the dispatched sub-agent's own transcript), `stage:` within the
   orchestrating session's own transcript.
3. Keep the change strictly additive: no existing frame renamed, reordered,
   or removed for markerless input.

## Acceptance

- [ ] `cd agentprof && go test ./...` → pass, including the role-marker,
      stage-marker (with stage-boundary handoff), and markerless
      byte-identical-stack fixture tests (R6, R7).
- [ ] `cd agentprof && gofmt -l . | wc -l` → 0.
