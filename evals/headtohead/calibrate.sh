#!/usr/bin/env bash
# evals/headtohead/calibrate.sh — RED/GREEN calibration proof for every real fixture.
#
# Proves the instrument end to end in one run. For each "real" task in
# tasks.manifest (ledger, notes-api, sitegen) it exercises the task's hidden,
# out-of-mount assert.sh against two inputs:
#
#   RED   — the untouched snapshot (repo/) must FAIL its assert.sh
#           → prints "<task> RED OK"
#   GREEN — the committed reference solution (reference/) must PASS its assert.sh
#           → prints "<task> GREEN OK"
#
# A grader that both fails the broken starting point and passes the intended
# fix is a real instrument; one that can't do both grades nothing. This script
# is that calibration check. It exits 0 only when all six conditions hold, and
# non-zero — naming the failing <task>/phase — otherwise.
#
# It edits no fixture and no reference solution: every check runs against a
# fresh temp copy, mirroring run.sh's copy-into-worktree isolation, so an
# assert.sh that writes __pycache__/out/ artifacts never dirties the tree.
#
# Written for bash 3.2 (macOS system bash) — no associative arrays.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$HERE/tasks.manifest"
REPO_ROOT="$(git -C "$HERE" rev-parse --show-toplevel 2>/dev/null || echo "$HERE/../..")"

TMPROOT="$(mktemp -d)"
trap 'rm -rf "$TMPROOT"' EXIT

FAIL=0

# run_check TASK PHASE SRC ASSERT
#   PHASE is "red" or "green". Copies SRC into a fresh working dir, runs ASSERT
#   against that copy, and checks its exit status against the phase's
#   expectation (red → must be non-zero; green → must be zero). On the expected
#   outcome it prints "<task> RED OK" / "<task> GREEN OK"; otherwise it records
#   a failure and names the task/phase.
run_check() {
  local task="$1" phase="$2" src="$3" assert="$4"
  local work="$TMPROOT/${task}_${phase}"

  if [ ! -d "$src" ]; then
    echo "$task ${phase} FAIL — missing input directory: $src" >&2
    FAIL=1
    return
  fi
  if [ ! -f "$assert" ]; then
    echo "$task ${phase} FAIL — missing assert.sh: $assert" >&2
    FAIL=1
    return
  fi

  rm -rf "$work"
  cp -R "$src" "$work"

  local status=0
  bash "$assert" "$work" >/dev/null 2>&1 || status=$?

  case "$phase" in
    red)
      if [ "$status" -ne 0 ]; then
        echo "$task RED OK"
      else
        echo "$task RED FAIL — assert.sh unexpectedly passed against the untouched snapshot" >&2
        FAIL=1
      fi
      ;;
    green)
      if [ "$status" -eq 0 ]; then
        echo "$task GREEN OK"
      else
        echo "$task GREEN FAIL — assert.sh did not pass against the reference solution (exit $status)" >&2
        FAIL=1
      fi
      ;;
  esac
}

# Walk the manifest's "real" rows in file order, RED then GREEN per task, so the
# path layout stays sourced from task 01's single source of truth.
saw_real=0
while IFS='|' read -r name kind snapshot assert reference brief; do
  case "$name" in ''|'#'*) continue ;; esac
  [ "$kind" = "real" ] || continue
  saw_real=1
  run_check "$name" red   "$REPO_ROOT/$snapshot"  "$REPO_ROOT/$assert"
  run_check "$name" green "$REPO_ROOT/$reference" "$REPO_ROOT/$assert"
done < "$MANIFEST"

if [ "$saw_real" -eq 0 ]; then
  echo "calibrate: no real tasks found in $MANIFEST" >&2
  exit 1
fi

if [ "$FAIL" -eq 0 ]; then
  echo "calibrate: all six RED/GREEN conditions hold"
  exit 0
fi
echo "calibrate: one or more RED/GREEN conditions failed" >&2
exit 1
