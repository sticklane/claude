# tool-output-spill

A `PostToolUse` hook that keeps an oversized `Bash` result out of the main
session's context. Past a character budget it writes the full field to a
spill file and hands Claude the same Bash output object with that field
replaced by a short pointer plus a preview.

This closes wake-budget cause #5 in `.claude/rules/token-discipline.md`
("Session refresh"): a session that inlines large raw tool output re-pays for
it on every later turn. Nothing is discarded — the spill file holds the whole
field and the replacement names its path, so the session reads back only the
slice it needs.

## Why a rewrite is possible

The [Claude Code hooks reference](https://code.claude.com/docs/en/hooks),
"PostToolUse decision control", documents a replacement field:

> `updatedToolOutput` | Replaces the tool's output with the provided value
> before it is sent to Claude. The value must match the tool's output shape

So the gate is a silent rewrite, not a block-and-resubmit.

## Why the matcher is `Bash` only

The output-shape requirement is the single most important constraint on this
mechanism. The same page's Warning, verbatim:

> The replacement value must match the tool's output shape. Built-in tools
> return structured objects rather than plain strings. For example, `Bash`
> returns an object with `stdout`, `stderr`, `interrupted`, and `isImage`
> fields. For built-in tools, a value that doesn't match the tool's output
> schema is ignored and the original output is used. MCP tool output is
> passed through without schema validation. Stripping error details that
> Claude needs can cause it to proceed on a false assumption.

`Bash` is the one built-in tool whose output schema the docs establish, so it
is the one tool this hook rewrites: the replacement is the full
`{stdout, stderr, interrupted, isImage}` object with only the over-budget
field(s) swapped for a pointer; `stderr`, `interrupted`, and `isImage` are
otherwise preserved so no error detail is stripped. `Read`, `Agent`, and
`Workflow` returns also get large, but their output schemas are not
documented — a guessed replacement would be silently ignored, leaving a hook
that looks installed and does nothing — so the hook exits silently for any
other tool, even if the matcher is widened. Extending coverage means
establishing a tool's real output schema first (or, for MCP tools, using the
documented unvalidated pass-through), not loosening that guard.

## Behavior

- Under budget: no output at all, exit 0. A hook that spoke on every tool
  call would churn the cached prefix each turn — the anti-pattern
  `token-discipline.md`'s cache-economics rule names.
- Over budget (`stdout` and `stderr` are measured independently): stdout is
  one JSON object setting `hookSpecificOutput.updatedToolOutput` to the Bash
  output object, where each over-budget field becomes
  `[Bash <field> spilled: N characters…]`, the spill path, a read-back
  instruction, and the first `TOOL_OUTPUT_SPILL_PREVIEW` characters.
- Non-`Bash` tools, and degraded input — no `jq`, no `tool_response`,
  malformed payload, an unwritable spill directory — are the same silent
  no-op. A guardrail must never break the turn it observes.
- Spill files land in `${TMPDIR:-/tmp}/claude-tool-output-spill/`; each fire
  deletes files there older than a day.

## Tuning

| Variable | Default | Meaning |
| --- | --- | --- |
| `TOOL_OUTPUT_SPILL_BUDGET` | `40000` | Spill threshold in characters (roughly 10k tokens). |
| `TOOL_OUTPUT_SPILL_PREVIEW` | `1500` | Leading characters kept inline. |

## Wiring

Shipped here, wired per user — add this to `~/.claude/settings.json`,
substituting your checkout path for `<repo>`.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
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
bash tests/test_tool_output_spill_hook.sh     # suite + output-schema case
```
