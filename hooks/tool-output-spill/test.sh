#!/usr/bin/env bash
# Suite for the tool-output-spill PostToolUse hook. Run directly or via
# tests/test_tool_output_spill_hook.sh (scripts/check.sh's glob).
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$ROOT/spill-check.sh"

passed=0
failed=0

check() {
  if [ "$2" = "$3" ]; then
    printf 'ok   - %s\n' "$1"
    passed=$((passed + 1))
  else
    printf 'FAIL - %s\n     expected: %s\n     actual:   %s\n' "$1" "$3" "$2"
    failed=$((failed + 1))
  fi
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
export TMPDIR="$work"

payload() { # payload <tool_name> <result-text>
  jq -n --arg t "$1" --arg r "$2" \
    '{session_id:"spill-test",hook_event_name:"PostToolUse",tool_name:$t,tool_input:{},tool_response:$r}'
}

big_text="$(head -c 60000 /dev/zero | tr '\0' 'x')"

if ! command -v jq >/dev/null 2>&1; then
  printf 'skip - suite needs jq to build fixtures\n'
  exit 0
fi

# 1. Under budget: the hook must stay completely silent (cache economics —
#    .claude/rules/token-discipline.md).
out="$(payload Bash "a short result" | bash "$HOOK")"
rc=$?
check "small tool result produces empty stdout" "${#out}" "0"
check "small tool result exits 0" "$rc" "0"

# 2. Over budget: the result is replaced via updatedToolOutput.
out="$(payload Bash "$big_text" | bash "$HOOK")"
event="$(printf '%s' "$out" | jq -r '.hookSpecificOutput.hookEventName // empty' 2>/dev/null)"
check "large tool result emits a PostToolUse hookSpecificOutput" "$event" "PostToolUse"

replacement="$(printf '%s' "$out" | jq -r '.hookSpecificOutput.updatedToolOutput // empty' 2>/dev/null)"
check "large tool result carries a non-empty replacement" \
  "$([ -n "$replacement" ] && echo yes || echo no)" "yes"

check "replacement is smaller than the original result" \
  "$([ "${#replacement}" -lt "${#big_text}" ] && echo yes || echo no)" "yes"

# 3. The full result is preserved on disk at the path the replacement names.
spill="$(printf '%s\n' "$replacement" | sed -n 's/^Full result: //p' | head -n 1)"
check "replacement names a spill file that exists" \
  "$([ -n "$spill" ] && [ -f "$spill" ] && echo yes || echo no)" "yes"
check "spill file holds the whole original result" \
  "$(wc -c <"$spill" | tr -d ' ')" "${#big_text}"

# 4. The threshold is tunable, so a small result can be forced over budget.
out="$(TOOL_OUTPUT_SPILL_BUDGET=5 payload Bash "a short result" | TOOL_OUTPUT_SPILL_BUDGET=5 bash "$HOOK")"
check "a lowered budget makes a small result spill" \
  "$(printf '%s' "$out" | jq -r '.hookSpecificOutput.hookEventName // empty' 2>/dev/null)" "PostToolUse"

# 5. Degraded inputs never break the turn: no tool_response, malformed JSON.
out="$(printf '{"session_id":"x","hook_event_name":"PostToolUse","tool_name":"Bash"}' | bash "$HOOK")"
check "payload without tool_response produces empty stdout" "${#out}" "0"

out="$(printf 'not json at all' | bash "$HOOK")"
rc=$?
check "malformed payload produces empty stdout" "${#out}" "0"
check "malformed payload exits 0" "$rc" "0"

# 6. Missing jq degrades to a silent no-op rather than an error.
stub="$work/stub-bin"
mkdir -p "$stub"
bash_bin="$(command -v bash)"
out="$(payload Bash "$big_text" | PATH="$stub" "$bash_bin" "$HOOK")"
rc=$?
check "missing jq produces empty stdout" "${#out}" "0"
check "missing jq exits 0" "$rc" "0"

printf '\n%d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
