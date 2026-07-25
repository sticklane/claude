#!/usr/bin/env bash
# Canonical repo check. Versioned fragments under tests/inventory classify
# every root tests/test_*.sh and tests/test_*.py test. Every test runs
# concurrently unless its inventory row carries a serial reason, and each
# test remains subject to the per-test timeout.
#
# A reasoned quarantine still runs and reports its status but does not fail
# the suite. Repositories that copy this runner without its inventory use the
# legacy discovery contract so the runner's hermetic fixture tests remain
# valid.
#
# Tunable via environment:
#   CHECK_TEST_TIMEOUT   seconds allowed per test (default 600)
set -u

cd "$(dirname "$0")/.."

TEST_TIMEOUT="${CHECK_TEST_TIMEOUT:-600}"
SURFACE_BASELINE="specs/toolkit-core-simplification/BASELINE.json"
SURFACE_CHECKER="scripts/inventory-core-surface.py"
TOOLKIT_MARKER=".claude-plugin/plugin.json"

if [ -f "$TOOLKIT_MARKER" ]; then
  if [ ! -f "$SURFACE_BASELINE" ]; then
    echo "check.sh: surface baseline missing: $SURFACE_BASELINE" >&2
    exit 1
  fi
  if [ ! -f "$SURFACE_CHECKER" ]; then
    echo "check.sh: surface checker missing: $SURFACE_CHECKER" >&2
    exit 1
  fi
fi

if [ -f "$SURFACE_BASELINE" ]; then
  if [ ! -f "$SURFACE_CHECKER" ]; then
    echo "check.sh: surface checker missing: $SURFACE_CHECKER" >&2
    exit 1
  fi
  if ! python3 "$SURFACE_CHECKER" --check "$SURFACE_BASELINE"; then
    echo "check.sh: surface inventory invalid" >&2
    exit 1
  fi
fi

TIMEOUT_BIN=""
for candidate in timeout gtimeout; do
  if command -v "$candidate" >/dev/null 2>&1; then
    TIMEOUT_BIN="$candidate"
    break
  fi
done

workdir="$(mktemp -d)" || { echo "check.sh: cannot create work dir" >&2; exit 1; }
trap 'rm -rf "$workdir"' EXIT

slug() { printf '%s' "$1" | tr '/.' '_-'; }

run_one() {
  local label="$1"
  shift
  local key
  key="$(slug "$label")"
  if [ -n "$TIMEOUT_BIN" ]; then
    "$TIMEOUT_BIN" "$TEST_TIMEOUT" "$@" >"$workdir/$key.log" 2>&1
  else
    "$@" >"$workdir/$key.log" 2>&1
  fi
  printf '%s' "$?" >"$workdir/$key.rc"
}

