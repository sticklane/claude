# tool-output-spill

A `PostToolUse` hook that keeps an oversized tool result out of the main
session's context. Past a character budget it writes the full result to a
spill file and hands Claude a short pointer plus a preview instead.

This closes wake-budget cause #5 in `.claude/rules/token-discipline.md`
("Session refresh"): a session that inlines large raw tool output re-pays for
it on every later turn. Nothing is discarded — the spill file holds the whole
result and the replacement names its path, so the session reads back only the
slice it needs.

## Why a rewrite is possible

The hook API supports replacing a tool result outright:

> `updatedToolOutput` | Replace the tool's result with this string before
> Claude processes it. Useful for redacting sensitive data or transforming
> tool output. The original result is not shown to Claude

— [Claude Code hooks reference](https://code.claude.com/docs/en/hooks),
"PostToolUse decision control". So the gate is a silent rewrite, not a
block-and-resubmit.

## Behavior

- Under budget: no output at all, exit 0. A hook that spoke on every tool
  call would churn the cached prefix each turn — the anti-pattern
  `token-discipline.md`'s cache-economics rule names.
- Over budget: stdout is one JSON object setting
  `hookSpecificOutput.updatedToolOutput` to
  `[tool output spilled: N characters…]`, the spill path, a read-back
  instruction, and the first `TOOL_OUTPUT_SPILL_PREVIEW` characters.
- Degraded input — no `jq`, no `tool_response`, malformed payload, an
  unwritable spill directory — is the same silent no-op. A guardrail must
  never break the turn it observes.
- Spill files land in `${TMPDIR:-/tmp}/claude-tool-output-spill/`; each fire
  deletes files there older than a day.

## Tuning

| Variable | Default | Meaning |
| --- | --- | --- |
| `TOOL_OUTPUT_SPILL_BUDGET` | `40000` | Spill threshold in characters (roughly 10k tokens). |
| `TOOL_OUTPUT_SPILL_PREVIEW` | `1500` | Leading characters kept inline. |

## Wiring

Shipped here, wired per user — add this to `~/.claude/settings.json`,
substituting your checkout path for `<repo>`. The matcher covers the tools
whose returns actually get large; narrow or widen it to taste.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash|Read|Agent|Workflow",
        "hooks": [
          {
            "type": "command",
            "command": "<repo>/hooks/tool-output-spill/spill-check.sh"
          }
        ]
      }
    ]
  }
}
```

## Tests

```bash
bash hooks/tool-output-spill/test.sh          # the hook's own suite
bash tests/test_tool_output_spill_hook.sh     # suite + structured-response case
```
