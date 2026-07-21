#!/usr/bin/env bash
# Tests for bin/resolve-skill-path — the in-repo shortcut implementing the
# canonical two-step skill-path resolution recipe from
# .claude/skills/drain/reference.md's "Worker prompt" section. Mirrors
# tests/test_plugin_version_helper.sh's shim-based approach: stubs the
# `claude` CLI with a PATH shim emitting the real `claude plugin list --json`
# shape, and stages a fake repo root + fake $HOME plugin cache, so it never
# invokes the live CLI or depends on a real installed plugin.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$TOOLKIT_DIR/bin/resolve-skill-path"

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

# stage_repo <tmpdir>: copies the real resolve-skill-path into <tmpdir>/bin so
# the script computes <tmpdir> as its repo root (root = parent of bin/).
stage_repo() {
  local t="$1"
  mkdir -p "$t/bin"
  cp "$SCRIPT" "$t/bin/resolve-skill-path"
  chmod +x "$t/bin/resolve-skill-path"
}

# mkshim <tmpdir> <json>: installs a fake `claude` on <tmpdir>/bin that
# records it was called (touch shim_called) and prints <json> for
# `plugin list --json`.
mkshim() {
  local t="$1" json="$2"
  cat > "$t/bin/claude" <<SHIM
#!/bin/sh
touch "$t/shim_called"
cat <<'JSON'
$json
JSON
SHIM
  chmod +x "$t/bin/claude"
}

# --- in-repo path exists: returns it, exit 0, shim NOT called ---------------
t="$(mktemp -d)"
stage_repo "$t"
mkshim "$t" '[{"id":"agentic@agentic-toolkit","version":"9.9.9"}]'
mkdir -p "$t/.claude/skills/foo"
: > "$t/.claude/skills/foo/bar.md"
out="$(PATH="$t/bin:$PATH" "$t/bin/resolve-skill-path" .claude/skills/foo/bar.md)"
rc=$?
check "in-repo: prints resolved path" "$([ "$out" = "$t/.claude/skills/foo/bar.md" ] && echo 0 || echo 1)"
check "in-repo: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
check "in-repo: shim not called" "$([ ! -e "$t/shim_called" ] && echo 0 || echo 1)"
rm -rf "$t"

# --- in-repo absent, plugin-cache path exists: returns cache path, exit 0 ---
t="$(mktemp -d)"
stage_repo "$t"
mkshim "$t" '[{"id":"other@mkt","version":"1.0.0"},{"id":"agentic@agentic-toolkit","version":"9.9.9"}]'
home="$t/home"
cache="$home/.claude/plugins/cache/agentic-toolkit/agentic/9.9.9/.claude/skills/foo/bar.md"
mkdir -p "$(dirname "$cache")"
: > "$cache"
out="$(HOME="$home" PATH="$t/bin:$PATH" "$t/bin/resolve-skill-path" .claude/skills/foo/bar.md)"
rc=$?
check "plugin-cache: prints constructed cache path" "$([ "$out" = "$cache" ] && echo 0 || echo 1)"
check "plugin-cache: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$t"

# --- no matching plugin: exit 1 with non-empty stderr -----------------------
t="$(mktemp -d)"
stage_repo "$t"
mkshim "$t" '[{"id":"other@mkt","version":"1.0.0"}]'
home="$t/home"
mkdir -p "$home"
err="$(HOME="$home" PATH="$t/bin:$PATH" "$t/bin/resolve-skill-path" .claude/skills/foo/bar.md 2>&1 >/dev/null)"
rc=$?
check "no-plugin: exit 1" "$([ "$rc" -eq 1 ] && echo 0 || echo 1)"
check "no-plugin: non-empty stderr" "$([ -n "$err" ] && echo 0 || echo 1)"
rm -rf "$t"

# --- version resolves but constructed cache path is absent: exit 1 ----------
t="$(mktemp -d)"
stage_repo "$t"
mkshim "$t" '[{"id":"agentic@agentic-toolkit","version":"9.9.9"}]'
home="$t/home"
mkdir -p "$home" # no cache file staged under it
err="$(HOME="$home" PATH="$t/bin:$PATH" "$t/bin/resolve-skill-path" .claude/skills/foo/bar.md 2>&1 >/dev/null)"
rc=$?
check "cache-absent: exit 1" "$([ "$rc" -eq 1 ] && echo 0 || echo 1)"
check "cache-absent: non-empty stderr" "$([ -n "$err" ] && echo 0 || echo 1)"
rm -rf "$t"

echo "----"
echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ]
