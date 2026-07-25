#!/usr/bin/env bash
# Behavior tests for tier-check.sh — the loop-tier PreToolUse warn hook.
# Drives the hook against synthetic transcript JSONL fixtures (fixtures/),
# asserting the advisory appears on exactly the frontier-tier loop-call path
# and nowhere else. Never touches real session data.
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$DIR/tier-check.sh"
FIX="$DIR/fixtures"

pass=0
fail=0

# stdin_for <tool-name> <transcript-path> — a synthetic PreToolUse payload.
stdin_for() {
  printf '{"session_id":"test-session","transcript_path":"%s","hook_event_name":"PreToolUse","tool_name":"%s","tool_input":{}}' "$2" "$1"
}

# run_hook <tool-name> <transcript-path> [env assignments...] — sets OUT, RC.
run_hook() {
  local tool="$1" transcript="$2"
  shift 2
  if [ "$#" -gt 0 ]; then
    OUT="$(stdin_for "$tool" "$transcript" | env "$@" bash "$HOOK")"
  else
    OUT="$(stdin_for "$tool" "$transcript" | bash "$HOOK")"
  fi
  RC=$?
}

check() { # check <description> <condition-result 0/1>
  if [ "$2" -eq 0 ]; then
    pass=$((pass + 1))
    printf 'ok   - %s\n' "$1"
  else
    fail=$((fail + 1))
    printf 'FAIL - %s\n' "$1"
  fi
}

# warns — OUT parses as JSON whose PreToolUse additionalContext names <model>
# and carries no permission decision (warn, never block).
warns() { # warns <model>
  printf '%s' "$OUT" | jq -e --arg m "$1" '
    .hookSpecificOutput.hookEventName == "PreToolUse"
    and (.hookSpecificOutput.additionalContext | type == "string" and contains($m))
    and (.hookSpecificOutput | has("permissionDecision") | not)
  ' >/dev/null 2>&1
}

# 1. Frontier-tier transcript + ScheduleWakeup → advisory naming the model.
run_hook ScheduleWakeup "$FIX/frontier.jsonl"
check "frontier-tier ScheduleWakeup warns, naming the model, without a permission decision" \
  "$([ "$RC" -eq 0 ] && warns claude-fable-5 && echo 0 || echo 1)"

# 2. Frontier-tier transcript + CronCreate → the same advisory.
run_hook CronCreate "$FIX/frontier.jsonl"
check "frontier-tier CronCreate warns" \
  "$([ "$RC" -eq 0 ] && warns claude-fable-5 && echo 0 || echo 1)"

# 3. Cheap-tier transcript + loop call → empty stdout, exit 0.
run_hook ScheduleWakeup "$FIX/cheap.jsonl"
check "cheap-tier loop call produces empty stdout" "$([ -z "$OUT" ] && echo 0 || echo 1)"
check "cheap-tier loop call exits 0" "$([ "$RC" -eq 0 ] && echo 0 || echo 1)"

# 4. Frontier-tier transcript + a non-loop tool → silent; only loop-shaped
#    calls are gated even if the settings matcher is broader than intended.
run_hook Bash "$FIX/frontier.jsonl"
check "non-loop tool call produces empty stdout even on a frontier transcript" \
  "$([ -z "$OUT" ] && [ "$RC" -eq 0 ] && echo 0 || echo 1)"

# 5. Frontier model appearing only on a sidechain (subagent) entry → silent;
#    the tier read is the MAIN loop's, and dispatching frontier subagents
#    from a cheap main loop is the compliant pattern.
run_hook ScheduleWakeup "$FIX/sidechain-frontier.jsonl"
check "sidechain-only frontier model produces empty stdout" \
  "$([ -z "$OUT" ] && [ "$RC" -eq 0 ] && echo 0 || echo 1)"

# 6. Malformed transcript (no readable model) → silent no-op.
run_hook ScheduleWakeup "$FIX/malformed.jsonl"
check "malformed transcript produces empty stdout" "$([ -z "$OUT" ] && echo 0 || echo 1)"
check "malformed transcript exits 0" "$([ "$RC" -eq 0 ] && echo 0 || echo 1)"

# 7. transcript_path absent from the payload → silent no-op.
OUT="$(printf '{"session_id":"t","hook_event_name":"PreToolUse","tool_name":"ScheduleWakeup","tool_input":{}}' | bash "$HOOK")"
RC=$?
check "missing transcript_path produces empty stdout" "$([ -z "$OUT" ] && echo 0 || echo 1)"
check "missing transcript_path exits 0" "$([ "$RC" -eq 0 ] && echo 0 || echo 1)"

# 8. transcript_path points at a nonexistent file → silent no-op.
run_hook ScheduleWakeup "/no/such/transcript-$$.jsonl"
check "unreadable transcript produces empty stdout" "$([ -z "$OUT" ] && echo 0 || echo 1)"
check "unreadable transcript exits 0" "$([ "$RC" -eq 0 ] && echo 0 || echo 1)"

# 9. jq absent from PATH → silent no-op. Absolute bash path so the restricted
#    PATH can't block resolving the interpreter itself.
OUT="$(stdin_for ScheduleWakeup "$FIX/frontier.jsonl" | PATH="/nonexistent" /bin/bash "$HOOK")"
RC=$?
check "missing jq produces empty stdout" "$([ -z "$OUT" ] && echo 0 || echo 1)"
check "missing jq exits 0" "$([ "$RC" -eq 0 ] && echo 0 || echo 1)"

# 10. The frontier pattern is tunable: pointing it at the cheap fixture's
#     model family makes that fixture warn.
run_hook ScheduleWakeup "$FIX/cheap.jsonl" LOOP_TIER_FRONTIER_PATTERN=haiku
check "custom frontier pattern warns on the matching model" \
  "$([ "$RC" -eq 0 ] && warns claude-haiku-4-5 && echo 0 || echo 1)"

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
