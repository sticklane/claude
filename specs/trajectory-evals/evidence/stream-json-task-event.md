# stream-json Task-dispatch event capture

Run by the drain orchestrator (task's own acceptance text designates this
capture as "human-launched or orchestrator-run").

## Command

```
claude -p --output-format stream-json --verbose --dangerously-skip-permissions \
  "Use the Task tool to dispatch a subagent of subagent_type 'scout' with the \
   prompt 'list the files in /tmp and report back in one sentence'. Just do \
   this one tool call and report the result." > stream_capture.jsonl
```

Run date: 2026-07-22.

## Verbatim JSONL tool_use event line

```json
{"type":"assistant","message":{"model":"claude-fable-5","id":"msg_011CdGfokCUsFgypq4nUjhXD","type":"message","role":"assistant","content":[{"type":"tool_use","id":"toolu_013Cns3STkqY8hsSvXCQhJok","name":"Agent","input":{"description":"List files in /tmp","prompt":"list the files in /tmp and report back in one sentence","subagent_type":"agentic:scout","run_in_background":false},"caller":{"type":"direct"}}],"stop_reason":null,"stop_sequence":null,"stop_details":null,"usage":{"input_tokens":2,"cache_creation_input_tokens":17333,"cache_read_input_tokens":15109,"cache_creation":{"ephemeral_5m_input_tokens":0,"ephemeral_1h_input_tokens":17333},"output_tokens":2,"service_tier":"standard","inference_geo":"not_available"},"diagnostics":null,"context_management":null},"parent_tool_use_id":null,"session_id":"94e19d2e-33c3-4a07-ac8a-d13bdc25bb6d","uuid":"f72b4575-2bd6-4c9a-aa6b-1d433f4af7d7","timestamp":"2026-07-22T07:04:22.878Z","request_id":"req_011CdGfoiT4ezpyRWKPtpVTB"}
```

## Finding

Two assumptions in the existing grep patterns were wrong:

1. **Field value is plugin-namespaced**: the real `subagent_type` value is
   `"agentic:scout"`, not the bare `"scout"` the assumed pattern expected.
   The old pattern `"subagent_type"[[:space:]]*:[[:space:]]*"scout"`
   requires the value to be exactly `"scout"` and does **not** match
   `"agentic:scout"` — this was a real false-fail risk, not just a
   theoretical one as the task's "the substring match still works" hedge
   assumed.
2. The tool `name` is `"Agent"` in this harness version, not `"Task"` —
   irrelevant to the shipped grep (which only checks `subagent_type`, not
   `name`), noted for completeness.

## Fix applied

Widened the pattern to accept an optional `<namespace>:` prefix before
`scout`, in all three carriers (kept consistent per this task's own
acceptance criterion 2 and CLAUDE.md's mirror convention):

```
"subagent_type"[[:space:]]*:[[:space:]]*"([A-Za-z0-9_-]+:)?scout"
```

- `evals/breakdown/02-scout-delegation/assert.sh`
- `.claude/skills/evals/reference.md`
- `codex/.agents/skills/evals/SKILL.md` (inline prose example)
