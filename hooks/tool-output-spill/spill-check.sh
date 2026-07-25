#!/usr/bin/env bash
# tool-output-spill: PostToolUse hook that keeps an oversized tool result out
# of the main session's context. Past a character budget it writes the full
# result to a spill file and returns a short pointer-plus-preview in its
# place, via the documented PostToolUse field:
#
#   "updatedToolOutput | Replace the tool's result with this string before
#    Claude processes it. Useful for redacting sensitive data or transforming
#    tool output. The original result is not shown to Claude"
#   — https://code.claude.com/docs/en/hooks
#
# This is wake-budget cause #5 (.claude/rules/token-discipline.md, "Session
# refresh"): a main session that inlines large raw tool output pays for it on
# every later turn. Nothing is lost — the spill file holds the whole result,
# and the replacement names its path so the session reads back only the slice
# it needs.
#
# Under budget the hook emits nothing at all and exits 0, so a stable cached
# prefix is never churned by a per-call reminder (token-discipline.md's
# cache-economics rule). Every degraded input — no jq, no tool_response, a
# malformed payload, an unwritable spill directory — is the same silent
# no-op: a guardrail must never break the turn it observes.
#
# Tunable via environment:
#   TOOL_OUTPUT_SPILL_BUDGET   spill threshold, characters (default 40000,
#                              roughly 10k tokens)
#   TOOL_OUTPUT_SPILL_PREVIEW  leading characters kept inline (default 1500)
set -u

BUDGET="${TOOL_OUTPUT_SPILL_BUDGET:-40000}"
PREVIEW="${TOOL_OUTPUT_SPILL_PREVIEW:-1500}"

command -v jq >/dev/null 2>&1 || exit 0

payload="$(cat)"

# One pass for both the size decision and the spill filename. A non-string
# tool_response (Read, Agent, Workflow return objects) is measured and stored
# as its compact JSON — the same text that would otherwise reach the model.
measure='[((.tool_response // "") | (if type == "string" then . else tojson end) | length),
          (.tool_name // "tool")] | @tsv'
IFS=$'\t' read -r size tool <<<"$(printf '%s' "$payload" | jq -r "$measure" 2>/dev/null)"

case "${size:-}" in '' | *[!0-9]*) exit 0 ;; esac
[ "$size" -ge "$BUDGET" ] || exit 0

dir="${TMPDIR:-/tmp}/claude-tool-output-spill"
mkdir -p "$dir" 2>/dev/null || exit 0
find "$dir" -type f -mtime +1 -delete 2>/dev/null

tool="${tool//[^A-Za-z0-9_-]/}"
spill="$dir/${tool:-tool}-$(date +%Y%m%dT%H%M%S)-$$.txt"

printf '%s' "$payload" |
  jq -j '(.tool_response // "") | if type == "string" then . else tojson end' \
    >"$spill" 2>/dev/null || exit 0
[ -s "$spill" ] || exit 0

replacement="$(
  printf '[tool output spilled: %s characters, past the %s-character context budget]\n' "$size" "$BUDGET"
  printf 'Full result: %s\n' "$spill"
  printf 'Read back only the slice you need (Read with offset/limit, or grep over that path) rather than re-running the tool.\n\n'
  printf -- '--- first %s characters ---\n' "$PREVIEW"
  head -c "$PREVIEW" "$spill"
)"

jq -n --arg out "$replacement" \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", updatedToolOutput: $out}}'
