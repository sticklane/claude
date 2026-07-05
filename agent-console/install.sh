#!/usr/bin/env bash
# Install Agent Console: symlink the CLI, render + load the launchd service.
# Nothing user-specific is committed — the plist is generated here from the
# current environment. Idempotent; safe to re-run after a git pull.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABEL="com.agent-console"
PORT="${AGENT_CONSOLE_PORT:-8899}"
HOST="${AGENT_CONSOLE_HOST:-127.0.0.1}"
PY="$(command -v python3)"
BIN="$HOME/.local/bin/agent-console"
LOGDIR="$HOME/Library/Logs/agent-console"
PLIST_DST="$HOME/Library/LaunchAgents/$LABEL.plist"
PATH_ENV="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin"

mkdir -p "$HOME/.local/bin" "$HOME/Library/LaunchAgents" "$LOGDIR"

# CLI convenience: ~/.local/bin/agent-console -> repo script
ln -sf "$REPO/agent-console.py" "$BIN"
echo "linked $BIN -> $REPO/agent-console.py"

# Render the plist template with this machine's paths (no committed user data)
sed -e "s|__LABEL__|$LABEL|g" \
    -e "s|__PYTHON__|$PY|g" \
    -e "s|__SCRIPT__|$REPO/agent-console.py|g" \
    -e "s|__HOME__|$HOME|g" \
    -e "s|__PATH__|$PATH_ENV|g" \
    -e "s|__PORT__|$PORT|g" \
    -e "s|__HOST__|$HOST|g" \
    -e "s|__LOG__|$LOGDIR/launchd.log|g" \
    "$REPO/launchd/agent-console.plist.tmpl" > "$PLIST_DST"

launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load "$PLIST_DST"
echo "loaded $LABEL"

sleep 1
if curl -fsS "http://$HOST:$PORT/healthz" >/dev/null; then
  echo "serving http://$HOST:$PORT  (Skills: /  ·  Workboard: /workboard)"
else
  echo "warning: health check failed — see $LOGDIR/launchd.log" >&2
fi
