#!/usr/bin/env bash
# Unit tests for autorefresh.sh — the plugin-autorefresh Stop hook.
# Builds throwaway trees under mktemp -d and stubs the remote/installed
# versions and the refresh command via PLUGIN_AUTOREFRESH_* env vars, so it
# never invokes the live `claude` CLI, never touches the real plugin cache,
# and never runs the real bin/refresh-plugins.
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$DIR/autorefresh.sh"

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

# mkenv <tmpdir>: writes a refresh-command stub into <tmpdir> that records
# each invocation by touching <tmpdir>/refresh-ran; echoes the stub's path.
mkenv() {
  local t="$1"
  cat > "$t/refresh-stub.sh" <<STUB
#!/bin/sh
touch "$t/refresh-ran"
STUB
  chmod +x "$t/refresh-stub.sh"
  printf '%s' "$t/refresh-stub.sh"
}

# --- installed behind remote: runs refresh, names both versions, exit 0 ---
t="$(mktemp -d)"
stub="$(mkenv "$t")"
out="$(CLAUDE_PROJECT_DIR="$t" \
  PLUGIN_AUTOREFRESH_REMOTE_VERSION="0.9.5" \
  PLUGIN_AUTOREFRESH_INSTALLED_VERSION="0.9.4" \
  PLUGIN_AUTOREFRESH_CMD="$stub" \
  PLUGIN_AUTOREFRESH_LOCK="$t/lock" \
  bash "$HOOK" </dev/null)"
rc=$?
check "behind: refresh command ran" "$([ -f "$t/refresh-ran" ] && echo 0 || echo 1)"
check "behind: names remote version 0.9.5" \
  "$(printf '%s' "$out" | grep -qF "0.9.5" && echo 0 || echo 1)"
check "behind: names installed version 0.9.4" \
  "$(printf '%s' "$out" | grep -qF "0.9.4" && echo 0 || echo 1)"
check "behind: exit 0 (never block Stop)" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
check "behind: lock released after run" "$([ ! -d "$t/lock" ] && echo 0 || echo 1)"
rm -rf "$t"

# --- matching versions: silent, refresh not run ----------------------------
t="$(mktemp -d)"
stub="$(mkenv "$t")"
out="$(CLAUDE_PROJECT_DIR="$t" \
  PLUGIN_AUTOREFRESH_REMOTE_VERSION="0.9.5" \
  PLUGIN_AUTOREFRESH_INSTALLED_VERSION="0.9.5" \
  PLUGIN_AUTOREFRESH_CMD="$stub" \
  PLUGIN_AUTOREFRESH_LOCK="$t/lock" \
  bash "$HOOK" </dev/null)"
rc=$?
check "match: refresh not run" "$([ ! -f "$t/refresh-ran" ] && echo 0 || echo 1)"
check "match: empty stdout" "$([ -z "$out" ] && echo 0 || echo 1)"
check "match: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$t"

# --- installed ahead of remote: silent (never downgrade) -------------------
t="$(mktemp -d)"
stub="$(mkenv "$t")"
out="$(CLAUDE_PROJECT_DIR="$t" \
  PLUGIN_AUTOREFRESH_REMOTE_VERSION="0.9.4" \
  PLUGIN_AUTOREFRESH_INSTALLED_VERSION="0.9.5" \
  PLUGIN_AUTOREFRESH_CMD="$stub" \
  PLUGIN_AUTOREFRESH_LOCK="$t/lock" \
  bash "$HOOK" </dev/null)"
rc=$?
check "ahead: refresh not run" "$([ ! -f "$t/refresh-ran" ] && echo 0 || echo 1)"
check "ahead: empty stdout" "$([ -z "$out" ] && echo 0 || echo 1)"
check "ahead: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$t"

# --- remote version undeterminable (no git repo, no stub): silent ---------
t="$(mktemp -d)"
stub="$(mkenv "$t")"
out="$(CLAUDE_PROJECT_DIR="$t" \
  PLUGIN_AUTOREFRESH_INSTALLED_VERSION="0.9.4" \
  PLUGIN_AUTOREFRESH_CMD="$stub" \
  PLUGIN_AUTOREFRESH_LOCK="$t/lock" \
  bash "$HOOK" </dev/null)"
rc=$?
check "no-remote: refresh not run" "$([ ! -f "$t/refresh-ran" ] && echo 0 || echo 1)"
check "no-remote: empty stdout" "$([ -z "$out" ] && echo 0 || echo 1)"
check "no-remote: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$t"

# --- installed version undeterminable: silent (can't compare) --------------
t="$(mktemp -d)"
stub="$(mkenv "$t")"
out="$(CLAUDE_PROJECT_DIR="$t" \
  PLUGIN_AUTOREFRESH_REMOTE_VERSION="0.9.5" \
  PLUGIN_AUTOREFRESH_INSTALLED_VERSION="" \
  PLUGIN_AUTOREFRESH_SKIP_CLI=1 \
  PLUGIN_AUTOREFRESH_CMD="$stub" \
  PLUGIN_AUTOREFRESH_LOCK="$t/lock" \
  bash "$HOOK" </dev/null)"
rc=$?
check "no-installed: refresh not run" "$([ ! -f "$t/refresh-ran" ] && echo 0 || echo 1)"
check "no-installed: empty stdout" "$([ -z "$out" ] && echo 0 || echo 1)"
check "no-installed: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$t"

# --- git path: reads the manifest from origin's default branch ref --------
t="$(mktemp -d)"
stub="$(mkenv "$t")"
git -C "$t" init -q
mkdir -p "$t/.claude-plugin"
cat > "$t/.claude-plugin/plugin.json" <<'JSON'
{ "name": "agentic", "version": "0.9.7" }
JSON
git -C "$t" add .claude-plugin/plugin.json
git -C "$t" -c user.email=t@t -c user.name=t -c commit.gpgsign=false \
  commit -qm "bump"
