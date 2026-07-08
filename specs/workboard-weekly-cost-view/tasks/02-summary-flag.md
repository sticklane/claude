# Task 02: agentprof claude --summary (pre-aggregated JSON)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: 01
Priority: P1
Budget: 16 turns
Spec: ../SPEC.md (requirement R3)
Touch: agentprof/cmd_claude.go, agentprof/internal/, agentprof/testdata/

## Goal

`agentprof claude` accepts `--summary <path>`, writing the exact JSON shape
pinned in SPEC.md: `{by_project, by_skill, by_agent_type, by_model, totals}`
each mapping name → `{sample_type: total}`, plus top-level `sessions_added`
(distinct fresh-sample session labels, always counted from fresh only).
Frame extraction rules are the spec's: `project = Stack[0]`; `skill` =
first `^skill:` frame or exactly `(no skill)`, with non-matching samples
bucketed under `(no skill)` rather than dropped; `agent_type` = first
`^agent:` frame; `model` = last leaf frame that isn't `tool:`/`role:`/
`stage:` (forward-compatible with agentprof-instrumentation's new frames;
unknown frame kinds are ignored). With `--merge`, grouping and totals come
from the FINAL merged post-eviction set; without it, from fresh Collect()
output.

## Touch

Same Go files as task 01 (hence the dependency — same-file serialization).
The JSON shape is a CONTRACT consumed by task 03's panel: implement it
exactly as pinned in SPEC.md — any deviation must go back into the spec,
never be absorbed silently on either side of the seam.

## Steps

1. Write the failing tests first: fixture with known project/skill/agent/
   model frames asserting the full grouped shape; an `(unlinked)`-shaped
   sample (no `skill:`/`(no skill)` frame) landing in `by_skill["(no
   skill)"]` while still counting in `by_project`/`by_model`/`totals`;
   `sessions_added` equal to the fixture's distinct fresh session count,
   including `0` for an empty fresh set; with `--merge`, totals computed
   from the merged post-eviction set while `sessions_added` still counts
   fresh only.
2. Implement the grouping in agentprof (which owns the frame-hierarchy
   convention) — never by parsing `go tool pprof -top` text.
3. Wire `--summary` into `cmd_claude.go` alongside the task-01 flags;
   summary writing must also work when the merged result is empty (empty
   groups, zero totals, `sessions_added: 0`).

## Acceptance

- [ ] `cd agentprof && go test ./...` → pass, including every R3 fixture
      test listed in Steps 1.
- [ ] `cd agentprof && go run . claude --days 1 -o /tmp/wwcv-y --summary /tmp/wwcv-summary.json && python3 -c "import json; d=json.load(open('/tmp/wwcv-summary.json')); print(sorted(d))"` →
      exits 0 and prints keys including `by_agent_type, by_model,
      by_project, by_skill, sessions_added, totals`.
- [ ] `cd agentprof && gofmt -l . | wc -l` → 0.
