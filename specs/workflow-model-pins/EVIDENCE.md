# Evidence: workflow-subagent model mix, 2026-06-27 → 2026-07-11

Source: `agentprof claude --days 14` run 2026-07-11; regenerate with:

    cd agentprof && ./agentprof claude --since 2026-06-27T00:00:00Z --summary /tmp/summary.json -o /dev/null

- `agent:workflow-subagent` total: $549 / 3,886 calls / 7.13M uncached
  input tokens (the largest uncached-input mover of any agent type).
  Model mix: fable-5 2,888 calls/$486, opus 572/$38, sonnet 401/$25.
- `skill:deep-research`: $201 total — fable-5 917 calls/$167, sonnet
  453/$31, opus 52/$3, haiku 12/$0. Its workflow workers moved 2.61M
  uncached input tokens ($59) under skill:deep-research alone.
- Top workflow-subagent@fable turns: "drain the recover dark ball, use
  ultraco…" (fooszone, $94/453 calls), "/idea we should be able to take
  acftions…" ($85/441), 'claude "Read docs/research-followups…"' ($76/450).
- Contrast (pins working): `agent:agentic:scout` 10,768 haiku calls for
  $64; `agent:agentic:implementation-worker` 7,694 opus calls/$606 with
  only $13 of fable (drain's deliberate escalation).
- Mechanism: `.claude/workflows/deep-research.js` passes `effort:"low"`
  on Search (≈line 185) and Fetch (≈line 219) stages but no `model` opt —
  agents inherit the session model. Comments in the file already declare
  those stages mechanical.
