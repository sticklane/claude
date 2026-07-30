#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$ROOT/.claude/skills/breakdown/preflight-acceptance-inventory.py"
BASELINE="specs/toolkit-core-simplification/BASELINE.json"

pass=0
fail=0

check_ok() { # check_ok <description> <command...>
  local desc="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc" >&2
  fi
}

check_fail() { # check_fail <description> <command...>
  local desc="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    fail=$((fail + 1))
    echo "FAIL: $desc" >&2
  else
    pass=$((pass + 1))
  fi
}

check_ok "repair/discrete path passes pre-flight" \
  python3 "$SCRIPT" --baseline "$BASELINE" --path ".claude/skills/drain/SKILL.md"

check_fail "retain-class path is refused" \
  python3 "$SCRIPT" --baseline "$BASELINE" --path "tests/test_agentic_bootstrap.sh"

check_fail "unclassified path is refused" \
  python3 "$SCRIPT" --baseline "$BASELINE" --path "tests/test_missing_surface_fixture.sh"

echo "test_breakdown_inventory_preflight.sh: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
