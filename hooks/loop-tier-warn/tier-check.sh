#!/usr/bin/env bash
# loop-tier-warn: PreToolUse hook that warns — never blocks — when a
# frontier-tier main loop is about to become a waiting loop.
#
# A ScheduleWakeup or CronCreate call turns the session into a poller that
# idles past the prompt-cache TTL; .claude/rules/token-discipline.md's
# "Session refresh" doctrine says that main loop must run cheap-tier ("A
# waiting main loop is a scheduler, not a thinker"). No hook input field
# carries the session's model, but the payload's transcript_path does: every
# main-loop assistant entry records the model that produced it. This hook
# reads the last such entry — the same transcript-read shape as
# hooks/session-refresh/refresh-check.sh — and, when that model matches the
# frontier pattern, injects an advisory via PreToolUse additionalContext.
# The call always proceeds; no permissionDecision is ever emitted.
#
# Known limitation (Claude Code hooks reference, "Common input fields",
# transcript_path row): the transcript "may lag the in-memory conversation",
# so the model read can be one turn stale — e.g. immediately after a /model
# switch. Accepted for a warn-only hook; the next loop call re-reads it.
#
# Silent no-op (empty stdout, exit 0) whenever the answer is unknowable or
# compliant: a non-loop tool, a cheap-tier model, no jq, no transcript_path,
# an unreadable or malformed transcript, no model entry yet, or an invalid
# pattern. Fail open — a broken guardrail must never break a tool call.
#
# The frontier match is tunable via environment (the default is the
# frontier-tier family pin from runtimes/claude-code.md, matched
# case-insensitively as an ERE against the model id):
#   LOOP_TIER_FRONTIER_PATTERN   (default "fable")
set -u

FRONTIER_PATTERN="${LOOP_TIER_FRONTIER_PATTERN:-fable}"

command -v jq >/dev/null 2>&1 || exit 0

payload="$(cat)"

tool="$(printf '%s' "$payload" | jq -r '.tool_name // empty' 2>/dev/null)"
case "$tool" in
  ScheduleWakeup | CronCreate) ;;
  *) exit 0 ;;
esac

transcript="$(printf '%s' "$payload" | jq -r '.transcript_path // empty' 2>/dev/null)"
[ -n "$transcript" ] && [ -r "$transcript" ] || exit 0

# Last main-loop assistant entry's model. isSidechain lines are subagent
# activity — a frontier subagent under a cheap main loop is the compliant
# pattern, so they are excluded. A malformed/truncated transcript makes jq
# exit non-zero; whatever complete lines it already emitted still count.
model="$(jq -r '
  select(.type == "assistant" and ((.isSidechain // false) == false)
         and (.message.model? | type == "string")) | .message.model
' "$transcript" 2>/dev/null | tail -n 1)"
[ -n "$model" ] || exit 0

printf '%s' "$model" | grep -qiE -- "$FRONTIER_PATTERN" 2>/dev/null || exit 0

jq -cn --arg model "$model" --arg tool "$tool" '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    additionalContext: "The main loop of this session is running \($model), a frontier-tier model, and this \($tool) call makes it a waiting loop. The Session refresh doctrine (.claude/rules/token-discipline.md) is that a waiting main loop is a scheduler, not a thinker: the poller runs cheap-tier (Haiku at low effort, or launchd), dispatching the judgment work of each wake to an awaited fresh subagent. This is advisory only — the call proceeds."
  }
}'

exit 0
