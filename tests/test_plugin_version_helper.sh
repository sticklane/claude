#!/usr/bin/env bash
# Tests for bin/plugin-installed-version — the shared "what version of the
# agentic plugin is installed" read used by hooks/plugin-staleness,
# hooks/plugin-autorefresh, and bin/refresh-plugins. Stubs the `claude` CLI
# with a PATH shim emitting the real `claude plugin list --json` shape, so it
# never invokes the live CLI.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HELPER="$TOOLKIT_DIR/bin/plugin-installed-version"

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

# mkshim <tmpdir> <json>: installs a fake `claude` on <tmpdir>/bin that
# prints <json> for `plugin list --json`.
mkshim() {
  local t="$1" json="$2"
  mkdir -p "$t/bin"
  cat > "$t/bin/claude" <<SHIM
#!/bin/sh
cat <<'JSON'
$json
JSON
SHIM
  chmod +x "$t/bin/claude"
}

# --- plugin installed: prints its version, exit 0 ---------------------------
t="$(mktemp -d)"
mkshim "$t" '[{"id":"other@mkt","version":"1.0.0"},{"id":"agentic@agentic-toolkit","version":"0.9.15","scope":"user","enabled":true}]'
out="$(PATH="$t/bin:$PATH" bash "$HELPER")"
rc=$?
check "installed: prints version" "$([ "$out" = "0.9.15" ] && echo 0 || echo 1)"
check "installed: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$t"

# --- explicit plugin id argument --------------------------------------------
t="$(mktemp -d)"
mkshim "$t" '[{"id":"other@mkt","version":"1.2.3"}]'
out="$(PATH="$t/bin:$PATH" bash "$HELPER" other@mkt)"
rc=$?
check "by-id: prints version" "$([ "$out" = "1.2.3" ] && echo 0 || echo 1)"
check "by-id: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$t"

# --- plugin not installed: empty, exit 1 -------------------------------------
t="$(mktemp -d)"
mkshim "$t" '[{"id":"other@mkt","version":"1.0.0"}]'
out="$(PATH="$t/bin:$PATH" bash "$HELPER")"
rc=$?
check "absent: empty output" "$([ -z "$out" ] && echo 0 || echo 1)"
check "absent: exit 1" "$([ "$rc" -eq 1 ] && echo 0 || echo 1)"
rm -rf "$t"

# --- malformed JSON from the CLI: empty, exit 1 ------------------------------
t="$(mktemp -d)"
mkshim "$t" 'not json at all'
out="$(PATH="$t/bin:$PATH" bash "$HELPER" 2>/dev/null)"
rc=$?
check "malformed: empty output" "$([ -z "$out" ] && echo 0 || echo 1)"
check "malformed: exit 1" "$([ "$rc" -eq 1 ] && echo 0 || echo 1)"
rm -rf "$t"

# --- claude CLI not on PATH: empty, exit 1 -----------------------------------
t="$(mktemp -d)"
mkdir -p "$t/bin" # no claude shim inside
out="$(PATH="$t/bin:/usr/bin:/bin" bash "$HELPER" 2>/dev/null)"
rc=$?
check "no-cli: empty output" "$([ -z "$out" ] && echo 0 || echo 1)"
check "no-cli: exit 1" "$([ "$rc" -eq 1 ] && echo 0 || echo 1)"
rm -rf "$t"

echo "----"
echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ]
