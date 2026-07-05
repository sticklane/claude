#!/usr/bin/env bash
# Regenerates the rolling 30-day agentprof profile used by the pprof web UI
# (agentprof/scripts/serve-pprof.sh) and the workboard's refresh control.
#
# Locates (building if needed) the agentprof binary, then writes the profile
# to a temp file in the state dir and mv's it into place so readers never see
# a partial file. Restarting the pprof service that serves the profile is the
# CALLER's job (launchd KeepAlive / the workboard's refresh handler) — this
# script only regenerates the file.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTPROF_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

STATE_DIR="$HOME/.local/state/agentprof"
OUTPUT="$STATE_DIR/claude-30d.pb.gz"

mkdir -p "$STATE_DIR"

# Locate or build the agentprof binary: prefer one already on PATH, then a
# binary already built in the repo, then build it.
if command -v agentprof >/dev/null 2>&1; then
  AGENTPROF_BIN="$(command -v agentprof)"
elif [ -x "$AGENTPROF_DIR/agentprof" ]; then
  AGENTPROF_BIN="$AGENTPROF_DIR/agentprof"
else
  (cd "$AGENTPROF_DIR" && go build -o agentprof .)
  AGENTPROF_BIN="$AGENTPROF_DIR/agentprof"
fi

TMP_FILE="$(mktemp "$STATE_DIR/.claude-30d.XXXXXX.pb.gz")"
trap 'rm -f "$TMP_FILE"' EXIT

"$AGENTPROF_BIN" claude --days 30 -o "$TMP_FILE"
mv "$TMP_FILE" "$OUTPUT"