git -C "$t" update-ref refs/remotes/origin/main HEAD
# working tree moves AHEAD of the pushed state: remote ref must still win
cat > "$t/.claude-plugin/plugin.json" <<'JSON'
{ "name": "agentic", "version": "0.9.8" }
JSON
out="$(CLAUDE_PROJECT_DIR="$t" \
  PLUGIN_AUTOREFRESH_INSTALLED_VERSION="0.9.6" \
  PLUGIN_AUTOREFRESH_CMD="$stub" \
  PLUGIN_AUTOREFRESH_LOCK="$t/lock" \
  bash "$HOOK" </dev/null)"
rc=$?
check "git: refresh ran against origin/main's version" \
  "$([ -f "$t/refresh-ran" ] && echo 0 || echo 1)"
check "git: names the pushed version 0.9.7, not the unpushed 0.9.8" \
  "$(printf '%s' "$out" | grep -qF "0.9.7" && ! printf '%s' "$out" | grep -qF "0.9.8" && echo 0 || echo 1)"
check "git: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$t"

# --- git path, bump committed but NOT pushed: silent (remote can't serve it)
t="$(mktemp -d)"
stub="$(mkenv "$t")"
git -C "$t" init -q
mkdir -p "$t/.claude-plugin"
cat > "$t/.claude-plugin/plugin.json" <<'JSON'
{ "name": "agentic", "version": "0.9.6" }
JSON
git -C "$t" add .claude-plugin/plugin.json
git -C "$t" -c user.email=t@t -c user.name=t -c commit.gpgsign=false \
  commit -qm "old"
git -C "$t" update-ref refs/remotes/origin/main HEAD
cat > "$t/.claude-plugin/plugin.json" <<'JSON'
{ "name": "agentic", "version": "0.9.7" }
JSON
git -C "$t" add .claude-plugin/plugin.json
git -C "$t" -c user.email=t@t -c user.name=t -c commit.gpgsign=false \
  commit -qm "bump, unpushed"
out="$(CLAUDE_PROJECT_DIR="$t" \
  PLUGIN_AUTOREFRESH_INSTALLED_VERSION="0.9.6" \
  PLUGIN_AUTOREFRESH_CMD="$stub" \
  PLUGIN_AUTOREFRESH_LOCK="$t/lock" \
  bash "$HOOK" </dev/null)"
rc=$?
check "unpushed: refresh not run" "$([ ! -f "$t/refresh-ran" ] && echo 0 || echo 1)"
check "unpushed: empty stdout" "$([ -z "$out" ] && echo 0 || echo 1)"
check "unpushed: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$t"

# --- refresh command fails: reports it, still exit 0 -----------------------
t="$(mktemp -d)"
cat > "$t/refresh-stub.sh" <<'STUB'
#!/bin/sh
exit 1
STUB
chmod +x "$t/refresh-stub.sh"
out="$(CLAUDE_PROJECT_DIR="$t" \
  PLUGIN_AUTOREFRESH_REMOTE_VERSION="0.9.5" \
  PLUGIN_AUTOREFRESH_INSTALLED_VERSION="0.9.4" \
  PLUGIN_AUTOREFRESH_CMD="$t/refresh-stub.sh" \
  PLUGIN_AUTOREFRESH_LOCK="$t/lock" \
  bash "$HOOK" </dev/null)"
rc=$?
check "refresh-fail: exit 0 (never block Stop)" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
check "refresh-fail: reports the failure" \
  "$(printf '%s' "$out" | grep -qi "fail" && echo 0 || echo 1)"
check "refresh-fail: lock released" "$([ ! -d "$t/lock" ] && echo 0 || echo 1)"
rm -rf "$t"

# --- fresh lock already held: skips (another refresh in flight) ------------
t="$(mktemp -d)"
stub="$(mkenv "$t")"
mkdir "$t/lock"
out="$(CLAUDE_PROJECT_DIR="$t" \
  PLUGIN_AUTOREFRESH_REMOTE_VERSION="0.9.5" \
  PLUGIN_AUTOREFRESH_INSTALLED_VERSION="0.9.4" \
  PLUGIN_AUTOREFRESH_CMD="$stub" \
  PLUGIN_AUTOREFRESH_LOCK="$t/lock" \
  bash "$HOOK" </dev/null)"
rc=$?
check "locked: refresh not run" "$([ ! -f "$t/refresh-ran" ] && echo 0 || echo 1)"
check "locked: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
check "locked: existing lock left in place" "$([ -d "$t/lock" ] && echo 0 || echo 1)"
rm -rf "$t"

# --- stale lock (>10 min old): taken over, refresh runs --------------------
t="$(mktemp -d)"
stub="$(mkenv "$t")"
mkdir "$t/lock"
touch -t 202001010000 "$t/lock"
out="$(CLAUDE_PROJECT_DIR="$t" \
  PLUGIN_AUTOREFRESH_REMOTE_VERSION="0.9.5" \
  PLUGIN_AUTOREFRESH_INSTALLED_VERSION="0.9.4" \
  PLUGIN_AUTOREFRESH_CMD="$stub" \
  PLUGIN_AUTOREFRESH_LOCK="$t/lock" \
  bash "$HOOK" </dev/null)"
rc=$?
check "stale-lock: refresh ran" "$([ -f "$t/refresh-ran" ] && echo 0 || echo 1)"
check "stale-lock: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$t"

echo "----"
echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ]
