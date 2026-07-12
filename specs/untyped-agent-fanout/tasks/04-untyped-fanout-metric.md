# Task 04: untyped_fanout guard metric

Status: pending
Depends on: ../../session-refresh-automation/tasks/02-per-session-reprime-fields.md, ../../session-refresh-automation/tasks/05-workboard-reprime-flag.md
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (requirement R4)
Touch: agentprof/internal/costsummary/, agentprof/SCHEMA.md, agent-console/

## Goal

The cost summary gains an additive `untyped_fanout` section — `calls`,
`cost_microusd`, `by_model`, `max_depth` — computed over the EXACT-match
untyped set {agent:claude, agent:agentic:claude, agent:general-purpose,
agent:agentic:general-purpose} with the pinned depth edge rule (adjacent
untyped frames; `wf:`/`stage:`/role markers transparent; any other
`agent:*` frame — explicitly `agent:claude-code-guide` — breaks the
chain). The workboard cost panel renders one line from it, omitted
gracefully when the section is absent.

## Touch

The costsummary/agent-console collisions with
`specs/session-refresh-automation/tasks/02-*` and `05-*` are expressed
as the cross-spec `Depends on:` paths above — this task admits only
after both land, so one repo-wide drain serializes them and this task
builds on the shipped `reprime_count` fields instead of merge-racing
them. Do NOT touch
`agentprof/internal/claude/` (stacks already carry the full nested agent
chain).

## Steps

1. RED: costsummary fixture asserting — a `agent:claude > agent:claude`
   sample counts with depth 2; `agent:claude > agent:scout >
   agent:claude` yields max_depth 1; `agent:claude-code-guide` samples
   are excluded entirely; by_model splits on the sample's model leaf.
2. GREEN: implement the section additively (existing field names
   unchanged; `--merge` aggregation path respected).
3. SCHEMA.md documents the section, the exact-match set, and the edge
   rule.
4. Workboard: failing renderer test first (line when section present,
   omitted when absent), then the panel line, same summary JSON path.

## Acceptance

- [ ] `cd agentprof && go test ./internal/costsummary/` → pass, including the exclusion and edge-rule cases
- [ ] `cd agentprof && go build -o agentprof . && ./agentprof claude --days 7 --summary /tmp/s.json -o /dev/null && jq -e '.untyped_fanout | has("calls") and has("cost_microusd") and has("by_model") and has("max_depth")' /tmp/s.json` → true
- [ ] `grep -c 'untyped_fanout' agentprof/SCHEMA.md` → ≥ 1
- [ ] `bash agentprof/scripts/check.sh` → green
- [ ] `bash agent-console/scripts/check.sh` → green, with the present/absent renderer cases
