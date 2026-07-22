#!/usr/bin/env bash
# preflight_fanout.sh — the pre-flight fan-out guard for /work (SPEC.md
# "The pre-flight fan-out guard", specs/beads-daily-skill/SPEC.md).
#
# Before /work authors or runs a native workflow script, this estimates the
# token floor of the proposed agent count (count x the measured per-agent
# floor) and refuses above a configured threshold unless explicitly
# overridden. No workflow is written until this passes.
#
#   Usage:  preflight_fanout.sh <agent-count> [--override]
#
# Env:
#   AGENTIC_FANOUT_THRESHOLD  agent-count threshold (default 20)
#   AGENTIC_AGENT_FLOOR       per-agent floor tokens (default 36000, the
#                             measured figure)
#
# Exit 0  = estimate at/under threshold, or above threshold with --override
# Exit 1  = above threshold, no --override given
# Exit 2  = usage error (missing/invalid agent count)
set -u

count="${1:-}"
override=0
for arg in "$@"; do
  case "$arg" in
    --override) override=1 ;;
  esac
done

if [ -z "$count" ] || ! printf '%s' "$count" | grep -Eq '^[0-9]+$'; then
  echo "preflight_fanout: usage: preflight_fanout.sh <agent-count> [--override]" >&2
  exit 2
fi

threshold="${AGENTIC_FANOUT_THRESHOLD:-20}"
floor="${AGENTIC_AGENT_FLOOR:-36000}"
estimate=$((count * floor))

if [ "$count" -gt "$threshold" ]; then
  if [ "$override" -eq 1 ]; then
    echo "preflight_fanout: estimate ${count} x ${floor} = ${estimate} tokens — above threshold ${threshold}, proceeding (explicit --override given)"
    exit 0
  fi
  echo "preflight_fanout: REFUSED — estimate ${count} x ${floor} = ${estimate} tokens, above threshold ${threshold} agents. Pass --override to proceed anyway." >&2
  exit 1
fi

echo "preflight_fanout: estimate ${count} x ${floor} = ${estimate} tokens — at/under threshold ${threshold}, proceeding"
exit 0
