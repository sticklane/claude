#!/usr/bin/env bash
# tool-output-spill: PostToolUse hook that keeps an oversized Bash result out
# of the main session's context. Past a character budget it writes the full
# field to a spill file and replaces it with a short pointer-plus-preview via
# the documented PostToolUse field:
#
#   "`updatedToolOutput` | Replaces the tool's output with the provided value
#    before it is sent to Claude. The value must match the tool's output
#    shape"
#   — https://code.claude.com/docs/en/hooks, "PostToolUse decision control"
#
# The shape requirement is load-bearing: "For built-in tools, a value that
# doesn't match the tool's output schema is ignored and the original output
# is used" (same page, Warning). So the replacement is emitted as the Bash
# output object — {stdout, stderr, interrupted, isImage}, the one built-in
# shape the docs establish — with only the over-budget field(s) rewritten.
# Any other tool is a silent no-op: guessing an undocumented schema would be
# silently ignored, leaving a hook that looks installed and does nothing.
#
# This is wake-budget cause #5 (.claude/rules/token-discipline.md, "Session
# refresh"): a main session that inlines large raw tool output pays for it on
# every later turn. Nothing is lost — the spill file holds the whole field,
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

sizes="$(printf '%s' "$payload" | jq -r '
  select(.tool_name == "Bash") | .tool_response
  | select(type == "object")
  | [((.stdout // "") | tostring | length), ((.stderr // "") | tostring | length)]
  | @tsv' 2>/dev/null)"
[ -n "$sizes" ] || exit 0
IFS=$'\t' read -r stdout_size stderr_size <<<"$sizes"
case "${stdout_size:-}${stderr_size:-}" in '' | *[!0-9]*) exit 0 ;; esac
[ "$stdout_size" -ge "$BUDGET" ] || [ "$stderr_size" -ge "$BUDGET" ] || exit 0

dir="${TMPDIR:-/tmp}/claude-tool-output-spill"
mkdir -p "$dir" 2>/dev/null || exit 0
find "$dir" -type f -mtime +1 -delete 2>/dev/null

spill_field() { # spill_field <stdout|stderr> <size> -> pointer text on stdout
  local field="$1" size="$2" spill
  spill="$dir/Bash-$field-$(date +%Y%m%dT%H%M%S)-$$.txt"
  printf '%s' "$payload" |
    jq -j ".tool_response.$field // \"\" | tostring" >"$spill" 2>/dev/null || return 1
  [ -s "$spill" ] || return 1
  printf '[Bash %s spilled: %s characters, past the %s-character context budget]\n' \
    "$field" "$size" "$BUDGET"
  printf 'Full result: %s\n' "$spill"
  printf 'Read back only the slice you need (Read with offset/limit, or grep over that path) rather than re-running the command.\n\n'
  printf -- '--- first %s characters ---\n' "$PREVIEW"
  head -c "$PREVIEW" "$spill"
}

new_stdout="" new_stderr=""
if [ "$stdout_size" -ge "$BUDGET" ]; then
  new_stdout="$(spill_field stdout "$stdout_size")" || exit 0
fi
if [ "$stderr_size" -ge "$BUDGET" ]; then
  new_stderr="$(spill_field stderr "$stderr_size")" || exit 0
fi

printf '%s' "$payload" | jq -c \
  --arg so "$new_stdout" --arg se "$new_stderr" \
  --argjson ro "$([ -n "$new_stdout" ] && echo true || echo false)" \
  --argjson re "$([ -n "$new_stderr" ] && echo true || echo false)" '
  .tool_response as $r |
  {hookSpecificOutput: {
    hookEventName: "PostToolUse",
    updatedToolOutput: {
      stdout: (if $ro then $so else (($r.stdout // "") | tostring) end),
      stderr: (if $re then $se else (($r.stderr // "") | tostring) end),
      interrupted: (($r.interrupted // false) == true),
      isImage: (($r.isImage // false) == true)
    }}}' 2>/dev/null
