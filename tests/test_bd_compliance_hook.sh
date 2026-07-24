#!/usr/bin/env bash
# Tests for .claude/hooks/bd-compliance.sh (specs/beads-daily-skill/SPEC.md,
# "The compliance Stop hook"): a session that claimed a still-open bd issue is
# blocked at Stop, and stops being blocked once the issue is closed. Runs
# against a throwaway bd-tracked fixture repo in a temp dir.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HOOK="$TOOLKIT_DIR/.claude/hooks/bd-compliance.sh"

for dep in bd jq git; do
  if ! command -v "$dep" >/dev/null 2>&1; then
    echo "SKIP: $dep not on PATH; bd-compliance hook cannot be exercised"
    exit 0
  fi
done

pass=0
fail=0

assert() { # assert <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc" >&2
  fi
}

assert_eq() { # assert_eq <description> <expected> <actual>
  local desc="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc (expected: '$expected', got: '$actual')" >&2
  fi
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# run_hook <script> <stdin> <cwd> -- sets RH_EXIT / RH_ERR.
run_hook() {
  local script="$1" stdin="$2" cwd="$3"
  local err_f="$TMP/.rh_err"
  (
    cd "$cwd" || exit 97
    printf '%s' "$stdin" | "$script" >/dev/null 2>"$err_f"
  )
  RH_EXIT=$?
  RH_ERR="$(cat "$err_f")"
}

assert "bd-compliance.sh exists and is executable" test -x "$HOOK"

REPO="$TMP/fixture repo"
mkdir -p "$REPO"
git -C "$REPO" init -q
git -C "$REPO" config user.name test
git -C "$REPO" config user.email test@example.com

(cd "$REPO" && BD_NON_INTERACTIVE=1 bd init --prefix bdc) >/dev/null 2>&1
issue_id="$(cd "$REPO" && bd create "claimed fixture issue" --json 2>/dev/null \
  | jq -r '.id // .[0].id // empty')"
if [ -z "$issue_id" ]; then
  echo "FAIL: fixture setup could not create a bd issue" >&2
  exit 1
fi

printf '%s\n' "$issue_id" > "$REPO/.beads/session-claims"

stop_payload="$(jq -nc --arg cwd "$REPO" '{stop_hook_active: false, cwd: $cwd}')"

# --- claimed issue still open -> Stop is blocked ----------------------------

run_hook "$HOOK" "$stop_payload" "$REPO"
assert_eq "hook exits 2 while the claimed issue is open" 2 "$RH_EXIT"
assert "hook names the open issue id on stderr" \
  grep -qF "$issue_id" <<<"$RH_ERR"

# --- claimed issue closed -> blocking clears --------------------------------

(cd "$REPO" && bd close "$issue_id") >/dev/null 2>&1

run_hook "$HOOK" "$stop_payload" "$REPO"
assert_eq "hook exits 0 once the claimed issue is closed" 0 "$RH_EXIT"
assert "hook says nothing on stderr once the claim is satisfied" \
  test -z "$RH_ERR"

# --- Summary -----------------------------------------------------------------

echo "pass: $pass, fail: $fail"
[ "$fail" -eq 0 ]
