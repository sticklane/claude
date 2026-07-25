#!/usr/bin/env bash
# Suite for the tool-output-spill PostToolUse hook. Run directly or via
# tests/test_tool_output_spill_hook.sh (scripts/check.sh's glob).
#
# The load-bearing assertions are shape assertions: per the hooks docs, a
# built-in tool's updatedToolOutput "must match the tool's output shape" or
# it is silently ignored — so a replacement that is merely a short string is
# a no-op, and a test that only checks for a short string passes while the
# hook does nothing. Every over-budget case here asserts the emitted
# replacement is the Bash output object: {stdout, stderr, interrupted,
# isImage} with the right types.
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

bash_payload() { # bash_payload <stdout> <stderr> <interrupted>
  jq -n --arg so "$1" --arg se "$2" --argjson intr "$3" \
    '{session_id:"spill-test",hook_event_name:"PostToolUse",tool_name:"Bash",
      tool_input:{command:"true"},
      tool_response:{stdout:$so,stderr:$se,interrupted:$intr,isImage:false}}'
}

big_text="$(head -c 60000 /dev/zero | tr '\0' 'x')"

if ! command -v jq >/dev/null 2>&1; then
  printf 'skip - suite needs jq to build fixtures\n'
  exit 0
fi

# 1. Under budget: the hook must stay completely silent (cache economics —
#    .claude/rules/token-discipline.md).
out="$(bash_payload "a short result" "" false | bash "$HOOK")"
rc=$?
check "small Bash result produces empty stdout" "${#out}" "0"
check "small Bash result exits 0" "$rc" "0"

# 2. Over budget: the replacement must be the Bash output object, not a bare
#    string — a bare string is silently ignored and the hook is a no-op.
out="$(bash_payload "$big_text" "warning: partial" true | bash "$HOOK")"
event="$(printf '%s' "$out" | jq -r '.hookSpecificOutput.hookEventName // empty' 2>/dev/null)"
check "large Bash stdout emits a PostToolUse hookSpecificOutput" "$event" "PostToolUse"

shape="$(printf '%s' "$out" | jq -r '.hookSpecificOutput.updatedToolOutput
  | [type, (.stdout|type), (.stderr|type), (.interrupted|type), (.isImage|type),
     (keys | sort | join(","))] | join("|")' 2>/dev/null)"
check "replacement matches the Bash output schema (object; typed fields; exact keys)" \
  "$shape" "object|string|string|boolean|boolean|interrupted,isImage,stderr,stdout"

check "replacement preserves interrupted from the original response" \
  "$(printf '%s' "$out" | jq -r '.hookSpecificOutput.updatedToolOutput.interrupted')" "true"
check "replacement preserves the original stderr verbatim" \
  "$(printf '%s' "$out" | jq -r '.hookSpecificOutput.updatedToolOutput.stderr')" "warning: partial"

new_stdout="$(printf '%s' "$out" | jq -r '.hookSpecificOutput.updatedToolOutput.stdout')"
check "replacement stdout is smaller than the original stdout" \
  "$([ "${#new_stdout}" -lt "${#big_text}" ] && echo yes || echo no)" "yes"

# 3. The full original stdout is preserved on disk at the path named inline.
spill="$(printf '%s\n' "$new_stdout" | sed -n 's/^Full result: //p' | head -n 1)"
check "replacement stdout names a spill file that exists" \
  "$([ -n "$spill" ] && [ -f "$spill" ] && echo yes || echo no)" "yes"
check "spill file holds the whole original stdout" \
  "$(wc -c <"$spill" | tr -d ' ')" "${#big_text}"

# 4. An oversized stderr spills the same way, leaving stdout intact.
out="$(bash_payload "ok" "$big_text" false | bash "$HOOK")"
check "large Bash stderr keeps stdout verbatim" \
  "$(printf '%s' "$out" | jq -r '.hookSpecificOutput.updatedToolOutput.stdout')" "ok"
err_repl="$(printf '%s' "$out" | jq -r '.hookSpecificOutput.updatedToolOutput.stderr')"
check "large Bash stderr is replaced by a smaller pointer" \
  "$([ -n "$err_repl" ] && [ "${#err_repl}" -lt "${#big_text}" ] && echo yes || echo no)" "yes"

# 5. Tools whose output schema the docs do not establish are excluded: a
#    guessed replacement would be silently ignored, so the hook says nothing.
out="$(jq -n --arg c "$big_text" \
  '{session_id:"spill-test",hook_event_name:"PostToolUse",tool_name:"Read",
    tool_input:{},tool_response:{file:{content:$c}}}' | bash "$HOOK")"
rc=$?
check "oversized non-Bash (Read) response stays silent" "${#out}" "0"
check "oversized non-Bash (Read) response exits 0" "$rc" "0"

# 6. The threshold is tunable, so a small result can be forced over budget.
out="$(bash_payload "a short result" "" false | TOOL_OUTPUT_SPILL_BUDGET=5 bash "$HOOK")"
check "a lowered budget makes a small result spill" \
  "$(printf '%s' "$out" | jq -r '.hookSpecificOutput.hookEventName // empty' 2>/dev/null)" "PostToolUse"

# 7. Degraded inputs never break the turn: no tool_response, a string
#    tool_response (not Bash's object shape), malformed JSON.
out="$(printf '{"session_id":"x","hook_event_name":"PostToolUse","tool_name":"Bash"}' | bash "$HOOK")"
check "payload without tool_response produces empty stdout" "${#out}" "0"

out="$(jq -n --arg r "$big_text" \
  '{session_id:"x",hook_event_name:"PostToolUse",tool_name:"Bash",tool_input:{},tool_response:$r}' |
  bash "$HOOK")"
check "string tool_response (not the Bash object shape) produces empty stdout" "${#out}" "0"

out="$(printf 'not json at all' | bash "$HOOK")"
rc=$?
check "malformed payload produces empty stdout" "${#out}" "0"
check "malformed payload exits 0" "$rc" "0"

# 8. Missing jq degrades to a silent no-op rather than an error.
stub="$work/stub-bin"
mkdir -p "$stub"
bash_bin="$(command -v bash)"
out="$(bash_payload "$big_text" "" false | PATH="$stub" "$bash_bin" "$HOOK")"
rc=$?
check "missing jq produces empty stdout" "${#out}" "0"
check "missing jq exits 0" "$rc" "0"

printf '\n%d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
