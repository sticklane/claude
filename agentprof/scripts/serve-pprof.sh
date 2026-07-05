#!/usr/bin/env bash
# Serves the pprof web UI over the profile written by refresh-profile.sh.
# Intended to run under launchd with KeepAlive so it restarts automatically
# whenever refresh-profile.sh replaces the profile file out from under it.
set -euo pipefail

PROFILE="${1:-$HOME/.local/state/agentprof/claude-30d.pb.gz}"

if [ ! -f "$PROFILE" ]; then
  echo "serve-pprof: profile not found at $PROFILE (run refresh-profile.sh first)" >&2
  exit 1
fi

exec go tool pprof -no_browser -http=127.0.0.1:8901 "$PROFILE"
