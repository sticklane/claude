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

# A file inside a skill directory is never a surface identity of its own, but
# the skill that owns the directory is classified, so the query resolves to it.
for path in \
  .claude/skills/drain/reference.md
do
  run_preflight "$path"
  assert_status 0 "$path should pass once resolved to its owning skill"
  assert_reports "skill:drain" "$path should name skill:drain as its owner"
  refute_reports "Unclassified surface path" \
    "$path must not report the unclassified refusal"
  assert_reports "preflight: PASS" "$path should report PASS"
done

for path in \
  .claude/skills/workboard/workboard.py \
  .claude/skills/workboard/reference.md \
  .claude/skills/workboard/test_workboard.py
do
  run_preflight "$path"
  assert_status 0 "$path should pass once resolved to its owning skill"
  assert_reports "skill:workboard" "$path should name skill:workboard as its owner"
  refute_reports "Unclassified surface path" \
    "$path must not report the unclassified refusal"
  assert_reports "preflight: PASS" "$path should report PASS"
done

# A module under agentic/ that is not cli.py resolves to the cli-command rows
# the agentic/ surface owns.
for path in \
  agentic/ready.py \
  agentic/audit.py
do
  run_preflight "$path"
  assert_status 0 "$path should pass once resolved to its owning cli-command rows"
  assert_reports "cli-command:ready" "$path should name a cli-command row as owner"
  assert_reports "cli-command:register-spec" \
    "$path should name every cli-command row its surface owns"
  refute_reports "Unclassified surface path" \
    "$path must not report the unclassified refusal"
  assert_reports "preflight: PASS" "$path should report PASS"
done

# Ownership resolution must not turn the checker into a no-op: a path inside a
# scanned namespace with no owning classified surface still refuses. Both
# fixtures are constructed names, not real files a later commit may classify.
for path in \
  .claude/rules/no-such-ownership-fixture.md \
  tests/test_no_such_ownership_fixture.sh
do
  run_preflight "$path"
  assert_status 1 "$path has no owning surface and must still refuse"
  assert_reports "Unclassified surface path" \
    "$path should keep the unclassified verdict"
done

# A path owned by a retain surface refuses, which is the protection ownership
# resolution exists to restore.
run_preflight hooks/bd-export-guard/README.md
assert_status 1 "a file owned by a retain surface must refuse"
assert_reports "hook:bd-export-guard" \
  "the retain refusal should name the owning surface"
assert_reports "retain" "the refusal should cite the retain disposition"

# agentic-8z7p's behavior is unchanged for paths that own nothing and are owned
# by nothing.
run_preflight .claude/rules/token-discipline.md
assert_status 0 "a classified surface should still pass"
assert_reports "preflight: PASS" "a classified surface should report PASS"

run_preflight scripts/check.sh
assert_status 0 "scripts/check.sh should still pass"
assert_reports "out-of-inventory-namespace" \
  "scripts/check.sh should still report the out-of-namespace verdict"
refute_reports "owned by" "scripts/check.sh should not resolve to any owner"

# Every path agentic-lgio's criterion 3 touches passes in one invocation.
run_preflight \
  .claude/skills/drain/reference.md \
  agentic/ready.py \
  agentic/audit.py \
  bin/janitor \
  .claude/skills/workboard/workboard.py \
  .claude/skills/workboard/reference.md \
  .claude/skills/workboard/test_workboard.py \
  specs/QUEUE.md
assert_status 0 "all eight criterion-3 paths should pass in one invocation"
assert_reports "preflight: PASS" "the combined invocation should report PASS"

echo "test_breakdown_preflight_ownership.sh: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
