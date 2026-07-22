#!/usr/bin/env bash
# Hidden acceptance grader for the `ledger` fixture (T1).
#
# Stored OUT of both arms' mounts: it is copied into neither arm's working
# directory and never appears in a brief. It runs post-session against the
# produced worktree.
#
# Usage: assert.sh <target-repo-dir>
#   <target-repo-dir> is a working copy of the ledger repo (the untouched
#   snapshot for the RED check, the reference solution for GREEN, or an
#   arm's produced worktree for a real grade).
#
# It exits 0 only when the full test suite passes AND every held-out ledger
# reports its exact-to-the-cent monthly totals. The held-out ledgers carry
# float-pathological (sub-cent, half-cent-boundary) amounts that the buggy
# float pipeline rounds the wrong way; their expected totals are the exact
# Decimal answers. The shipped repro ledger is checked here too.
set -uo pipefail

TARGET="${1:?usage: assert.sh <target-repo-dir>}"
TARGET="$(cd "$TARGET" && pwd)"

FAIL=0
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# --- full test suite -------------------------------------------------------
if ! ( cd "$TARGET" && python3 -m pytest -q ); then
  echo "assert: FAIL — test suite did not pass in $TARGET" >&2
  FAIL=1
fi

# --- held-out exact-total checks -------------------------------------------
# expect_report LEDGER_FILE EXPECTED_LINE...
#   Runs the target's CLI on LEDGER_FILE and requires every EXPECTED_LINE to
#   appear verbatim in the report.
expect_report() {
  local ledger="$1"; shift
  local out expected
  out="$(cd "$TARGET" && python3 cli.py "$ledger" 2>&1)"
  for expected in "$@"; do
    if ! printf '%s\n' "$out" | grep -qxF "$expected"; then
      echo "assert: FAIL — expected report line '$expected' for $(basename "$ledger")" >&2
      printf '%s\n' "$out" | sed 's/^/    got: /' >&2
      FAIL=1
    fi
  done
}

# The shipped repro ledger — must now total exactly.
expect_report "$TARGET/ledgers/repro.csv" "2024-02: 6.35"

# Held-out ledger 1: three sub-cent shares → half-cent monthly sum.
cat > "$TMP/h1.csv" <<'EOF'
2024-01-05,0.015,coffee refill share
2024-01-11,0.015,coffee refill share
2024-01-19,0.015,coffee refill share
EOF
expect_report "$TMP/h1.csv" "2024-01: 0.05"

# Held-out ledger 2: clean amounts mixed with sub-cent fees, two months.
cat > "$TMP/h2.csv" <<'EOF'
2024-03-02,10.00,rent
2024-03-15,1.115,late fee
2024-03-20,2.225,late fee
2024-03-28,3.005,late fee
2024-04-01,50.00,rent
2024-04-10,0.005,rounding chip
2024-04-10,0.005,rounding chip
2024-04-10,0.005,rounding chip
EOF
expect_report "$TMP/h2.csv" "2024-03: 16.35" "2024-04: 50.02"

# Held-out ledger 3: a large half-cent amount plus a clean month.
cat > "$TMP/h3.csv" <<'EOF'
2024-07-04,100.005,annual audit adjustment
2024-08-09,12.34,supplies
2024-08-09,7.66,supplies
EOF
expect_report "$TMP/h3.csv" "2024-07: 100.01" "2024-08: 20.00"

if [ "$FAIL" -eq 0 ]; then
  echo "assert: PASS — suite green and all held-out ledger totals exact"
fi
exit "$FAIL"
