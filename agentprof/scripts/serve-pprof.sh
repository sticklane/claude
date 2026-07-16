#!/usr/bin/env bash
# Serves the pprof web UI over the profile written by refresh-profile.sh.
# Runs under launchd with KeepAlive; refresh-profile.sh kickstarts the job
# after each profile rebuild (pprof loads the profile once at startup and
# never re-reads it — a file replacement alone does NOT refresh the UI).
set -euo pipefail

PROFILE="${1:-$HOME/.local/state/agentprof/claude-30d.pb.gz}"

if [ ! -f "$PROFILE" ]; then
  echo "serve-pprof: profile not found at $PROFILE (run refresh-profile.sh first)" >&2
  exit 1
fi

exec go tool pprof -no_browser -http=127.0.0.1:8901 "$PROFILE"
