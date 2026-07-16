#!/usr/bin/env bash
# Regenerates the rolling 30-day agentprof profile used by the pprof web UI
# (agentprof/scripts/serve-pprof.sh) and the workboard's refresh control, then
# maintains the rolling 7-day cost-summary cache used by the workboard's
# "Cost (7d)" panel (specs/workboard-weekly-cost-view/SPEC.md R4).
#
# Locates (building if needed) the agentprof binary, then writes each output
# to a temp file in the state dir and mv's it into place so readers never see
# a partial file. After replacing the 30d profile it kickstarts the pprof
# service — go tool pprof loads the profile once at startup and never
# re-reads it, so without a restart the web UI serves a stale snapshot
# indefinitely (observed 3 days stale, 2026-07-15).
set -euo pipefail

# Timestamped run markers so the launchd log attributes output to runs and a
# skipped/failed hour is visible from the log itself, not just file mtimes.
log() { printf '%s refresh-profile: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"; }
log "start"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTPROF_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

STATE_DIR="$HOME/.local/state/agentprof"
OUTPUT="$STATE_DIR/claude-30d.pb.gz"
WEEKLY_JSONL="$STATE_DIR/weekly-7d.jsonl"
WEEKLY_SUMMARY="$STATE_DIR/weekly-7d-summary.json"

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

# mktemp's X-substitution only fires on trailing X's (BSD mktemp does not
# randomize a template with a static suffix after the X's, e.g.
# ".XXXXXX.pb.gz" — it silently returns the literal, colliding name on a
# second run), so generate suffix-free then rename.
TMP_FILE="$(mktemp "$STATE_DIR/.claude-30d.XXXXXX")"
mv "$TMP_FILE" "$TMP_FILE.pb.gz"
TMP_FILE="$TMP_FILE.pb.gz"
TMP_WEEKLY="$(mktemp "$STATE_DIR/.weekly-7d.XXXXXX")"
mv "$TMP_WEEKLY" "$TMP_WEEKLY.jsonl"
TMP_WEEKLY="$TMP_WEEKLY.jsonl"
trap 'rm -f "$TMP_FILE" "$TMP_WEEKLY"' EXIT

"$AGENTPROF_BIN" claude --days 30 -o "$TMP_FILE"
mv "$TMP_FILE" "$OUTPUT"

# pprof serves whatever profile it loaded at startup; kick the serving job
# so the web UI picks up the rebuilt file. Never fail the refresh over it.
if launchctl kickstart -k "gui/$(id -u)/com.sjaconette.agentprof-pprof" 2>/dev/null; then
  log "30d profile replaced, pprof restarted"
else
  log "30d profile replaced, but pprof kickstart failed (job not loaded?) — web UI may be stale"
fi

# Weekly 7d rolling cache: --since the previous run's cache mtime (falling
# back to 7 days ago on first run / missing file), --merge reads the current
# cache while -o writes to a temp file so readers never see a partial write.
if [ -f "$WEEKLY_JSONL" ]; then
  SINCE="$(date -u -r "$WEEKLY_JSONL" '+%Y-%m-%dT%H:%M:%SZ')"
else
  SINCE="$(date -u -v-7d '+%Y-%m-%dT%H:%M:%SZ')"
fi

"$AGENTPROF_BIN" claude --since "$SINCE" --merge "$WEEKLY_JSONL" -o "$TMP_WEEKLY" --summary "$WEEKLY_SUMMARY"
mv "$TMP_WEEKLY" "$WEEKLY_JSONL"
log "done"
