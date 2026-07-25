#!/usr/bin/env bash
# session-refresh: UserPromptSubmit hook that flags a session over its wake
# budget. On prompt-submit it reads this session's own transcript_path from
# the hook's stdin JSON and computes the budget directly from that one file —
# no agentprof dependency, no shelling out to a separate process, no
# --since-windowed re-parse of transcript history (2026-07-23 decoupling:
# agentprof stays the tool for general cost-attribution digging; this hook
# only needs the cheap, always-available guardrail — maintainer's own framing).
#
# ONE arm — context size. Past budget, it prints the directive telling the
# session to write a /handoff and end instead of carrying its fat context
# into another wake (.claude/rules/token-discipline.md, "Session refresh"):
#
#   context-size arm — this turn's live context size, read from the most
#   recent main-loop assistant usage entry in the transcript:
#     ctx = input_tokens + cache_read_input_tokens
#   This is exactly agentprof's own "ctx" definition — mirrored, not
#   reinvented, so the two tools stay conceptually consistent
#   (agentprof/internal/costsummary/costsummary.go: "p50/p90 are over
#   per-call context size (cache_read_tokens + input_tokens)"; the same two
#   transcript usage fields, agentprof/internal/claude/claude.go's
#   transcriptLine.Message.Usage struct). Unlike agentprof's p90-over-a-window,
#   this arm is a single live reading of the CURRENT turn — the guardrail
#   only needs "over budget right now", not a percentile.
#
#
# Silent no-op (empty stdout, exit 0) on any missing dependency or parse
# error — no jq, no transcript_path in the payload, an unreadable or
# malformed transcript, a transcript with no qualifying usage line yet. A
# missing/broken guardrail must never break a session's prompt.
#
# The budget is tunable via environment (the default is the 30-day-profile
# pin from token-discipline.md, not a hard limit):
#   REFRESH_CTX_BUDGET       context-size arm             (default 250000)
set -u

CTX_BUDGET="${REFRESH_CTX_BUDGET:-250000}"

# jq parses both the stdin payload and the transcript; without it, no-op.
command -v jq >/dev/null 2>&1 || exit 0

payload="$(cat)"
transcript="$(printf '%s' "$payload" | jq -r '.transcript_path // empty' 2>/dev/null)"
[ -n "$transcript" ] && [ -r "$transcript" ] || exit 0

# One jq pass over the transcript: emit tab-separated
# (input_tokens, cache_read_input_tokens) for every main-loop assistant line
# carrying a usage object, in file order. isSidechain lines are subagent
# activity, excluded to match agentprof's main-loop-only ctx definition. A
# malformed/truncated transcript makes jq exit non-zero; whatever complete
# lines it already emitted before the failure are still used (2>/dev/null
# discards only the stderr noise).
qualifying="$(jq -r '
  select(.type == "assistant" and ((.isSidechain // false) == false)
         and .message.usage != null) |
  [(.message.usage.input_tokens // 0),
   (.message.usage.cache_read_input_tokens // 0)] | @tsv
' "$transcript" 2>/dev/null)"
[ -n "$qualifying" ] || exit 0

# The CURRENT turn is the last complete qualifying line.
IFS=$'\t' read -r last_it last_cr <<<"$(printf '%s\n' "$qualifying" | tail -n 1)"
case "$last_it" in '' | *[!0-9]*) last_it=0 ;; esac
case "$last_cr" in '' | *[!0-9]*) last_cr=0 ;; esac

ctx=$((last_it + last_cr))

if [ "$ctx" -ge "$CTX_BUDGET" ]; then
  cat <<EOF
Over wake budget: this turn's context size is ${ctx} tokens, past the refresh budget (${CTX_BUDGET} tokens).
Write a handoff now with /handoff and end this session instead of continuing — refresh-over-carry. A fresh session resuming from the handoff avoids re-paying the accumulated context on every wake.
EOF
fi

exit 0
