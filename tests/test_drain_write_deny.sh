#!/usr/bin/env bash
# A drain worker's declared external write boundary is enforced by the OS,
# not by prompt compliance.
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GUARD="$ROOT/.claude/skills/drain/write-deny.sh"
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

"$GUARD" --deny-write "$denied" -- \
  sh -c 'printf violated > "$1"' sh "$denied/marker" \
  >/dev/null 2>&1
denied_rc=$?
check "barred write exits nonzero" test "$denied_rc" -ne 0
check "barred write creates no file" test ! -e "$denied/marker"

"$GUARD" --deny-write "$denied" -- \
  sh -c 'printf allowed > "$1"' sh "$allowed/marker" \
  >/dev/null 2>&1
allowed_rc=$?
check "write outside barred path succeeds" test "$allowed_rc" -eq 0
check "allowed write creates its file" test -f "$allowed/marker"

check "dispatch contract names the mechanical wrapper" \
  grep -q 'write-deny.sh' "$ROOT/.claude/skills/drain/reference.md"
check "dispatch contract routes boundary-sensitive workers through headless mode" \
  grep -q 'boundary-sensitive worker.*headless' \
    "$ROOT/.claude/skills/drain/reference.md"

printf '%s passed, %s failed\n' "$pass" "$fail"
test "$fail" -eq 0
