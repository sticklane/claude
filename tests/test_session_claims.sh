#!/usr/bin/env bash
# Tests for bin/session-claims. The contract is idempotent add/remove, safe
# single-id cleanup, and stable behavior when IDs are absent.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CMD="$TOOLKIT_DIR/bin/session-claims"

pass=0
fail=0

run_cmd() { # run_cmd <operation> <id>
  RC_OUT="$("$CMD" "$1" "$2" 2>&1)"
  RC_EXIT=$?
}

assert_rc() { # assert_rc <desc> <expected> <actual>
  local desc="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc (expected '$expected', got '$actual')" >&2
  fi
}

assert() { # assert <desc> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc" >&2
  fi
}

assert_not() { # assert_not <desc> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    fail=$((fail + 1))
    echo "FAIL: $desc" >&2
  else
    pass=$((pass + 1))
  fi
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
SESSION_FILE="$TMP/.beads/session-claims"

with_file() {
  SESSION_CLAIMS_FILE="$SESSION_FILE"
  export SESSION_CLAIMS_FILE
}

# ---------------------------------------------------------------------------
# ADD/REMOVE — single-line cleanup must not no-op when removing the only id.
# ---------------------------------------------------------------------------
with_file
mkdir -p "$TMP/.beads"
printf 'single-id\n' > "$SESSION_FILE"

run_cmd rm single-id
assert_rc "single-id removal runs successfully" 0 "$RC_EXIT"
assert "single-id removal leaves an empty file" \
  [ -f "$SESSION_FILE" ] && [ ! -s "$SESSION_FILE" ]

# ---------------------------------------------------------------------------
# REMOVE — multi-id list keeps the order and only removes matching ids.
# ---------------------------------------------------------------------------
printf 'alpha\nbeta\ngamma\n' > "$SESSION_FILE"
run_cmd rm beta
assert_rc "middle-id removal runs successfully" 0 "$RC_EXIT"
assert "multi-id removal drops only the requested id" \
  diff -u "$SESSION_FILE" <(printf 'alpha\ngamma\n')

# ---------------------------------------------------------------------------
# ADD — duplicate adds are deduplicated and idempotent.
# ---------------------------------------------------------------------------
printf '' > "$SESSION_FILE"
run_cmd add repeat-id
run_cmd add repeat-id
assert_rc "duplicate add runs successfully" 0 "$RC_EXIT"
assert "duplicate add writes only one line for the id" \
  [ "$(grep -cx "^repeat-id$" "$SESSION_FILE")" -eq 1 ]

# ---------------------------------------------------------------------------
# REMOVE — unknown id leaves file unchanged.
# ---------------------------------------------------------------------------
printf 'keep-a\nkeep-b\n' > "$SESSION_FILE"
run_cmd rm missing-id
assert_rc "absent-id removal runs successfully" 0 "$RC_EXIT"
assert "absent-id removal keeps existing lines" \
  diff -u "$SESSION_FILE" <(printf 'keep-a\nkeep-b\n')

# ---------------------------------------------------------------------------
# CONTAINS — exact membership checks are reliable for present/absent IDs.
# ---------------------------------------------------------------------------
run_cmd add present
run_cmd contains present
assert_rc "contains succeeds for a present id" 0 "$RC_EXIT"
run_cmd contains missing
assert_rc "contains fails for a missing id" 1 "$RC_EXIT"

# ---------------------------------------------------------------------------
# ATOMIC BEHAVIOR — removal always rewrites via temp file, not a no-op edge case.
# ---------------------------------------------------------------------------
printf 'only-entry\n' > "$SESSION_FILE"
run_cmd rm only-entry
assert "atomic remove keeps the marker file present" \
  [ -f "$SESSION_FILE" ]
assert "atomic remove on final line leaves an empty file" \
  [ ! -s "$SESSION_FILE" ]

echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ] || exit 1
exit 0
