#!/usr/bin/env bash
# Remove the launchd service and CLI symlink. Leaves the repo and logs intact.
set -euo pipefail

LABEL="com.agent-console"
PLIST_DST="$HOME/Library/LaunchAgents/$LABEL.plist"

launchctl unload "$PLIST_DST" 2>/dev/null || true
rm -f "$PLIST_DST" "$HOME/.local/bin/agent-console"
echo "unloaded $LABEL and removed symlinks (logs kept at ~/Library/Logs/agent-console)"
