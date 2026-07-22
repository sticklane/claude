#!/usr/bin/env bash
# Regression test for /work's pre-flight fan-out guard
# (.claude/skills/work/preflight_fanout.sh), specs/beads-daily-skill/SPEC.md
# acceptance criterion: "fed a fixture plan of 30 agents against a 20-agent
# threshold, refuses without the override flag and passes with it."
set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$here/.." && pwd)"
guard="$repo_root/.claude/skills/work/preflight_fanout.sh"

pass=0
fail=0

check() { # check <description> <condition-result 0/1>
  if [ "$2" -eq 0 ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $1" >&2
  fi
}

# --- 5 agents, default threshold (20): passes ------------------------------
out="$(bash "$guard" 5 2>&1)"
rc=$?
check "5 agents: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
check "5 agents: prints estimate (5 x 36000)" "$(printf '%s' "$out" | grep -q '5 x 36000' && echo 0 || echo 1)"

# --- 30 agents vs threshold 20: refuses, names --override ------------------
out="$(AGENTIC_FANOUT_THRESHOLD=20 bash "$guard" 30 2>&1)"
rc=$?
check "30 vs threshold 20: exit 1" "$([ "$rc" -eq 1 ] && echo 0 || echo 1)"
check "30 vs threshold 20: message names --override" "$(printf '%s' "$out" | grep -q -- '--override' && echo 0 || echo 1)"
check "30 vs threshold 20: message prints estimate" "$(printf '%s' "$out" | grep -q '30 x 36000' && echo 0 || echo 1)"

# --- 30 agents with --override: passes -------------------------------------
out="$(AGENTIC_FANOUT_THRESHOLD=20 bash "$guard" 30 --override 2>&1)"
rc=$?
check "30 with --override: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
check "30 with --override: notes override was explicit" "$(printf '%s' "$out" | grep -qi 'override' && echo 0 || echo 1)"

# --- usage error: missing agent count --------------------------------------
bash "$guard" >/dev/null 2>&1
rc=$?
check "missing agent count: exit 2" "$([ "$rc" -eq 2 ] && echo 0 || echo 1)"

echo "pass: $pass fail: $fail"
if [ "$fail" -eq 0 ]; then
  echo "PREFLIGHT TEST OK"
  exit 0
fi
exit 1
