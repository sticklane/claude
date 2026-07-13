#!/usr/bin/env bash
# Install slack-relay: create its venv, render + load the launchd service.
# Nothing user-specific is committed — the plist is generated here from the
# current environment. Idempotent; safe to re-run after a git pull.
#
# Prerequisites this script does NOT do for you (see AGENTS.md):
#   - Create the Slack app + bot token, store it in Keychain:
#       security add-generic-password -s slack-relay -a bot-token -w <token>
#   - Copy slack_relay_config.example.yaml to slack_relay_config.yaml and fill it in.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABEL="com.agent-console.slack-relay"
INTERVAL="${SLACK_RELAY_INTERVAL_SECONDS:-120}"
LOGDIR="$HOME/Library/Logs/agent-console"
PLIST_DST="$HOME/Library/LaunchAgents/$LABEL.plist"
PATH_ENV="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin"

mkdir -p "$HOME/Library/LaunchAgents" "$LOGDIR"

if [ ! -f "$REPO/slack_relay_config.yaml" ]; then
  echo "error: $REPO/slack_relay_config.yaml is missing — copy" \
       "slack_relay_config.example.yaml and fill it in first." >&2
  exit 1
fi

if [ ! -d "$REPO/.venv" ]; then
  python3 -m venv "$REPO/.venv"
  echo "created $REPO/.venv"
fi
"$REPO/.venv/bin/pip" install -q -r "$REPO/requirements.txt"

# Render the plist template with this machine's paths (no committed user data)
sed -e "s|__LABEL__|$LABEL|g" \
    -e "s|__PYTHON__|$REPO/.venv/bin/python|g" \
    -e "s|__SCRIPT__|$REPO/slack_relay.py|g" \
    -e "s|__CONFIG__|$REPO/slack_relay_config.yaml|g" \
    -e "s|__REPO__|$REPO|g" \
    -e "s|__HOME__|$HOME|g" \
    -e "s|__PATH__|$PATH_ENV|g" \
    -e "s|__INTERVAL__|$INTERVAL|g" \
    -e "s|__LOG__|$LOGDIR/slack-relay.log|g" \
    "$REPO/launchd/slack-relay.plist.tmpl" > "$PLIST_DST"

launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load "$PLIST_DST"
echo "loaded $LABEL (polling every ${INTERVAL}s, log: $LOGDIR/slack-relay.log)"
