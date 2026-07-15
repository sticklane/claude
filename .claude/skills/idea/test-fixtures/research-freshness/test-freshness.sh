#!/usr/bin/env bash
# Fixture-driven tests for check-freshness.sh.
#
# Fixed reference date TODAY=2026-06-01; every fixture stamp is a deliberate
# offset from it (not an arbitrary literal):
#   fresh / file-level-stamp: TODAY-17d  (2026-05-15) -> within 90d -> fresh
#   stale:                    TODAY-151d (2026-01-01) -> older      -> stale
#   no-stamp:                 no stamp anywhere                      -> absent
set -u
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
checker="$here/check-freshness.sh"
today="2026-06-01"

pass=0
fail=0
check() {
  local name="$1" expected="$2" got
  got="$(bash "$checker" "$here/$name" --today "$today")"
  if [ "$got" = "$expected" ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $name expected '$expected' got '$got'" >&2
  fi
}

check fresh fresh
check stale stale
check no-stamp absent
check file-level-stamp fresh

echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ] || exit 1
