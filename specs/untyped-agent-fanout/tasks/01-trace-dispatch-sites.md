# Task 01: Trace the untyped dispatch sites

Status: in-progress
Depends on: none
Priority: P0
Budget: 12 turns
Spec: ../SPEC.md (requirement R1)
Touch: specs/untyped-agent-fanout/EVIDENCE.md

## Goal

`EVIDENCE.md` names, for every `agent:claude` chain ≥2 deep in sessions
`6fddf102-f06a-4562-bc20-14742aa17582` and
`80161f1c-8c2c-4bc3-a8d5-a4afb10ce3d4`, the dispatch site (skill text,
freehand orchestrator prompt, FleetView default, or harness behavior) or
an explicit "unresolved" disposition — plus each chain's depth, inherited
model, and cost. This is the spec's riskiest-assumption probe: task 02's
fixes are only as good as this attribution.

## Touch

Writes EVIDENCE.md only; everything else is read-only (pinned samples at
`specs/untyped-agent-fanout/evidence-samples-2026-07-11.jsonl.gz`,
transcripts under `~/.claude/projects/` while they last, toolkit skill
text). Any additional committed profile evidence follows the
pinned-evidence denylist rule in agentprof/README.md.

## Steps

1. `gunzip -k` the pinned samples; group `agent:claude` samples by
   `agent_id` and stack to enumerate the chains and their costs.
2. For each chain, locate the spawn in the session transcripts (the
   parent's Agent tool calls; agent sidecar files agent-<id>.jsonl) and
   classify the dispatch site. Use the untyped set and depth edge rule
   exactly as ../SPEC.md R4 pins them (exact-match enumeration;
   `agent:claude-code-guide` is typed).
3. Write EVIDENCE.md: one row per chain — site, depth, model, cost,
   proposed fix owner (task 02) or disposition.

## Acceptance

- [ ] `test -f specs/untyped-agent-fanout/EVIDENCE.md` → exists
- [ ] `grep -c 'dispatch site\|Dispatch site' specs/untyped-agent-fanout/EVIDENCE.md` → ≥ 1, and every chain row carries a site or the literal `unresolved`
- [ ] EVIDENCE.md's chain count is reconciled against the pinned samples (state the count and the jq/command used to derive it in the file)
