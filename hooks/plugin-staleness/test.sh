#!/usr/bin/env bash
# Unit tests for staleness-check.sh — the plugin-staleness SessionStart hook.
# Builds throwaway project trees under mktemp -d and stubs the installed
# version via PLUGIN_STALENESS_INSTALLED_VERSION, so it never invokes the live
# `claude plugin list` nor touches the real installed plugin cache.
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$DIR/staleness-check.sh"

pass=0
fail=0

check() { # check <description> <condition-result 0/1>
  if [ "$2" -eq 0 ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $1"
  fi
}

# build a temp project root whose .claude-plugin/plugin.json pins $1 as source
mkroot() { # mkroot <source-version>
  local t
  t="$(mktemp -d)"
  mkdir -p "$t/.claude-plugin"
  cat > "$t/.claude-plugin/plugin.json" <<JSON
{ "name": "agentic", "version": "$1" }
JSON
  printf '%s' "$t"
}

# --- installed behind source: warns, names both versions, exit 0 ----------
root="$(mkroot 0.9.3)"
out="$(CLAUDE_PROJECT_DIR="$root" PLUGIN_STALENESS_INSTALLED_VERSION="0.9.1" \
  bash "$HOOK" </dev/null)"
rc=$?
check "behind: non-empty stdout" "$([ -n "$out" ] && echo 0 || echo 1)"
check "behind: names source version 0.9.3" \
  "$(printf '%s' "$out" | grep -qF "0.9.3" && echo 0 || echo 1)"
check "behind: names installed version 0.9.1" \
  "$(printf '%s' "$out" | grep -qF "0.9.1" && echo 0 || echo 1)"
check "behind: exit 0 (warn, never block)" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$root"

# --- matching versions: silent, exit 0 ------------------------------------
root="$(mkroot 0.9.3)"
out="$(CLAUDE_PROJECT_DIR="$root" PLUGIN_STALENESS_INSTALLED_VERSION="0.9.3" \
  bash "$HOOK" </dev/null)"
rc=$?
check "match: empty stdout" "$([ -z "$out" ] && echo 0 || echo 1)"
check "match: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$root"

# --- installed ahead of source: silent (never nags on a newer install) ----
root="$(mkroot 0.9.1)"
out="$(CLAUDE_PROJECT_DIR="$root" PLUGIN_STALENESS_INSTALLED_VERSION="0.9.3" \
  bash "$HOOK" </dev/null)"
rc=$?
check "ahead: empty stdout" "$([ -z "$out" ] && echo 0 || echo 1)"
check "ahead: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$root"

# --- installed version undeterminable: silent (can't compare, don't nag) --
root="$(mkroot 0.9.3)"
out="$(CLAUDE_PROJECT_DIR="$root" PLUGIN_STALENESS_INSTALLED_VERSION="" \
  PLUGIN_STALENESS_SKIP_CLI=1 bash "$HOOK" </dev/null)"
rc=$?
check "no-installed: empty stdout" "$([ -z "$out" ] && echo 0 || echo 1)"
check "no-installed: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$root"

# --- no plugin.json at root: silent (not a plugin checkout) ---------------
root="$(mktemp -d)"
out="$(CLAUDE_PROJECT_DIR="$root" PLUGIN_STALENESS_INSTALLED_VERSION="0.9.1" \
  bash "$HOOK" </dev/null)"
rc=$?
check "no-manifest: empty stdout" "$([ -z "$out" ] && echo 0 || echo 1)"
check "no-manifest: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$root"

echo "----"
echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ]