inventory_files=(tests/inventory/*.json)
inventory_plan="$workdir/inventory.plan"
inventory_mode=0
if [ -e "${inventory_files[0]}" ]; then
  inventory_mode=1
  if ! python3 - "${inventory_files[@]}" >"$inventory_plan" <<'PY'
import json
import pathlib
import sys

fragments = {}
tests = {}
errors = []

for argument in sys.argv[1:]:
    path = pathlib.Path(argument)
    try:
        manifest = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path}: cannot read valid JSON: {exc}")
        continue
    if not isinstance(manifest, dict):
        errors.append(f"{path}: inventory fragment must be an object")
        continue
    if manifest.get("schema_version") != 1:
        errors.append(f"{path}: schema_version must be 1")
    fragment = manifest.get("fragment")
    if not isinstance(fragment, str) or not fragment.strip():
        errors.append(f"{path}: fragment must be a non-empty string")
    elif fragment != path.stem:
        errors.append(
            f"{path}: fragment {fragment!r} must match filename stem {path.stem!r}"
        )
    elif fragment in fragments:
        errors.append(
            f"duplicate test inventory fragment {fragment!r}: "
            f"{fragments[fragment]} and {path}"
        )
    else:
        fragments[fragment] = path
    unknown_manifest = sorted(
        set(manifest) - {"fragment", "schema_version", "tests"}
    )
    if unknown_manifest:
        errors.append(f"{path}: unknown fields: {', '.join(unknown_manifest)}")
    rows = manifest.get("tests")
    if not isinstance(rows, list):
        errors.append(f"{path}: tests must be an array")
        continue
    for position, row in enumerate(rows):
        prefix = f"{path}: tests[{position}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix} must be an object")
            continue
        allowed = {
            "disposition",
            "path",
            "reason",
            "runner",
            "serial",
            "serial_reason",
        }
        unknown = sorted(set(row) - allowed)
        if unknown:
            errors.append(f"{prefix} unknown fields: {', '.join(unknown)}")
        test_path = row.get("path")
        if not isinstance(test_path, str) or not test_path:
            errors.append(f"{prefix}.path must be a non-empty string")
            continue
        normalized = pathlib.PurePosixPath(test_path)
        if (
            normalized.is_absolute()
            or ".." in normalized.parts
            or normalized.as_posix() != test_path
            or normalized.parent.as_posix() != "tests"
            or not normalized.name.startswith("test_")
            or normalized.suffix not in {".py", ".sh"}
            or "|" in test_path
        ):
            errors.append(
                f"{prefix}.path must name a root tests/test_*.py or tests/test_*.sh"
            )
        if test_path in tests:
            errors.append(
                f"duplicate inventoried test {test_path!r}: "
                f"{tests[test_path][0]} and {path}"
            )
        runner = row.get("runner")
        if runner not in {"bash", "pytest"}:
            errors.append(f"{prefix}.runner must be bash or pytest")
        elif (
            runner == "bash"
            and normalized.suffix != ".sh"
            or runner == "pytest"
            and normalized.suffix != ".py"
        ):
            errors.append(f"{prefix}.runner does not match the test suffix")
        disposition = row.get("disposition")
        if disposition not in {"retain", "quarantine"}:
            errors.append(f"{prefix}.disposition must be retain or quarantine")
        reason = row.get("reason", "")
        if disposition == "quarantine" and (
            not isinstance(reason, str) or not reason.strip()
        ):
            errors.append(f"{prefix}: quarantine requires reason")
        if not isinstance(reason, str) or any(char in reason for char in "\n\r|"):
            errors.append(f"{prefix}.reason must be a single line without '|'")
        serial = row.get("serial")
        if not isinstance(serial, bool):
            errors.append(f"{prefix}.serial must be true or false")
        serial_reason = row.get("serial_reason", "")
        if serial and (
            not isinstance(serial_reason, str) or not serial_reason.strip()
        ):
            errors.append(f"{prefix}: serial test requires serial_reason")
        if serial_reason and (
            not isinstance(serial_reason, str)
            or any(char in serial_reason for char in "\n\r|")
        ):
            errors.append(
                f"{prefix}.serial_reason must be a single line without '|'"
            )
        tests[test_path] = (path, runner, disposition, serial, reason)

for test_path in sorted(tests):
    if not pathlib.Path(test_path).is_file():
        errors.append(f"inventoried test missing: {test_path}")

discovered = {
    path.as_posix()
    for path in pathlib.Path("tests").glob("test_*")
    if path.is_file() and path.suffix in {".py", ".sh"}
}
for test_path in sorted(discovered - tests.keys()):
    errors.append(f"unclassified test: {test_path}")

if errors:
    for error in errors:
        print(f"check.sh inventory: {error}", file=sys.stderr)
    raise SystemExit(1)

for test_path, (_, runner, disposition, serial, reason) in sorted(tests.items()):
    print(
        "|".join(
            (
                test_path,
                runner,
                disposition,
                "1" if serial else "0",
                reason,
            )
        )
    )
PY
  then
    echo "check.sh: test inventory invalid" >&2
    exit 1
  fi
elif [ -f ".claude-plugin/plugin.json" ] \
  || [ -f "specs/toolkit-core-simplification/BASELINE.json" ]; then
  echo "check.sh inventory: test inventory missing from tests/inventory/" >&2
  echo "check.sh: test inventory invalid" >&2
  exit 1
fi

test_paths=()
test_runners=()
quarantine_tests=()
quarantine_reasons=()
serial_config=()

if [ "$inventory_mode" -eq 1 ]; then
  while IFS='|' read -r test_path runner disposition serial reason; do
    [ -n "$test_path" ] || continue
    test_paths+=("$test_path")
    test_runners+=("$runner")
    if [ "$disposition" = "quarantine" ]; then
      quarantine_tests+=("$test_path")
      quarantine_reasons+=("$reason")
    fi
    if [ "$serial" = "1" ]; then
      serial_config+=("$test_path")
    fi
  done <"$inventory_plan"
else
  for test_path in tests/test_*.sh; do
    [ -e "$test_path" ] || continue
    test_paths+=("$test_path")
    test_runners+=("bash")
  done
  for test_path in tests/test_agentic_*.py; do
    [ -e "$test_path" ] || continue
    test_paths+=("$test_path")
    test_runners+=("pytest")
  done
  quarantine_tests+=("tests/test_eval_coverage_lint.sh")
  quarantine_reasons+=(
    "Owned by specs/eval-coverage-tiers; requires Bash 4 associative arrays."
  )
  serial_config+=("tests/test_agentic_latency.sh")
fi

is_quarantined() {
  local candidate="$1" test_path
  for test_path in "${quarantine_tests[@]:-}"; do
    [ "$test_path" = "$candidate" ] && return 0
  done
  return 1
}

is_serial() {
  local candidate="$1" test_path
  for test_path in "${serial_config[@]:-}"; do
    [ "$test_path" = "$candidate" ] && return 0
  done
  return 1
}

run_test() {
  local test_path="$1" runner="$2"
  if [ "$runner" = "bash" ]; then
    run_one "$test_path" bash "$test_path"
  else
    run_one "$test_path" python3 -m pytest "$test_path" -q
  fi
}

shell_tests=()
pytest_tests=()
serial_tests=()
serial_runners=()
index=0
while [ "$index" -lt "${#test_paths[@]}" ]; do
  test_path="${test_paths[$index]}"
  runner="${test_runners[$index]}"
  if [ "$runner" = "bash" ]; then
    shell_tests+=("$test_path")
  else
    pytest_tests+=("$test_path")
  fi
  if is_serial "$test_path"; then
    serial_tests+=("$test_path")
    serial_runners+=("$runner")
  else
    run_test "$test_path" "$runner" &
  fi
  index=$((index + 1))
done

wait

index=0
while [ "$index" -lt "${#serial_tests[@]}" ]; do
  run_test "${serial_tests[$index]}" "${serial_runners[$index]}"
  index=$((index + 1))
done

# --- collect, in stable inventory order -------------------------------------
fail=0

report() {
  local label="$1" key rc status
  key="$(slug "$label")"
  rc="$(cat "$workdir/$key.rc" 2>/dev/null)"
  case "$rc" in '' | *[!0-9]*) rc=1 ;; esac
  if [ "$rc" -eq 0 ]; then
    status="ok"
  elif [ "$rc" -eq 124 ]; then
    status="FAIL(timeout after ${TEST_TIMEOUT}s)"
  else
    status="FAIL"
  fi
  if is_quarantined "$label"; then
    echo "  [quarantined:${status}] $label"
    return
  fi
  echo "  [${status}] $label"
  if [ "$rc" -ne 0 ]; then
    sed 's/^/      /' "$workdir/$key.log" 2>/dev/null
    fail=1
  fi
}

echo "== shell tests =="
for test_path in "${shell_tests[@]:-}"; do
  [ -n "$test_path" ] || continue
  report "$test_path"
done

echo "== pytest tests =="
if [ "${#pytest_tests[@]}" -eq 0 ]; then
  echo "  (no inventoried pytest tests)"
else
  for test_path in "${pytest_tests[@]}"; do
    report "$test_path"
  done
fi

echo "== quarantined (known-red, do not fail the suite) =="
index=0
while [ "$index" -lt "${#quarantine_tests[@]}" ]; do
  echo "  - ${quarantine_tests[$index]} — ${quarantine_reasons[$index]}"
  index=$((index + 1))
done

if [ "$fail" -ne 0 ]; then
  echo "check.sh: FAIL"
  exit 1
fi
echo "check.sh: green"
