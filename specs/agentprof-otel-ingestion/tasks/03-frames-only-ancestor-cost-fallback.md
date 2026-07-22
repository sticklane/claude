# Task 03: Frames-only-ancestor cost fallback + multi-descendant tie-break

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: pending
Depends on: 02
Priority: P2
Budget: 18 turns
Spec: ../SPEC.md (design pt 6; Decision 4)
Touch: agentprof/internal/otel/otel.go, agentprof/internal/otel/otel_test.go, agentprof/internal/otel/testdata/

## Goal

Completes the cost-join rule (SPEC.md design pt 6) for the case where a cost
log event's `span_id` targets a **frames-only** ancestor (e.g. the
`claude_code.interaction` span) rather than a token-bearing span. The cost
attaches to the token-bearing descendant whose span time range contains the
event timestamp; if several qualify, the earliest span start wins; if none
contains it, the latest token-bearing descendant that started before the
event is used. Golden fixtures cover the single-descendant and
multi-descendant cases against this rule.

## Touch

Extends only the join logic added in Task 02 within `internal/otel/otel.go`.
Add fixtures under `internal/otel/testdata/` with
`ancestor`/`descendant`-prefixed names to avoid collision with Task 02's
`logs`/`cost` fixtures.

## Steps

1. Write failing tests first in `otel_test.go`:
   - a cost event whose `span_id` names a frames-only ancestor attaches to
     the single token-bearing descendant whose time range contains the event
     timestamp;
   - with multiple containing descendants, the earliest-start one receives
     the cost;
   - with no descendant time range containing the timestamp, the latest
     token-bearing descendant that started before the event receives it;
   - a cost event whose `span_id` matches a token-bearing span directly
     (Task 02's path) is unchanged (regression).
   Confirm they fail for the right reason (ancestor-targeted cost currently
   attaches nothing).
2. Implement the descendant resolution: given a cost record targeting span
   `S`, gather token-bearing spans transitively descended from `S` within
   the same `trace_id`; select by timestamp-containment
   (`start ≤ event_ts ≤ end`), earliest-start tie-break, then
   latest-started-before-event fallback.
3. Keep the direct-match fast path from Task 02 as the first check; only
   fall back to the descendant walk when the targeted span is frames-only.
4. Add golden fixtures under `internal/otel/testdata/` for the
   single-descendant and multi-descendant cases.

## Acceptance

Runnable commands only:

- [ ] `cd agentprof && go test ./internal/otel/ -run 'Ancestor|Descendant' -v` → new fallback + tie-break tests pass (L2)
- [ ] `cd agentprof && go test ./internal/otel/ -v` → full package green, no regression in Task 02's direct-match join (L2)
- [ ] `bash agentprof/scripts/check.sh` → exits 0
