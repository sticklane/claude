#!/usr/bin/env bash
# A drain worker's declared external write boundary is enforced by the OS,
# not by prompt compliance.
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DISPATCHER="$ROOT/.claude/skills/drain/dispatch-worker.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
check() {
  local description="$1"
  shift
  if "$@"; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    printf 'FAIL: %s\n' "$description" >&2
  fi
}

denied="$TMP/external repo"
allowed="$TMP/worker tree"
mkdir -p "$denied" "$allowed"

check "dispatcher exists and is executable" test -x "$DISPATCHER"

"$DISPATCHER" --deny-write "$denied" -- \
  sh -c 'printf violated > "$1"' sh "$denied/marker" \
  >/dev/null 2>&1
denied_rc=$?
check "barred write exits nonzero" test "$denied_rc" -ne 0
check "barred write creates no file" test ! -e "$denied/marker"

"$DISPATCHER" --deny-write "$denied" -- \
  sh -c 'printf allowed > "$1"' sh "$allowed/marker" \
  >/dev/null 2>&1
allowed_rc=$?
check "write outside barred path succeeds" test "$allowed_rc" -eq 0
check "allowed write creates its file" test -f "$allowed/marker"

AGENTIC_SANDBOX_EXEC="$TMP/missing-sandbox" \
AGENTIC_BWRAP="$TMP/missing-bwrap" \
  "$DISPATCHER" --deny-write "$denied" -- \
    sh -c 'printf launched > "$1"' sh "$allowed/backend-fallthrough" \
    >/dev/null 2>&1
backend_rc=$?
check "missing sandbox backend exits nonzero" test "$backend_rc" -ne 0
check "missing backend never launches worker command" \
  test ! -e "$allowed/backend-fallthrough"

"$DISPATCHER" -- \
  sh -c 'printf launched > "$1"' sh "$allowed/no-deny-fallthrough" \
  >/dev/null 2>&1
no_deny_rc=$?
check "zero denied paths exits nonzero" test "$no_deny_rc" -ne 0
check "zero denied paths cannot fall through to direct execution" \
  test ! -e "$allowed/no-deny-fallthrough"

check "dispatch contract names the mechanical dispatcher" \
  grep -q 'dispatch-worker.sh' "$ROOT/.claude/skills/drain/reference.md"
check "dispatch contract forbids native spawn for boundary-sensitive work" \
  grep -q 'MUST NOT use.*native.*spawn' \
    "$ROOT/.claude/skills/drain/reference.md"

printf '%s passed, %s failed\n' "$pass" "$fail"
test "$fail" -eq 0
