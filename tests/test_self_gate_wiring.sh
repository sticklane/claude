#!/usr/bin/env bash
# This toolkit dogfoods the two-layer gate it teaches consuming repos: the
# vetted templates/stop-gate.sh is installed into .claude/hooks/ and wired
# into .claude/settings.json's Stop hooks, alongside (never replacing) the
# plugin-autorefresh and bd-compliance entries already there.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SETTINGS="$TOOLKIT_DIR/.claude/settings.json"
INSTALLED="$TOOLKIT_DIR/.claude/hooks/stop-gate.sh"
TEMPLATE="$TOOLKIT_DIR/templates/stop-gate.sh"

pass=0
fail=0

assert() { # assert <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc" >&2
  fi
}

stop_entry_matching() { # stop_entry_matching <command substring>
  jq -e --arg needle "$1" \
    '[.hooks.Stop[]?.hooks[]? | select(.command | contains($needle))] | length > 0' \
    "$SETTINGS"
}

assert "installed stop-gate.sh is executable" test -x "$INSTALLED"
assert "installed stop-gate.sh is byte-identical to the vetted template" \
  diff -q "$INSTALLED" "$TEMPLATE"
assert "a Stop hook invokes stop-gate.sh" stop_entry_matching "stop-gate.sh"
assert "the plugin-autorefresh Stop hook survives" \
  stop_entry_matching "plugin-autorefresh"
assert "the bd-compliance Stop hook survives" \
  stop_entry_matching "bd-compliance.sh"

echo "pass: $pass, fail: $fail"
[ "$fail" -eq 0 ]
