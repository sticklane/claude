#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$ROOT/.claude/skills/breakdown/preflight-acceptance-inventory.py"
BASELINE="specs/toolkit-core-simplification/BASELINE.json"

cd "$ROOT" || exit 1

pass=0
fail=0

record() { # record <ok|no> <description>
  if [ "$1" = ok ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $2" >&2
  fi
}

preflight_output=""
preflight_status=0
run_preflight() { # run_preflight <path> [path ...]
  local args=()
  local path
  for path in "$@"; do
    args+=(--path "$path")
  done
  preflight_output="$(python3 "$SCRIPT" --baseline "$BASELINE" "${args[@]}" 2>&1)"
  preflight_status=$?
}

assert_status() { # assert_status <expected> <description>
  if [ "$preflight_status" -eq "$1" ]; then
    record ok
  else
    record no "$2 (expected exit $1, got $preflight_status)"
  fi
}

assert_reports() { # assert_reports <substring> <description>
  case "$preflight_output" in
    *"$1"*) record ok ;;
    *) record no "$2" ;;
  esac
}

refute_reports() { # refute_reports <substring> <description>
  case "$preflight_output" in
    *"$1"*) record no "$2" ;;
    *) record ok ;;
  esac
}

# A path outside every namespace discover_surfaces scans is not a refusal:
# it reports the out-of-namespace note and still passes.
for path in \
  bin/review-gate \
  scripts/check.sh \
  docs/memory.md \
  specs/QUEUE.md \
  agentic/ready.py \
  .claude/skills/drain/reference.md
do
  run_preflight "$path"
  assert_status 0 "$path is out of namespace and must not refuse"
  assert_reports "out-of-inventory-namespace" \
    "$path should report the out-of-namespace verdict"
  refute_reports "Unclassified surface path" \
    "$path must not report the unclassified refusal"
  assert_reports "preflight: PASS" "$path should still report PASS"
done

# A path inside a scanned namespace that the inventory does not classify still
# refuses — including a namespace whose members are whole directories, where the
# queried surface does not exist yet.
for path in \
  .claude/rules/no-such-namespace-fixture.md \
  .claude/skills/no-such-skill-fixture/SKILL.md \
  hooks/no-such-hook-fixture/run.sh \
  tests/test_no_such_fixture.sh
do
  run_preflight "$path"
  assert_status 1 "$path is in a scanned namespace and must still refuse"
  assert_reports "Unclassified surface path" \
    "$path should keep the unclassified verdict"
done

run_preflight .claude/rules/token-discipline.md
assert_status 0 "classified surface should still pass"
assert_reports "preflight: PASS" "classified surface should report PASS"

# /breakdown passes every path a criterion touches in one invocation, so a
# classified path alongside an out-of-namespace one still passes.
run_preflight .claude/rules/token-discipline.md docs/memory.md
assert_status 0 "classified plus out-of-namespace should pass"
assert_reports "preflight: PASS" "mixed invocation should report PASS"

# An out-of-namespace path must not mask a real refusal in the same invocation.
run_preflight \
  .claude/rules/token-discipline.md \
  docs/memory.md \
  .claude/rules/no-such-namespace-fixture.md
assert_status 1 "an unclassified path must still refuse in a mixed invocation"
assert_reports "Unclassified surface path" \
  "mixed invocation should keep the unclassified verdict"

echo "test_breakdown_preflight_namespace.sh: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
